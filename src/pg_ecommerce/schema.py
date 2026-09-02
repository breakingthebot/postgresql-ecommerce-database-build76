"""
Schema management, migration executor, index inspector, and database introspection.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pg_ecommerce.db import DatabaseConnection


class SchemaManager:
    """Manages database DDL execution, index introspection, and schema verification."""

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

    EXPECTED_INDEXES = [
        "idx_products_category_status_price",
        "idx_orders_customer_placed_at",
        "idx_order_items_order_variant",
        "idx_reviews_product_rating_helpful",
        "idx_categories_parent_path",
        "idx_products_active_featured",
        "idx_orders_unfulfilled_queue",
        "idx_inventory_reorder_alerts",
        "idx_coupons_active_valid",
        "idx_customers_lower_email",
        "idx_variants_lower_sku",
        "idx_variants_attributes_gin",
        "idx_products_tags_gin",
        "idx_orders_shipping_address_gin",
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

    def apply_indexes(self, filename: str = "03_indexes.sql") -> None:
        """Apply advanced composite, partial, expression, and GIN indexes."""
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

    def get_indexes(self) -> List[Dict[str, Any]]:
        """List all custom non-system indexes."""
        if self.db.engine_type == "sqlite":
            query = """
            SELECT name, tbl_name AS table_name, sql
            FROM sqlite_master
            WHERE type = 'index' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'autoindex_%'
            ORDER BY name;
            """
        else:
            query = """
            SELECT indexname AS name, tablename AS table_name, indexdef AS sql
            FROM pg_indexes
            WHERE schemaname = 'public' AND indexname NOT LIKE '%_pkey'
            ORDER BY indexname;
            """
        return self.db.fetch_all(query)

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

    def verify_indexes(self) -> Dict[str, Any]:
        """Verify presence of all expected advanced indexes."""
        indexes = self.get_indexes()
        existing_idx_names = {idx["name"] for idx in indexes}

        missing_indexes = [idx for idx in self.EXPECTED_INDEXES if idx not in existing_idx_names]
        is_valid = len(missing_indexes) == 0

        return {
            "is_valid": is_valid,
            "engine": self.db.engine_type,
            "total_indexes": len(indexes),
            "expected_indexes": len(self.EXPECTED_INDEXES),
            "missing_indexes": missing_indexes,
            "existing_indexes": sorted(list(existing_idx_names)),
        }
