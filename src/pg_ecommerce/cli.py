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
            # Ensure schema is applied for verification if using in-memory
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
