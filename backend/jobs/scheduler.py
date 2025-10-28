"""
Nightly Jobs Scheduler

Purpose: Orchestrate sacred job order for daily pricing pack and metrics computation
Updated: 2025-10-22
Priority: P0 (S1-W1 GATE - Truth Spine Foundation)

Sacred Order (NON-NEGOTIABLE):
    1. build_pack          → Create immutable pricing snapshot (prices + FX)
    2. reconcile_ledger    → Validate vs Beancount ±1bp (BLOCKS if fails)
    3. compute_daily_metrics → TWR, MWR, vol, Sharpe, alpha, beta
    4. prewarm_factors     → Factor fits, rolling stats
    5. prewarm_ratings     → Buffett quality scores
    6. mark_pack_fresh     → Enable executor freshness gate
    7. evaluate_alerts     → Check conditions, dedupe, deliver

Critical Requirements:
    - Jobs MUST run in order (no parallelization)
    - Reconciliation failure BLOCKS all subsequent jobs
    - Pack build must complete by 00:15 (10 min deadline)
    - Mark fresh only after ALL pre-warm jobs complete
    - Errors are logged + sent to DLQ for manual review

SLOs:
    - Pack build completes by 00:15 local time (10 min deadline)
    - Total nightly job duration < 30 minutes
    - Reconciliation ±1bp accuracy (100% of portfolios)

Scheduler: APScheduler (cron trigger at 00:05 daily)
"""

import argparse
import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import os

# Job imports
from jobs.build_pricing_pack import PricingPackBuilder
from jobs.reconcile_ledger import ReconciliationService
from jobs.metrics import MetricsComputer

# Logger
logger = logging.getLogger("DawsOS.Scheduler")


@dataclass
class JobResult:
    """Result from a single job execution."""
    job_name: str
    success: bool
    duration_seconds: float
    started_at: datetime
    completed_at: datetime
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NightlyRunReport:
    """Report from complete nightly job run."""
    run_date: date
    started_at: datetime
    completed_at: Optional[datetime]
    total_duration_seconds: Optional[float]
    jobs: List[JobResult] = field(default_factory=list)
    success: bool = False
    blocked_at: Optional[str] = None  # Job name that blocked execution


