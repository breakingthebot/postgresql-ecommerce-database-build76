"""
Command-line interface for PostgreSQL E-Commerce database suite.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from pg_ecommerce import __version__
from pg_ecommerce.db import DatabaseConnection
from pg_ecommerce.schema import SchemaManager
from pg_ecommerce.seeder import DataSeeder


def build_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="pg-ecommerce",
        description="PostgreSQL E-Commerce Database Management and Optimization CLI",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"pg-ecommerce {__version__}",
        help="Show program's version number and exit",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="PostgreSQL connection string (defaults to DATABASE_URL environment variable)",
    )
    parser.add_argument(
        "--in-memory",
        action="store_true",
        help="Force in-memory relational verification engine without connecting to external database",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: migrate
    subparsers.add_parser("migrate", help="Apply core schema DDL migrations")

    # Command: verify
    subparsers.add_parser("verify", help="Verify database schema tables, views, and integrity")

    # Command: info
    subparsers.add_parser("info", help="Display database metadata, engine type, and table inventory")

    # Command: seed
    seed_parser = subparsers.add_parser("seed", help="Populate database with curated or synthetic e-commerce data")
    seed_parser.add_argument(
        "--mode",
        choices=["curated", "synthetic"],
        default="curated",
        help="Seeding mode: 'curated' (rich SQL seed) or 'synthetic' (configurable volume generator)",
    )
    seed_parser.add_argument(
        "--products",
        type=int,
        default=50,
        help="Number of products to generate (synthetic mode only)",
    )
    seed_parser.add_argument(
        "--customers",
        type=int,
        default=30,
        help="Number of customers to generate (synthetic mode only)",
    )
    seed_parser.add_argument(
        "--orders",
        type=int,
        default=60,
        help="Number of orders to generate (synthetic mode only)",
    )
    seed_parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic random seed for reproducibility",
    )

    # Command: indexes
    idx_parser = subparsers.add_parser("indexes", help="Manage and verify advanced PostgreSQL indexes")
    idx_parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply advanced indexes from sql/03_indexes.sql",
    )
    idx_parser.add_argument(
        "--list",
        action="store_true",
        help="List all active database indexes and their target tables",
    )
    idx_parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify all expected composite, partial, expression, and GIN indexes exist",
    )

    # Command: export-sql
    export_parser = subparsers.add_parser("export-sql", help="Concatenate and output raw SQL files")
    export_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Optional destination file path for exported SQL",
    )

    return parser


def main(args: Optional[List[str]] = None) -> int:
    """CLI execution entry point."""
    parser = build_parser()
    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 0

    db = DatabaseConnection(
        database_url=parsed_args.database_url,
        in_memory=parsed_args.in_memory,
    )
    schema_mgr = SchemaManager(db=db)

    try:
        if parsed_args.command == "migrate":
            print(f"[*] Applying core schema DDL on engine: {db.engine_type.upper()}...")
            schema_mgr.apply_schema("01_schema.sql")
            report = schema_mgr.verify_schema()
            if report["is_valid"]:
                print(f"[+] Successfully migrated! Tables created: {report['total_tables']}, Views: {report['total_views']}")
                return 0
            else:
                print(f"[-] Migration completed with missing items: {report['missing_tables']}")
                return 1

        elif parsed_args.command == "verify":
            if db.in_memory and len(schema_mgr.get_tables()) == 0:
                schema_mgr.apply_schema("01_schema.sql")
            report = schema_mgr.verify_schema()
            print(json.dumps(report, indent=2))
            return 0 if report["is_valid"] else 1

        elif parsed_args.command == "info":
            if db.in_memory and len(schema_mgr.get_tables()) == 0:
                schema_mgr.apply_schema("01_schema.sql")
            tables = schema_mgr.get_tables()
            views = schema_mgr.get_views()
            print(f"Database Engine: {db.engine_type.upper()}")
            print(f"Total Tables:    {len(tables)}")
            for tbl in tables:
                print(f"  - {tbl}")
            print(f"Total Views:     {len(views)}")
            for vw in views:
                print(f"  - {vw}")
            return 0

        elif parsed_args.command == "seed":
            if db.in_memory and len(schema_mgr.get_tables()) == 0:
                schema_mgr.apply_schema("01_schema.sql")

            seeder = DataSeeder(db=db, seed=parsed_args.seed)
            if parsed_args.mode == "curated":
                print(f"[*] Applying curated seed data from sql/02_seed_data.sql...")
                seeder.apply_curated_seed()
            else:
                print(f"[*] Generating synthetic dataset: {parsed_args.products} products, {parsed_args.customers} customers, {parsed_args.orders} orders (seed={parsed_args.seed})...")
                seeder.generate_synthetic_dataset(
                    num_products=parsed_args.products,
                    num_customers=parsed_args.customers,
                    num_orders=parsed_args.orders,
                )

            counts = seeder.get_table_counts()
            print(f"[+] Seeding complete! Populated row counts:")
            for tbl, count in counts.items():
                print(f"  - {tbl:22}: {count} rows")
            return 0

        elif parsed_args.command == "indexes":
            if db.in_memory and len(schema_mgr.get_tables()) == 0:
                schema_mgr.apply_schema("01_schema.sql")

            if parsed_args.apply:
                print(f"[*] Applying advanced indexes from sql/03_indexes.sql...")
                schema_mgr.apply_indexes("03_indexes.sql")
                print(f"[+] Advanced indexes applied successfully!")

            if parsed_args.verify:
                # If indexes haven't been applied yet in in-memory mode, apply them
                if db.in_memory and len(schema_mgr.get_indexes()) == 0:
                    schema_mgr.apply_indexes("03_indexes.sql")
                report = schema_mgr.verify_indexes()
                print(json.dumps(report, indent=2))
                return 0 if report["is_valid"] else 1

            if parsed_args.list or (not parsed_args.apply and not parsed_args.verify):
                if db.in_memory and len(schema_mgr.get_indexes()) == 0:
                    schema_mgr.apply_indexes("03_indexes.sql")
                indexes = schema_mgr.get_indexes()
                print(f"Total Custom Indexes: {len(indexes)}")
                for idx in indexes:
                    print(f"  - {idx['name']:36} ON {idx['table_name']}")
                return 0

            return 0

        elif parsed_args.command == "export-sql":
            sql_script = schema_mgr.get_sql_script("01_schema.sql")
            if parsed_args.output:
                out_path = Path(parsed_args.output)
                out_path.write_text(sql_script, encoding="utf-8")
                print(f"[+] Exported SQL script to {out_path} ({len(sql_script)} bytes)")
            else:
                print(sql_script)
            return 0

    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
