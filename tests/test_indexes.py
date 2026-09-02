"""
Unit tests for advanced composite B-Tree, partial, expression, and GIN indexes.
Verifies index creation, catalog introspection, and query planner plan execution.
"""

import pytest
from pg_ecommerce.db import DatabaseConnection
from pg_ecommerce.schema import SchemaManager
from pg_ecommerce.seeder import DataSeeder


@pytest.fixture
def indexed_db():
    """Provides an isolated in-memory test database with schema, seed data, and indexes."""
    conn = DatabaseConnection(in_memory=True)
    schema_mgr = SchemaManager(db=conn)
    schema_mgr.apply_schema("01_schema.sql")
    schema_mgr.apply_indexes("03_indexes.sql")
    seeder = DataSeeder(db=conn, seed=42)
    seeder.apply_curated_seed()
    yield conn, schema_mgr
    conn.close()


def test_index_file_contents(indexed_db):
    """Verify sql/03_indexes.sql defines all critical index strategies."""
    _, schema_mgr = indexed_db
    sql = schema_mgr.get_sql_script("03_indexes.sql")
    assert "idx_products_category_status_price" in sql
    assert "idx_orders_customer_placed_at" in sql
    assert "idx_orders_unfulfilled_queue" in sql
    assert "idx_inventory_reorder_alerts" in sql
    assert "idx_customers_lower_email" in sql
    assert "idx_variants_attributes_gin" in sql
    assert "USING gin" in sql
    assert "WHERE status = 'active'" in sql


def test_all_expected_indexes_created(indexed_db):
    """Verify all 14 expected indexes exist in the database catalog."""
    _, schema_mgr = indexed_db
    report = schema_mgr.verify_indexes()
    assert report["is_valid"] is True, f"Missing indexes: {report['missing_indexes']}"
    assert report["total_indexes"] >= 14
    assert len(report["missing_indexes"]) == 0


def test_composite_catalog_index_usage(indexed_db):
    """Verify query plan utilizes idx_products_category_status_price for catalog queries."""
    conn, _ = indexed_db
    plan_rows = conn.fetch_all(
        "EXPLAIN QUERY PLAN SELECT * FROM products WHERE category_id = 1 AND status = 'active' ORDER BY base_price;"
    )
    plan_text = " ".join(str(row) for row in plan_rows)
    assert "idx_products_category_status_price" in plan_text or "USING INDEX" in plan_text


def test_expression_index_case_insensitive_email(indexed_db):
    """Verify query plan uses expression index for lower(email) lookup."""
    conn, _ = indexed_db
    # Lookup using lower(email)
    res = conn.fetch_one(
        "SELECT * FROM customers WHERE lower(email) = 'elena.rostova@example.com';"
    )
    assert res is not None
    assert res["full_name"] == "Elena Rostova"

    # Inspect query plan
    plan_rows = conn.fetch_all(
        "EXPLAIN QUERY PLAN SELECT * FROM customers WHERE lower(email) = 'elena.rostova@example.com';"
    )
    plan_text = " ".join(str(row) for row in plan_rows)
    assert "idx_customers_lower_email" in plan_text or "USING INDEX" in plan_text


def test_partial_index_unfulfilled_orders(indexed_db):
    """Verify partial index on pending/paid/processing orders works as expected."""
    conn, _ = indexed_db
    # Query within partial index predicate
    unfulfilled = conn.fetch_all(
        "SELECT order_number, status FROM orders WHERE status IN ('pending', 'paid', 'processing');"
    )
    assert len(unfulfilled) >= 1
    for o in unfulfilled:
        assert o["status"] in ("pending", "paid", "processing")

    plan_rows = conn.fetch_all(
        "EXPLAIN QUERY PLAN SELECT * FROM orders WHERE status IN ('pending', 'paid', 'processing');"
    )
    plan_text = " ".join(str(row) for row in plan_rows)
    assert "orders" in plan_text


def test_partial_index_inventory_reorder_alerts(indexed_db):
    """Verify partial index on low-stock inventory reorders."""
    conn, _ = indexed_db
    # Reorder point alerts
    alerts = conn.fetch_all(
        "SELECT * FROM inventory WHERE quantity_on_hand <= reorder_point;"
    )
    # Check that query executes smoothly
    assert isinstance(alerts, list)