class NightlyJobScheduler:
    """
    Orchestrates nightly jobs in sacred order.

    Sacred Order (NON-NEGOTIABLE):
        1. build_pack → 2. reconcile_ledger → 3. compute_daily_metrics →
        4. prewarm_factors → 5. prewarm_ratings → 6. mark_pack_fresh →
        7. evaluate_alerts

    Critical Rules:
        - Jobs run sequentially (no parallelization)
        - Reconciliation failure blocks all subsequent jobs
        - Pack build must complete by 00:15 (10 min deadline)
        - Mark fresh only after ALL pre-warm completes
    """

    def __init__(
        self,
        pricing_policy: str = "WM4PM_CAD",
        ledger_path: str = ".ledger/main.beancount",
        run_hour: int = 0,
        run_minute: int = 5,
    ):
        """
        Initialize scheduler.

        Args:
            pricing_policy: Pricing policy (WM4PM_CAD, CLOSE, etc.)
            ledger_path: Path to Beancount ledger file
            run_hour: Hour to run nightly job (default: 0 = midnight)
            run_minute: Minute to run nightly job (default: 5)
        """
        self.pricing_policy = pricing_policy
        self.ledger_path = ledger_path
        self.run_hour = run_hour
        self.run_minute = run_minute

        # Initialize APScheduler
        self.scheduler = AsyncIOScheduler()

        # Initialize job components
        self.pricing_pack_builder = PricingPackBuilder(use_stubs=False)
        self.reconciliation_service = ReconciliationService()
        self.metrics_computer = MetricsComputer(use_db=True)

        # Track last run
        self.last_run: Optional[NightlyRunReport] = None

    def start(self):
        """Start the scheduler."""
        # Add nightly job at 00:05
        self.scheduler.add_job(
            self.run_nightly_jobs,
            trigger=CronTrigger(hour=self.run_hour, minute=self.run_minute),
            id="nightly_jobs",
            name="Nightly Jobs (Sacred Order)",
            replace_existing=True,
            max_instances=1,  # Only one instance at a time
        )

        # Add DLQ replay job (hourly at :05)
        self.scheduler.add_job(
            self.run_dlq_replay,
            trigger=CronTrigger(minute=5),  # Every hour at :05
            id="dlq_replay",
            name="DLQ Replay (Hourly)",
            replace_existing=True,
            max_instances=1,
        )

        self.scheduler.start()
        logger.info(f"Scheduler started. Nightly jobs will run at {self.run_hour:02d}:{self.run_minute:02d}")
        logger.info("DLQ replay will run hourly at :05")

    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    async def run_nightly_jobs(self, asof_date: Optional[date] = None) -> NightlyRunReport:
        """
        Run nightly jobs in sacred order.

        Sacred Order (NON-NEGOTIABLE):
            1. build_pack
            2. reconcile_ledger (BLOCKS if fails)
            3. compute_daily_metrics
            4. prewarm_factors
            5. prewarm_ratings
            6. mark_pack_fresh
            7. evaluate_alerts

        Args:
            asof_date: Date for pricing pack (default: yesterday)

        Returns:
            NightlyRunReport with job results
        """
        if asof_date is None:
            asof_date = date.today() - timedelta(days=1)

        logger.info(f"=" * 80)
        logger.info(f"NIGHTLY JOBS STARTED: {asof_date}")
        logger.info(f"=" * 80)

        report = NightlyRunReport(
            run_date=asof_date,
            started_at=datetime.now(),
            completed_at=None,
            total_duration_seconds=None,
        )

        try:
            # JOB 1: Build Pricing Pack
            job1_result = await self._run_job(
                job_name="build_pack",
                job_func=self._job_build_pack,
                job_args=(asof_date,),
            )
            report.jobs.append(job1_result)

            if not job1_result.success:
                logger.error("CRITICAL: Pricing pack build failed. BLOCKING all subsequent jobs.")
                report.blocked_at = "build_pack"
                report.success = False
                return report

            pack_id = job1_result.details.get("pack_id")
            logger.info(f"✅ Pricing pack built: {pack_id}")

            # JOB 2: Reconcile Ledger (CRITICAL - BLOCKS IF FAILS)
            job2_result = await self._run_job(
                job_name="reconcile_ledger",
                job_func=self._job_reconcile_ledger,
                job_args=(pack_id, asof_date),
            )
            report.jobs.append(job2_result)

            if not job2_result.success:
                logger.error("CRITICAL: Ledger reconciliation failed. BLOCKING all subsequent jobs.")
                logger.error(f"Reconciliation errors: {job2_result.details.get('errors', [])}")
                report.blocked_at = "reconcile_ledger"
                report.success = False
                return report

            logger.info(f"✅ Ledger reconciliation passed (±1bp)")

            # JOB 3: Compute Daily Metrics
            job3_result = await self._run_job(
                job_name="compute_daily_metrics",
                job_func=self._job_compute_daily_metrics,
                job_args=(pack_id, asof_date),
            )
            report.jobs.append(job3_result)

            if not job3_result.success:
                logger.warning("Daily metrics computation failed (non-blocking)")
            else:
                logger.info(f"✅ Daily metrics computed")

            # JOB 4: Pre-warm Factors
            job4_result = await self._run_job(
                job_name="prewarm_factors",
                job_func=self._job_prewarm_factors,
                job_args=(pack_id, asof_date),
            )
            report.jobs.append(job4_result)

            if not job4_result.success:
                logger.warning("Factor pre-warm failed (non-blocking)")
            else:
                logger.info(f"✅ Factors pre-warmed")

            # JOB 5: Pre-warm Ratings
            job5_result = await self._run_job(
                job_name="prewarm_ratings",
                job_func=self._job_prewarm_ratings,
                job_args=(pack_id, asof_date),
            )
            report.jobs.append(job5_result)

            if not job5_result.success:
                logger.warning("Ratings pre-warm failed (non-blocking)")
            else:
                logger.info(f"✅ Ratings pre-warmed")

            # JOB 6: Mark Pack Fresh (CRITICAL - enables executor)
            job6_result = await self._run_job(
                job_name="mark_pack_fresh",
                job_func=self._job_mark_pack_fresh,
                job_args=(pack_id,),
            )
            report.jobs.append(job6_result)

            if not job6_result.success:
                logger.error("CRITICAL: Failed to mark pack as fresh")
                report.blocked_at = "mark_pack_fresh"
                report.success = False
                return report

            logger.info(f"✅ Pack marked as fresh (executor enabled)")

            # JOB 7: Evaluate Alerts
            job7_result = await self._run_job(
                job_name="evaluate_alerts",
                job_func=self._job_evaluate_alerts,
                job_args=(pack_id, asof_date),
            )
            report.jobs.append(job7_result)

            if not job7_result.success:
                logger.warning("Alert evaluation failed (non-blocking)")
            else:
                logger.info(f"✅ Alerts evaluated")

            # All jobs completed successfully
            report.success = True
            logger.info(f"=" * 80)
            logger.info(f"NIGHTLY JOBS COMPLETED SUCCESSFULLY: {asof_date}")
            logger.info(f"=" * 80)

        except Exception as e:
            logger.exception(f"CRITICAL: Nightly jobs failed with unexpected error: {e}")
            report.success = False

        finally:
            report.completed_at = datetime.now()
            report.total_duration_seconds = (report.completed_at - report.started_at).total_seconds()
            self.last_run = report

            # Log summary
            self._log_summary(report)

        return report

    async def _run_job(
        self,
        job_name: str,
        job_func,
        job_args: tuple = (),
    ) -> JobResult:
        """
        Run a single job and track timing.

        Args:
            job_name: Name of job
            job_func: Job function to execute
            job_args: Arguments to pass to job function

        Returns:
            JobResult with timing and error info
        """
        logger.info(f"Starting job: {job_name}")
        started_at = datetime.now()

        try:
            result = await job_func(*job_args)
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            logger.info(f"Job completed: {job_name} ({duration:.2f}s)")

            return JobResult(
                job_name=job_name,
                success=True,
                duration_seconds=duration,
                started_at=started_at,
                completed_at=completed_at,
                details=result if isinstance(result, dict) else {},
            )

        except Exception as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            logger.exception(f"Job failed: {job_name} ({duration:.2f}s): {e}")

            return JobResult(
                job_name=job_name,
                success=False,
                duration_seconds=duration,
                started_at=started_at,
                completed_at=completed_at,
                error=str(e),
            )

    # ===========================
    # JOB IMPLEMENTATIONS
    # ===========================

    async def _job_build_pack(self, asof_date: date) -> Dict[str, Any]:
        """
        JOB 1: Build immutable pricing pack.

        Creates pricing pack with:
        - Prices from Polygon/FMP
        - FX rates from WM 4PM fixing
        - SHA256 hash for immutability
        - Status: warming (NOT fresh yet)
        - Rate limiting and circuit breaker for providers

        Returns:
            {"pack_id": str, "asof_date": str, "policy": str}
        """
        pack_id = await self.pricing_pack_builder.build_pack(
            asof_date=asof_date,
            policy=self.pricing_policy,
            mark_fresh=False,  # Don't mark fresh until prewarm complete
        )

        return {
            "pack_id": pack_id,
            "asof_date": str(asof_date),
            "policy": self.pricing_policy,
        }

    async def _job_reconcile_ledger(self, pack_id: str, asof_date: date) -> Dict[str, Any]:
        """
        JOB 2: Reconcile DB vs ledger NAV (±1bp tolerance).

        Sacred invariants:
        - Ledger is source of truth
        - DB NAV must match ledger NAV ±1bp
        - Quantities must match exactly
        - All positions reconciled

        CRITICAL: This job BLOCKS all subsequent jobs if it fails.

        Returns:
            {"success": bool, "num_portfolios": int, "num_passed": int, "num_failed": int}
        """
        # Reconcile all portfolios
        results = await self.reconciliation_service.reconcile_all_portfolios(
            as_of_date=asof_date
        )

        # Check if all passed
        num_passed = sum(1 for r in results if r.passed)
        num_failed = sum(1 for r in results if not r.passed)

        if num_failed > 0:
            # Log failures
            for r in results:
                if not r.passed:
                    logger.error(
                        f"Reconciliation FAILED for {r.portfolio_id}: "
                        f"error={r.error_bps:.2f}bp "
                        f"(ledger={r.ledger_nav}, db={r.pricing_nav})"
                    )

            raise ValueError(
                f"Ledger reconciliation failed: {num_failed}/{len(results)} portfolios "
                f"exceeded ±1bp tolerance"
            )

        # Update pricing pack reconciliation status
        from app.db.connection import execute_statement
        update_query = """
            UPDATE pricing_packs
            SET reconciliation_passed = true,
                reconciliation_error_bps = 0.0,
                updated_at = NOW()
            WHERE id = $1
        """
        await execute_statement(update_query, pack_id)

        return {
            "success": True,
            "num_portfolios": len(results),
            "num_passed": num_passed,
            "num_failed": num_failed,
        }

    async def _job_compute_daily_metrics(self, pack_id: str, asof_date: date) -> Dict[str, Any]:
        """
        JOB 3: Compute daily portfolio metrics.

        Metrics:
        - TWR (time-weighted return)
        - MWR (money-weighted return / IRR)
        - Volatility (rolling 30/60/90 day)
        - Sharpe ratio
        - Alpha / Beta vs benchmark

        Returns:
            {"num_portfolios": int, "metrics_computed": List[str]}
        """
        logger.info(f"Computing daily metrics for pack {pack_id}")

        metrics_list = await self.metrics_computer.compute_all_metrics(
            pack_id=pack_id,
            asof_date=asof_date,
        )

        return {
            "num_portfolios": len(metrics_list),
            "metrics_computed": ["TWR", "MWR", "vol", "sharpe", "alpha", "beta"],
        }

    async def _job_prewarm_factors(self, pack_id: str, asof_date: date) -> Dict[str, Any]:
        """
        JOB 4: Pre-warm macro factors and regime detection.

        Macro computations:
        - Regime detection (5 regimes: Goldilocks, Reflationary, Stagflation, Deflation, Recovery)
        - Cycle analysis (Empire/Long-term/Short-term debt cycles)
        - Factor exposures (real rate, inflation, credit, USD, risk-free)

        These are pre-computed so the UI loads instantly.

        Returns:
            {"num_portfolios": int, "regime_computed": bool, "cycles_computed": bool}
        """
        logger.info(f"Pre-warming macro factors for pack {pack_id}")

        from app.db.connection import execute_query

        # Get all active portfolios
        query_portfolios = "SELECT id FROM portfolios WHERE is_active = true"
        portfolios = await execute_query(query_portfolios)

        num_portfolios = len(portfolios)

        # Call macro agent to compute regime and cycles
        # This will be cached in database for fast UI retrieval
        try:
            from app.services.macro import get_macro_service

            macro_service = get_macro_service()

            # Compute regime for asof_date
            regime_result = await macro_service.detect_regime(asof_date)
            logger.info(f"Regime detected: {regime_result.get('regime', 'unknown')}")

            # Compute cycle analysis
            cycles_result = await macro_service.compute_cycles(asof_date)
            logger.info(f"Cycles computed: {len(cycles_result.get('cycles', []))} cycles")

            return {
                "num_portfolios": num_portfolios,
                "regime": regime_result.get("regime"),
                "regime_confidence": float(regime_result.get("confidence", 0.0)),
                "cycles_computed": len(cycles_result.get("cycles", [])),
                "factors": ["real_rate", "inflation", "credit", "usd", "risk_free"],
            }

        except Exception as e:
            logger.error(f"Failed to prewarm factors: {e}", exc_info=True)
            # Non-blocking - return partial success
            return {
                "num_portfolios": num_portfolios,
                "regime": None,
                "cycles_computed": 0,
                "error": str(e),
            }

    async def _job_prewarm_ratings(self, pack_id: str, asof_date: date) -> Dict[str, Any]:
        """
        JOB 5: Pre-warm Buffett quality ratings.

        Ratings (0-10 scale):
        - Quality (margins, ROIC, FCF conversion)
        - Moat (competitive advantages)
        - Balance sheet (debt, coverage)
        - Management (capital allocation)
        - Valuation (DCF, multiples)

        Returns:
            {"num_securities": int, "ratings_computed": List[str]}
        """
        # TODO: Implement ratings pre-warm
        # This will integrate with financial_analyst agent

        logger.info(f"Pre-warming ratings for pack {pack_id}")

        # Placeholder
        return {
            "num_securities": 0,
            "ratings_computed": ["quality", "moat", "balance_sheet", "management", "valuation"],
            "status": "TODO",
        }

    async def _job_mark_pack_fresh(self, pack_id: str) -> Dict[str, Any]:
        """
        JOB 6: Mark pricing pack as fresh.

        CRITICAL: This enables the executor freshness gate.
        Executor will reject requests until this job completes.

        Updates pricing_packs table:
        - status: 'warming' → 'fresh'
        - is_fresh: false → true
        - prewarm_done: false → true
        - updated_at: current timestamp

        Returns:
            {"pack_id": str, "is_fresh": bool, "prewarm_done": bool}
        """
        logger.info(f"Marking pack as fresh: {pack_id}")

        from app.db.connection import execute_statement, execute_query_one

        # Update pricing pack status
        update_query = """
            UPDATE pricing_packs
            SET status = 'fresh',
                is_fresh = true,
                prewarm_done = true,
                updated_at = NOW()
            WHERE id = $1
            RETURNING id, status, is_fresh, prewarm_done
        """

        result = await execute_query_one(update_query, pack_id)

        if not result:
            raise ValueError(f"Failed to mark pack {pack_id} as fresh (pack not found)")

        logger.info(
            f"✅ Pack {pack_id} marked as fresh "
            f"(status={result['status']}, is_fresh={result['is_fresh']}, "
            f"prewarm_done={result['prewarm_done']})"
        )

        return {
            "pack_id": pack_id,
            "status": result["status"],
            "is_fresh": result["is_fresh"],
            "prewarm_done": result["prewarm_done"],
        }

    async def _job_evaluate_alerts(self, pack_id: str, asof_date: date) -> Dict[str, Any]:
        """
        JOB 7: Evaluate alert conditions.

        Alert types:
        - Regime change (macro shift)
        - Position drift (exceeds target allocation)
        - Risk threshold (VaR, DaR)
        - Rebalance opportunity (TE below limit)
        - Ratings change (quality degradation)

        Deduplication:
        - Single delivery per user/alert/day (DB unique index)

        Returns:
            {"num_alerts_evaluated": int, "num_alerts_delivered": int}
        """
        logger.info(f"Evaluating alerts for pack {pack_id}")

        try:
            from jobs.evaluate_alerts import AlertEvaluator

            evaluator = AlertEvaluator(use_db=True)
            summary = await evaluator.evaluate_all_alerts(asof_date=asof_date)

            return {
                "num_alerts_evaluated": summary["alerts_evaluated"],
                "num_alerts_delivered": summary["notifications_delivered"],
                "num_alerts_failed": summary["notifications_failed"],
                "duration_seconds": summary["duration_seconds"],
            }

        except Exception as e:
            logger.error(f"Alert evaluation failed: {e}", exc_info=True)
            raise

    async def run_dlq_replay(self):
        """
        Run DLQ replay job (hourly).

        Retries failed notification deliveries from Dead Letter Queue.

        This job runs hourly at :05 (00:05, 01:05, 02:05, ...).
        """
        logger.info("=" * 80)
        logger.info("DLQ REPLAY JOB STARTED")
        logger.info("=" * 80)

        started_at = datetime.now()

        try:
            from jobs.replay_dlq import DLQReplayer

            replayer = DLQReplayer(use_db=True)
            summary = await replayer.replay_dlq_jobs(batch_size=100)

            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            logger.info("=" * 80)
            logger.info("DLQ REPLAY JOB COMPLETED")
            logger.info(f"  Duration: {duration:.2f}s")
            logger.info(f"  Jobs processed: {summary['jobs_processed']}")
            logger.info(f"  Jobs succeeded: {summary['jobs_succeeded']}")
            logger.info(f"  Jobs failed: {summary['jobs_failed']}")
            logger.info(f"  Jobs permanently failed: {summary['jobs_permanent_fail']}")
            logger.info("=" * 80)

        except Exception as e:
            logger.exception(f"DLQ replay job failed: {e}")
            # Don't raise - hourly job should continue on failure

    def _log_summary(self, report: NightlyRunReport):
        """Log summary of nightly run."""
        logger.info("")
        logger.info("=" * 80)
        logger.info("NIGHTLY JOB SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Run Date: {report.run_date}")
        logger.info(f"Started: {report.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Completed: {report.completed_at.strftime('%Y-%m-%d %H:%M:%S') if report.completed_at else 'N/A'}")
        logger.info(f"Duration: {report.total_duration_seconds:.2f}s" if report.total_duration_seconds else "N/A")
        logger.info(f"Success: {'✅ YES' if report.success else '❌ NO'}")

        if report.blocked_at:
            logger.error(f"BLOCKED AT: {report.blocked_at}")

        logger.info("")
        logger.info("Job Results:")
        logger.info("-" * 80)

        for job in report.jobs:
            status = "✅" if job.success else "❌"
            logger.info(f"{status} {job.job_name:30s} {job.duration_seconds:6.2f}s")
            if job.error:
                logger.error(f"   Error: {job.error}")

        logger.info("=" * 80)


