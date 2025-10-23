"""
Beancount Ledger Integration Service

Purpose: Parse Beancount ledger, extract transactions, store in database
Updated: 2025-10-22
Priority: P0 (Critical for Sprint 1 - Truth Spine)

Features:
    - Parse Beancount ledger from git repository
    - Extract portfolio transactions
    - Store transactions with commit hash provenance
    - Support for multi-currency transactions
    - Handle corporate actions (splits, dividends)

Architecture:
    Ledger Repo (Git) → Parser → Database → Reconciliation Job

Dependencies:
    pip install beancount

Usage:
    from backend.app.services.ledger import LedgerService

    service = LedgerService(ledger_path="/app/ledger")
    transactions = await service.parse_and_store()
"""

import logging
import os
import subprocess
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

try:
    from beancount import loader
    from beancount.core import data, amount, position
    BEANCOUNT_AVAILABLE = True
except ImportError:
    BEANCOUNT_AVAILABLE = False
    logging.warning("Beancount not installed. Ledger integration disabled.")

from backend.app.db.connection import get_db_pool, execute_statement, execute_query

logger = logging.getLogger("DawsOS.LedgerService")


# ============================================================================
# Data Models
# ============================================================================


class LedgerTransaction:
    """Ledger transaction from Beancount."""

    def __init__(
        self,
        date: date,
        account: str,
        amount: Decimal,
        currency: str,
        narration: str,
        metadata: Dict[str, Any] = None,
    ):
        self.date = date
        self.account = account
        self.amount = amount
        self.currency = currency
        self.narration = narration
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "account": self.account,
            "amount": float(self.amount),
            "currency": self.currency,
            "narration": self.narration,
            "metadata": self.metadata,
        }


# ============================================================================
# Ledger Service
# ============================================================================


