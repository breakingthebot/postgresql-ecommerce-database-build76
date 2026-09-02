"""
Schema management, migration executor, and database introspection.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pg_ecommerce.db import DatabaseConnection


class SchemaManager:
    """Manages database DDL execution, introspection, and schema verification."""

    EXPECTED_TABLES = [
        "customers",
        "addresses",
        "categories",
        "brands",
        "products",
        "product_variants",
        "inventory",
        "coupons",
        "orders",
        "order_items",
        "order_status_history",
        "reviews",
    ]

    EXPECTED_VIEWS = [
        "vw_product_catalog_details",
        "vw_customer_order_summary",
    ]

    def __init__(self, db: Optional[DatabaseConnection] = None, sql_dir: Optional[Path] = None):
        self.db = db or DatabaseConnection()
        if sql_dir:
            self.sql_dir = sql_dir
        else:
            # Default to sql/ directory relative to project root
            pkg_dir = Path(__file__).parent.parent.parent
            self.sql_dir = pkg_dir / "sql"

    def get_sql_script(self, filename: str) -> str:
        """Read SQL script content by filename."""
        file_path = self.sql_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"SQL file not found: {file_path}")
        return file_path.read_text(encoding="utf-8")

    def apply_schema(self, filename: str = "01_schema.sql") -> None:
        """Execute core schema DDL migration."""
        sql_content = self.get_sql_script(filename)
        self.db.execute(sql_content)

    def get_tables(self) -> List[str]:
        """List all user tables in the database."""
        if self.db.engine_type == "sqlite":
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
        else:
            query = "SELECT table_name AS name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name;"
        rows = self.db.fetch_all(query)
        return [row["name"] for row in rows]

    def get_views(self) -> List[str]:
        """List all views in the database."""
        if self.db.engine_type == "sqlite":
            query = "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name;"
        else:
            query = "SELECT table_name AS name FROM information_schema.views WHERE table_schema = 'public' ORDER BY table_name;"
        rows = self.db.fetch_all(query)
        return [row["name"] for row in rows]

    def verify_schema(self) -> Dict[str, Any]:
        """
        Verify database schema against expected tables, views, and integrity.
        Returns a verification summary dictionary.
        """
        existing_tables = set(self.get_tables())
        existing_views = set(self.get_views())

        missing_tables = [t for t in self.EXPECTED_TABLES if t not in existing_tables]
        missing_views = [v for v in self.EXPECTED_VIEWS if v not in existing_views]

        is_valid = len(missing_tables) == 0 and len(missing_views) == 0

        return {
            "is_valid": is_valid,
            "engine": self.db.engine_type,
            "total_tables": len(existing_tables),
            "total_views": len(existing_views),
            "missing_tables": missing_tables,
            "missing_views": missing_views,
            "existing_tables": sorted(list(existing_tables)),
            "existing_views": sorted(list(existing_views)),
        }