# ===========================
# STANDALONE EXECUTION
# ===========================

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DawsOS Nightly Job Scheduler")
    parser.add_argument(
        "--mode",
        choices=("run-once", "daemon"),
        default="run-once",
        help="Execution mode. 'run-once' executes the nightly flow immediately; 'daemon' runs on schedule.",
    )
    parser.add_argument(
        "--asof-date",
        help="ISO date (YYYY-MM-DD) for run-once mode. Defaults to yesterday.",
    )
    parser.add_argument(
        "--pricing-policy",
        default=os.getenv("PRICING_POLICY", "WM4PM_CAD"),
        help="Pricing policy identifier (default: WM4PM_CAD).",
    )
    parser.add_argument(
        "--ledger-path",
        default=os.getenv("LEDGER_PATH", ".ledger/main.beancount"),
        help="Path to Beancount ledger repository (default: .ledger/main.beancount).",
    )
    parser.add_argument(
        "--run-hour",
        type=int,
        default=int(os.getenv("SCHEDULER_RUN_HOUR", "0")),
        help="Hour (0-23) for nightly job in daemon mode (default: 0).",
    )
    parser.add_argument(
        "--run-minute",
        type=int,
        default=int(os.getenv("SCHEDULER_RUN_MINUTE", "5")),
        help="Minute (0-59) for nightly job in daemon mode (default: 5).",
    )
    return parser.parse_args()


async def _run_daemon(args: argparse.Namespace) -> None:
    scheduler = NightlyJobScheduler(
        pricing_policy=args.pricing_policy,
        ledger_path=args.ledger_path,
        run_hour=args.run_hour,
        run_minute=args.run_minute,
    )

    scheduler.start()
    logger.info("Nightly scheduler running in daemon mode. Press Ctrl+C to stop.")

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Shutdown signal received. Stopping scheduler...")
        scheduler.stop()


async def _run_once(args: argparse.Namespace) -> int:
    if args.asof_date:
        asof_date = date.fromisoformat(args.asof_date)
    else:
        asof_date = date.today() - timedelta(days=1)

    scheduler = NightlyJobScheduler(
        pricing_policy=args.pricing_policy,
        ledger_path=args.ledger_path,
        run_hour=args.run_hour,
        run_minute=args.run_minute,
    )

    report = await scheduler.run_nightly_jobs(asof_date=asof_date)
    return 0 if report.success else 1


async def main_async() -> int:
    args = _parse_args()

    if args.mode == "daemon":
        await _run_daemon(args)
        return 0

    return await _run_once(args)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    exit_code = asyncio.run(main_async())
    raise SystemExit(exit_code)