class LedgerService:
    """
    Beancount ledger integration service.

    Parses Beancount ledger from git repository and stores transactions
    in the database with commit hash provenance.
    """

    def __init__(self, ledger_path: str = None):
        """
        Initialize ledger service.

        Args:
            ledger_path: Path to Beancount ledger git repository
                        (default: env LEDGER_PATH or /app/ledger)
        """
        self.ledger_path = Path(ledger_path or os.getenv("LEDGER_PATH", "/app/ledger"))

        if not BEANCOUNT_AVAILABLE:
            logger.error("Beancount not installed. Install with: pip install beancount")
            raise ImportError("Beancount library required for ledger integration")

    def get_commit_hash(self) -> str:
        """
        Get current git commit hash of ledger repository.

        Returns:
            Git commit hash (40-char SHA-1)

        Raises:
            subprocess.CalledProcessError: If git command fails
        """
        if not self.ledger_path.exists():
            raise FileNotFoundError(f"Ledger path not found: {self.ledger_path}")

        try:
            result = subprocess.check_output(
                ["git", "-C", str(self.ledger_path), "rev-parse", "HEAD"],
                stderr=subprocess.PIPE,
            )
            commit_hash = result.decode().strip()
            logger.info(f"Ledger commit hash: {commit_hash}")
            return commit_hash

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get git commit hash: {e.stderr.decode()}")
            raise

    def parse_ledger(self, ledger_file: str = "main.beancount") -> List[data.Transaction]:
        """
        Parse Beancount ledger file.

        Args:
            ledger_file: Name of ledger file (default: main.beancount)

        Returns:
            List of Beancount transaction objects

        Raises:
            FileNotFoundError: If ledger file doesn't exist
        """
        ledger_file_path = self.ledger_path / ledger_file

        if not ledger_file_path.exists():
            raise FileNotFoundError(f"Ledger file not found: {ledger_file_path}")

        logger.info(f"Parsing ledger: {ledger_file_path}")

        # Load and parse Beancount ledger
        entries, errors, options = loader.load_file(str(ledger_file_path))

        if errors:
            logger.warning(f"Beancount parse errors: {len(errors)} errors found")
            for error in errors[:10]:  # Log first 10 errors
                logger.warning(f"  {error}")

        # Filter for Transaction entries only
        transactions = [entry for entry in entries if isinstance(entry, data.Transaction)]

        logger.info(f"Parsed {len(transactions)} transactions from ledger")
        return transactions

    def extract_portfolio_transactions(
        self,
        transactions: List[data.Transaction],
        portfolio_pattern: str = "Assets:Portfolio:",
    ) -> List[LedgerTransaction]:
        """
        Extract transactions for portfolios from Beancount entries.

        Args:
            transactions: List of Beancount transaction objects
            portfolio_pattern: Account pattern to match portfolios
                              (default: "Assets:Portfolio:")

        Returns:
            List of LedgerTransaction objects
        """
        ledger_transactions = []

        for txn in transactions:
            # Iterate through postings (legs) of transaction
            for posting in txn.postings:
                if posting.account.startswith(portfolio_pattern):
                    # Extract amount and currency
                    if posting.units:
                        amt = posting.units.number
                        curr = posting.units.currency
                    else:
                        # Skip postings without units (balance assertions, etc.)
                        continue

                    ledger_txn = LedgerTransaction(
                        date=txn.date,
                        account=posting.account,
                        amount=Decimal(str(amt)),
                        currency=curr,
                        narration=txn.narration or "",
                        metadata=dict(txn.meta) if txn.meta else {},
                    )
                    ledger_transactions.append(ledger_txn)

        logger.info(f"Extracted {len(ledger_transactions)} portfolio transactions")
        return ledger_transactions

    async def store_transactions(
        self,
        transactions: List[LedgerTransaction],
        commit_hash: str,
    ) -> int:
        """
        Store ledger transactions in database.

        Args:
            transactions: List of LedgerTransaction objects
            commit_hash: Git commit hash of ledger

        Returns:
            Number of transactions stored
        """
        if not transactions:
            logger.warning("No transactions to store")
            return 0

        # Check if this commit hash already processed
        check_query = """
            SELECT COUNT(*) AS count
            FROM ledger_transactions
            WHERE ledger_commit_hash = $1
        """
        result = await execute_query(check_query, commit_hash)

        if result and result[0]["count"] > 0:
            logger.info(f"Ledger commit {commit_hash[:8]} already processed, skipping")
            return 0

        # Insert transactions
        insert_query = """
            INSERT INTO ledger_transactions (
                id,
                ledger_commit_hash,
                date,
                account,
                amount,
                currency,
                narration,
                metadata_json
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """

        stored_count = 0
        for txn in transactions:
            try:
                await execute_statement(
                    insert_query,
                    uuid4(),
                    commit_hash,
                    txn.date,
                    txn.account,
                    txn.amount,
                    txn.currency,
                    txn.narration,
                    txn.metadata,
                )
                stored_count += 1

            except Exception as e:
                logger.error(f"Failed to store transaction: {e}")
                # Continue with other transactions

        logger.info(f"Stored {stored_count}/{len(transactions)} transactions")
        return stored_count

    async def parse_and_store(
        self,
        ledger_file: str = "main.beancount",
        portfolio_pattern: str = "Assets:Portfolio:",
    ) -> Dict[str, Any]:
        """
        Parse ledger and store transactions in database (full pipeline).

        Args:
            ledger_file: Name of ledger file
            portfolio_pattern: Account pattern for portfolios

        Returns:
            Summary dict with commit_hash, transactions_parsed, transactions_stored
        """
        # Step 1: Get commit hash
        commit_hash = self.get_commit_hash()

        # Step 2: Parse ledger
        transactions = self.parse_ledger(ledger_file)

        # Step 3: Extract portfolio transactions
        portfolio_txns = self.extract_portfolio_transactions(
            transactions,
            portfolio_pattern,
        )

        # Step 4: Store in database
        stored_count = await self.store_transactions(portfolio_txns, commit_hash)

        summary = {
            "commit_hash": commit_hash,
            "transactions_parsed": len(transactions),
            "portfolio_transactions": len(portfolio_txns),
            "transactions_stored": stored_count,
        }

        logger.info(f"Ledger parse summary: {summary}")
        return summary

    async def get_portfolio_balance(
        self,
        portfolio_id: UUID,
        as_of_date: date,
        commit_hash: Optional[str] = None,
    ) -> Dict[str, Decimal]:
        """
        Get portfolio balance from ledger as of a specific date.

        Args:
            portfolio_id: Portfolio UUID
            as_of_date: Balance as-of date
            commit_hash: Optional ledger commit hash (latest if None)

        Returns:
            Dict mapping currency to balance amount
        """
        # Query ledger transactions
        query = """
            SELECT
                currency,
                SUM(amount) AS balance
            FROM ledger_transactions
            WHERE account LIKE $1
              AND date <= $2
        """
        params = [f"%{portfolio_id}%", as_of_date]

        if commit_hash:
            query += " AND ledger_commit_hash = $3"
            params.append(commit_hash)

        query += " GROUP BY currency"

        results = await execute_query(query, *params)

        balances = {row["currency"]: Decimal(str(row["balance"])) for row in results}

        logger.debug(f"Portfolio {portfolio_id} balance as of {as_of_date}: {balances}")
        return balances

    def extract_portfolio_id_from_account(self, account: str) -> Optional[UUID]:
        """
        Extract portfolio UUID from Beancount account name.

        Convention: Assets:Portfolio:<UUID>:<Security>
        Example: Assets:Portfolio:11111111-1111-1111-1111-111111111111:AAPL

        Args:
            account: Beancount account name

        Returns:
            Portfolio UUID or None if not found
        """
        parts = account.split(":")

        # Look for UUID in account path
        for part in parts:
            try:
                return UUID(part)
            except ValueError:
                continue

        return None


# ============================================================================
# Singleton
# ============================================================================


_ledger_service_instance = None


def get_ledger_service() -> LedgerService:
    """
    Get singleton LedgerService instance.

    Returns:
        LedgerService singleton
    """
    global _ledger_service_instance

    if _ledger_service_instance is None:
        _ledger_service_instance = LedgerService()

    return _ledger_service_instance


# ============================================================================
# CLI Entry Point
# ============================================================================


async def main():
    """CLI entry point for ledger parsing."""
    import argparse

    parser = argparse.ArgumentParser(description="Parse Beancount ledger and store in database")
    parser.add_argument("--ledger-path", type=str, help="Path to ledger git repository")
    parser.add_argument("--ledger-file", type=str, default="main.beancount", help="Ledger file name")
    parser.add_argument("--portfolio-pattern", type=str, default="Assets:Portfolio:", help="Portfolio account pattern")

    args = parser.parse_args()

    # Initialize service
    service = LedgerService(ledger_path=args.ledger_path)

    # Parse and store
    summary = await service.parse_and_store(
        ledger_file=args.ledger_file,
        portfolio_pattern=args.portfolio_pattern,
    )

    print("\n=== Ledger Parse Summary ===")
    print(f"Commit Hash: {summary['commit_hash']}")
    print(f"Transactions Parsed: {summary['transactions_parsed']}")
    print(f"Portfolio Transactions: {summary['portfolio_transactions']}")
    print(f"Transactions Stored: {summary['transactions_stored']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
