#!/usr/bin/env python3
"""
Fix Seed Data UUIDs

Purpose: Convert all short IDs in seed CSV files to proper UUIDs
Date: 2025-10-24
"""

import csv
import uuid
from pathlib import Path

# Generate deterministic UUIDs based on readable IDs
def gen_uuid(readable_id):
    """Generate UUID v5 based on readable ID."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, readable_id))

# Define ID mappings
ID_MAP = {
    # Portfolio IDs
    "P1": "11111111-1111-1111-1111-111111111111",

    # User IDs
    "U1": "22222222-2222-2222-2222-222222222222",

    # Security IDs (generate from symbol) - used in securities.csv
    "SEC_AAPL": gen_uuid("security.AAPL"),
    "SEC_RY": gen_uuid("security.RY"),
    "SEC_XIU": gen_uuid("security.XIU"),
    "SEC_SPY": gen_uuid("security.SPY"),
    "SEC_VFV": gen_uuid("security.VFV"),
    "SEC_TD": gen_uuid("security.TD"),
    "SEC_MSFT": gen_uuid("security.MSFT"),
    "SEC_GOOGL": gen_uuid("security.GOOGL"),
    "SEC_AMZN": gen_uuid("security.AMZN"),
    "SEC_ENB": gen_uuid("security.ENB"),
    "SEC_XIC": gen_uuid("security.XIC"),

    # Transaction IDs
    "TXN_AAPL_BUY": gen_uuid("txn.AAPL.BUY"),
    "TXN_RY_BUY": gen_uuid("txn.RY.BUY"),
    "TXN_XIU_BUY": gen_uuid("txn.XIU.BUY"),
    "TXN_AAPL_DIV1": gen_uuid("txn.AAPL.DIV1"),
    "TXN_RY_DIV1": gen_uuid("txn.RY.DIV1"),

    # Lot IDs
    "LOT_AAPL_P1": gen_uuid("lot.AAPL.P1"),
    "LOT_RY_P1": gen_uuid("lot.RY.P1"),
    "LOT_XIU_P1": gen_uuid("lot.XIU.P1"),
}

def replace_ids(value, id_map):
    """Replace short IDs with UUIDs in a value."""
    if not value or value == "":
        return value

    # Check if the value is in the ID map
    if value in id_map:
        return id_map[value]

    return value

def fix_csv_file(filepath, id_fields, id_map):
    """Fix IDs in a CSV file."""
    filepath = Path(filepath)

    if not filepath.exists():
        print(f"⚠️  File not found: {filepath}")
        return 0

    # Read all rows
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    # Replace IDs in specified fields
    count = 0
    for row in rows:
        for field in id_fields:
            if field in row:
                old_value = row[field]
                new_value = replace_ids(old_value, id_map)
                if old_value != new_value:
                    row[field] = new_value
                    count += 1

    # Write back
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Fixed {filepath.name}: {count} ID replacements in {len(rows)} rows")
    return count

def main():
    """Main execution."""
    print("=" * 80)
    print("FIXING SEED DATA UUIDs - ALL DOMAINS")
    print("=" * 80)

    base_seed_dir = Path(__file__).parent.parent / "data" / "seeds"
    portfolios_dir = base_seed_dir / "portfolios"
    symbols_dir = base_seed_dir / "symbols"

    print(f"\nBase seed directory: {base_seed_dir}")
    print(f"\nID Mappings ({len(ID_MAP)} total):")
    for short_id, uuid_val in sorted(ID_MAP.items())[:10]:
        print(f"  {short_id:20} → {uuid_val}")
    if len(ID_MAP) > 10:
        print(f"  ... and {len(ID_MAP) - 10} more")

    print("\n" + "-" * 80)

    total_replacements = 0

    # Fix securities.csv (CRITICAL - source of truth)
    print("\n🔧 Fixing securities.csv (source of truth for security UUIDs)...")
    total_replacements += fix_csv_file(
        symbols_dir / "securities.csv",
        id_fields=["id"],
        id_map=ID_MAP
    )

    # Fix portfolios.csv
    print("\n🔧 Fixing portfolios.csv...")
    total_replacements += fix_csv_file(
        portfolios_dir / "portfolios.csv",
        id_fields=["id", "user_id"],
        id_map=ID_MAP
    )

    # Fix transactions.csv
    print("\n🔧 Fixing transactions.csv...")
    total_replacements += fix_csv_file(
        portfolios_dir / "transactions.csv",
        id_fields=["id", "portfolio_id", "security_id"],
        id_map=ID_MAP
    )

    # Fix lots.csv
    print("\n🔧 Fixing lots.csv...")
    lots_file = portfolios_dir / "lots.csv"
    lots_backup = portfolios_dir / "lots.csv.bak"

    # Try both lots.csv and lots.csv.bak
    if lots_backup.exists():
        total_replacements += fix_csv_file(
            lots_backup,
            id_fields=["id", "portfolio_id", "security_id"],
            id_map=ID_MAP
        )
        lots_backup.rename(lots_file)
        print(f"✅ Renamed lots.csv.bak → lots.csv")
    elif lots_file.exists():
        total_replacements += fix_csv_file(
            lots_file,
            id_fields=["id", "portfolio_id", "security_id"],
            id_map=ID_MAP
        )

    print("\n" + "=" * 80)
    print(f"✅ COMPLETE: {total_replacements} total ID replacements")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Verify: cat data/seeds/symbols/securities.csv")
    print("  2. Reset DB: Connect to your database and run: TRUNCATE securities, prices, lots, portfolios, transactions CASCADE;")
    print("  3. Reload: ./venv/bin/python3 scripts/seed_loader.py --all")
    print("=" * 80)

if __name__ == "__main__":
    main()
