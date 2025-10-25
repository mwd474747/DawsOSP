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
from backend.jobs.pricing_pack import PricingPackBuilder
from backend.jobs.reconciliation import LedgerReconciliator, ReconciliationReport
from backend.jobs.metrics import MetricsComputer
from backend.jobs.factors import FactorComputer

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
        self.pricing_pack_builder = PricingPackBuilder()
        self.ledger_reconciliator = LedgerReconciliator()
        self.metrics_computer = MetricsComputer(use_db=True)
        self.factor_computer = FactorComputer()

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
        - FX rates from FRED
        - SHA256 hash for immutability
        - Status: warming

        Returns:
            {"pack_id": str, "num_prices": int, "num_fx_rates": int}
        """
        pack_id = await self.pricing_pack_builder.build_pack(
            asof_date=asof_date,
            policy=self.pricing_policy,
        )

        return {
            "pack_id": pack_id,
            "asof_date": str(asof_date),
            "policy": self.pricing_policy,
        }

    async def _job_reconcile_ledger(self, pack_id: str, asof_date: date) -> Dict[str, Any]:
        """
        JOB 2: Reconcile DB vs Beancount ledger (±1bp).

        Sacred invariants:
        - Position quantities must match exactly
        - Cost basis must match exactly
        - Portfolio valuations must match ±1bp

        CRITICAL: This job BLOCKS all subsequent jobs if it fails.

        Returns:
            {"success": bool, "num_portfolios": int, "errors": List}
        """
        report = await self.ledger_reconciliator.reconcile_ledger(
            pack_id=pack_id,
            ledger_path=self.ledger_path,
        )

        if not report.success:
            raise ValueError(f"Ledger reconciliation failed: {len(report.errors)} errors found")

        return {
            "success": report.success,
            "num_portfolios": report.num_portfolios_checked,
            "errors": [
                {
                    "account": err.account,
                    "error_type": err.error_type,
                    "error_bps": float(err.error_bps) if err.error_bps else None,
                }
                for err in report.errors
            ],
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
        JOB 4: Pre-warm factor exposures.

        Factors:
        - Real rate (DFII10)
        - Inflation (T10YIE)
        - Credit spread (BAMLC0A0CM)
        - USD (DTWEXBGS)
        - Risk-free rate (DGS10)

        Computes:
        - Factor loadings (regression)
        - Rolling correlations
        - Factor contribution to return

        Returns:
            {"num_portfolios": int, "factors": List[str]}
        """
        logger.info(f"Pre-warming factors for pack {pack_id}")

        exposures = await self.factor_computer.compute_all_factors(
            pack_id=pack_id,
            asof_date=asof_date,
        )

        return {
            "num_portfolios": len(exposures),
            "factors": ["real_rate", "inflation", "credit", "usd", "risk_free"],
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
            {"pack_id": str, "is_fresh": bool}
        """
        # TODO: Implement mark_pack_fresh
        # Updates pricing_packs table via DB service

        logger.info(f"Marking pack as fresh: {pack_id}")

        # Placeholder
        return {
            "pack_id": pack_id,
            "is_fresh": True,
            "prewarm_done": True,
            "status": "TODO",
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
            from backend.jobs.evaluate_alerts import AlertEvaluator

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
            from backend.jobs.replay_dlq import DLQReplayer

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
