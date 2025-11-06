#!/usr/bin/env python3
"""
Database Schema Validation Script

This script validates the actual database schema against the documented schema
to detect and prevent documentation drift.

Usage: python backend/scripts/validate_database_schema.py
"""

import asyncio
import asyncpg
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional


class SchemaValidator:
    """Validates database schema against documentation."""
    
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
        self.errors = []
        self.warnings = []
        
    async def get_all_tables(self) -> List[str]:
        """Get all tables in the public schema."""
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        rows = await self.conn.fetch(query)
        return [row['table_name'] for row in rows]
    
    async def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get all columns for a table."""
        query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE table_name = $1
            ORDER BY ordinal_position
        """
        rows = await self.conn.fetch(query, table_name)
        return [dict(row) for row in rows]
    
    async def get_table_constraints(self, table_name: str) -> List[Dict[str, Any]]:
        """Get all constraints for a table."""
        query = """
            SELECT 
                c.conname AS constraint_name,
                c.contype AS constraint_type,
                pg_get_constraintdef(c.oid) AS constraint_definition
            FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            WHERE t.relname = $1
            ORDER BY c.conname
        """
        rows = await self.conn.fetch(query, table_name)
        return [dict(row) for row in rows]
    
    async def get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get all indexes for a table."""
        query = """
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = $1
            ORDER BY indexname
        """
        rows = await self.conn.fetch(query, table_name)
        return [dict(row) for row in rows]
    
    async def validate_critical_tables(self):
        """Validate critical tables have expected structure."""
        critical_tables = {
            'lots': {
                'required_columns': [
                    'id', 'portfolio_id', 'security_id', 
                    'quantity_open', 'quantity_original',  # Full names after Migration 001
                    'cost_basis', 'acquisition_date'
                ],
                'deprecated_columns': ['quantity'],  # Should be marked as deprecated
                'indexes': ['idx_lots_quantity_open'],  # Should exist
            },
            'transactions': {
                'required_columns': [
                    'id', 'portfolio_id', 'transaction_type',
                    'security_id', 'transaction_date', 'quantity',
                    'price', 'amount', 'realized_pl'  # Added by Migration 017
                ]
            },
            'portfolios': {
                'required_columns': [
                    'id', 'name', 'base_currency', 
                    'user_id', 'cost_basis_method'  # user_id not owner_id
                ]
            },
            'cost_basis_method_audit': {  # Added by Migration 018
                'required_columns': [
                    'id', 'portfolio_id', 'old_method', 
                    'new_method', 'changed_by', 'changed_at'
                ]
            }
        }
        
        tables = await self.get_all_tables()
        
        for table_name, requirements in critical_tables.items():
            if table_name not in tables:
                self.errors.append(f"Critical table '{table_name}' is missing!")
                continue
            
            columns = await self.get_table_columns(table_name)
            column_names = {col['column_name'] for col in columns}
            
            # Check required columns
            for required_col in requirements.get('required_columns', []):
                if required_col not in column_names:
                    self.errors.append(
                        f"Table '{table_name}' missing required column '{required_col}'"
                    )
            
            # Check deprecated columns
            for deprecated_col in requirements.get('deprecated_columns', []):
                if deprecated_col in column_names:
                    # Should have a comment marking it as deprecated
                    comment_query = """
                        SELECT obj_description(
                            (SELECT c.oid FROM pg_class c 
                             JOIN pg_namespace n ON n.oid = c.relnamespace
                             WHERE n.nspname = 'public' AND c.relname = $1),
                            'pg_class'
                        ) || ' ' || col_description(
                            (SELECT c.oid FROM pg_class c 
                             JOIN pg_namespace n ON n.oid = c.relnamespace
                             WHERE n.nspname = 'public' AND c.relname = $1),
                            (SELECT ordinal_position FROM information_schema.columns
                             WHERE table_name = $1 AND column_name = $2)
                        ) as comment
                    """
                    comment_row = await self.conn.fetchval(comment_query, table_name, deprecated_col)
                    if not comment_row or 'deprecated' not in comment_row.lower():
                        self.warnings.append(
                            f"Column '{table_name}.{deprecated_col}' should be marked as deprecated"
                        )
            
            # Check indexes
            if 'indexes' in requirements:
                indexes = await self.get_table_indexes(table_name)
                index_names = {idx['indexname'] for idx in indexes}
                
                for required_idx in requirements['indexes']:
                    if required_idx not in index_names:
                        self.warnings.append(
                            f"Table '{table_name}' missing expected index '{required_idx}'"
                        )
    
    async def check_field_naming_consistency(self):
        """Check for field naming inconsistencies."""
        # Check lots table specifically for the quantity field issue
        lots_columns = await self.get_table_columns('lots')
        
        has_qty_open = any(col['column_name'] == 'qty_open' for col in lots_columns)
        has_quantity_open = any(col['column_name'] == 'quantity_open' for col in lots_columns)
        
        if has_qty_open and not has_quantity_open:
            self.errors.append(
                "Field naming issue: 'lots' table has 'qty_open' but Migration 001 should have renamed it to 'quantity_open'"
            )
        elif has_quantity_open and not has_qty_open:
            print("✓ Field names correctly standardized: 'quantity_open' found (Migration 001 executed)")
        elif has_qty_open and has_quantity_open:
            self.errors.append(
                "Field naming issue: Both 'qty_open' and 'quantity_open' exist in lots table!"
            )
    
    async def generate_schema_documentation(self) -> Dict[str, Any]:
        """Generate complete schema documentation from database."""
        tables = await self.get_all_tables()
        schema_doc = {
            'generated_at': datetime.now().isoformat(),
            'total_tables': len(tables),
            'tables': {}
        }
        
        for table_name in tables:
            columns = await self.get_table_columns(table_name)
            constraints = await self.get_table_constraints(table_name)
            indexes = await self.get_table_indexes(table_name)
            
            schema_doc['tables'][table_name] = {
                'columns': columns,
                'constraints': [
                    {
                        'name': c['constraint_name'],
                        'type': self._constraint_type_name(c['constraint_type']),
                        'definition': c['constraint_definition']
                    }
                    for c in constraints
                ],
                'indexes': [
                    {
                        'name': idx['indexname'],
                        'definition': idx['indexdef']
                    }
                    for idx in indexes
                ]
            }
        
        return schema_doc
    
    def _constraint_type_name(self, contype: str) -> str:
        """Convert constraint type code to name."""
        mapping = {
            'p': 'PRIMARY KEY',
            'f': 'FOREIGN KEY',
            'u': 'UNIQUE',
            'c': 'CHECK',
            't': 'TRIGGER',
            'x': 'EXCLUSION'
        }
        return mapping.get(contype, contype)
    
    async def validate(self) -> bool:
        """Run all validation checks."""
        print("=" * 60)
        print("DATABASE SCHEMA VALIDATION")
        print("=" * 60)
        
        # Get basic statistics
        tables = await self.get_all_tables()
        print(f"\n📊 Database Statistics:")
        print(f"  - Total tables: {len(tables)}")
        
        # Check critical tables
        print("\n🔍 Validating critical tables...")
        await self.validate_critical_tables()
        
        # Check field naming
        print("\n🔍 Checking field naming consistency...")
        await self.check_field_naming_consistency()
        
        # Report results
        print("\n" + "=" * 60)
        if self.errors:
            print("❌ VALIDATION FAILED")
            print("\nErrors found:")
            for error in self.errors:
                print(f"  ❌ {error}")
        else:
            print("✅ VALIDATION PASSED")
        
        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f"  ⚠️ {warning}")
        
        print("=" * 60)
        
        return len(self.errors) == 0


async def main():
    """Main entry point."""
    # Get database URL
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # Create validator
        validator = SchemaValidator(conn)
        
        # Run validation
        success = await validator.validate()
        
        # Generate schema documentation
        print("\n📝 Generating schema documentation...")
        schema_doc = await validator.generate_schema_documentation()
        
        # Save to file
        output_file = "backend/db/actual_schema.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(schema_doc, f, indent=2, default=str)
        print(f"  Schema documentation saved to: {output_file}")
        
        # Close connection
        await conn.close()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())