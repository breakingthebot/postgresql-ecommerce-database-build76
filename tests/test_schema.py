"""
Unit tests for core schema definition, migration, and relational integrity.
"""

import pytest
from pg_ecommerce.db import DatabaseConnection
from pg_ecommerce.schema import SchemaManager


@pytest.fixture
def db():
    """Provides a fresh isolated in-memory database connection."""
    conn = DatabaseConnection(in_memory=True)
    yield conn
    conn.close()


@pytest.fixture
def schema_manager(db):
    """Provides a SchemaManager connected to the in-memory test database."""
    manager = SchemaManager(db=db)
    manager.apply_schema("01_schema.sql")
    return manager


def test_schema_file_exists(schema_manager):
    """Verify that 01_schema.sql is readable and non-empty."""
    sql = schema_manager.get_sql_script("01_schema.sql")
    assert len(sql) > 500
    assert "CREATE TABLE IF NOT EXISTS customers" in sql
    assert "CREATE TABLE IF NOT EXISTS products" in sql
    assert "CREATE TABLE IF NOT EXISTS orders" in sql


def test_tables_created(schema_manager):
    """Verify all 12 expected relational tables exist after migration."""
    tables = schema_manager.get_tables()
    for expected in SchemaManager.EXPECTED_TABLES:
        assert expected in tables, f"Expected table '{expected}' not found in database"


def test_views_created(schema_manager):
    """Verify all expected analytical views exist after migration."""
    views = schema_manager.get_views()
    for expected in SchemaManager.EXPECTED_VIEWS:
        assert expected in views, f"Expected view '{expected}' not found in database"


def test_schema_verification_passes(schema_manager):
    """Verify schema verification report passes with zero missing elements."""
    report = schema_manager.verify_schema()
    assert report["is_valid"] is True
    assert len(report["missing_tables"]) == 0
    assert len(report["missing_views"]) == 0
    assert report["total_tables"] >= 12
    assert report["total_views"] >= 2


def test_customer_address_relational_cascade(db, schema_manager):
    """Test customer creation and address cascade deletion."""
    # Insert customer
    db.execute("""
        INSERT INTO customers (id, email, full_name, role)
        VALUES ('c1111111-1111-1111-1111-111111111111', 'test@example.com', 'Alice Smith', 'customer');
    """)
    # Insert address
    db.execute("""
        INSERT INTO addresses (id, customer_id, recipient_name, street_line1, city, state, postal_code, country)
        VALUES ('a1111111-1111-1111-1111-111111111111', 'c1111111-1111-1111-1111-111111111111',
                'Alice Smith', '123 Market St', 'San Francisco', 'CA', '94105', 'US');
    """)

    addr = db.fetch_one("SELECT * FROM addresses WHERE customer_id = 'c1111111-1111-1111-1111-111111111111';")
    assert addr is not None
    assert addr["city"] == "San Francisco"

    # Delete customer and verify address cascaded
    db.execute("DELETE FROM customers WHERE id = 'c1111111-1111-1111-1111-111111111111';")
    addr_after = db.fetch_one("SELECT * FROM addresses WHERE customer_id = 'c1111111-1111-1111-1111-111111111111';")
    assert addr_after is None


def test_product_variant_inventory_integrity(db, schema_manager):
    """Test inserting brand, category, product, variant, and inventory records."""
    db.execute("INSERT INTO brands (id, name, slug) VALUES (1, 'Acme Corp', 'acme-corp');")
    db.execute("INSERT INTO categories (id, name, slug, hierarchy_path) VALUES (1, 'Electronics', 'electronics', '/electronics');")
    db.execute("""
        INSERT INTO products (id, brand_id, category_id, name, slug, base_price, status)
        VALUES (1, 1, 1, 'Noise Cancelling Headphones', 'noise-cancelling-headphones', 199.99, 'active');
    """)
    db.execute("""
        INSERT INTO product_variants (id, product_id, sku, attributes, price_override)
        VALUES (1, 1, 'NCH-BLK-01', '{"color": "black"}', 199.99);
    """)
    db.execute("""
        INSERT INTO inventory (variant_id, warehouse_code, quantity_on_hand, quantity_reserved, reorder_point)
        VALUES (1, 'WH-MAIN', 50, 5, 10);
    """)

    catalog_row = db.fetch_one("SELECT * FROM vw_product_catalog_details WHERE product_id = 1;")
    assert catalog_row is not None
    assert catalog_row["product_name"] == "Noise Cancelling Headphones"
    assert catalog_row["brand_name"] == "Acme Corp"
    assert catalog_row["category_name"] == "Electronics"
    assert catalog_row["total_variants"] == 1
    assert catalog_row["total_available_stock"] == 45
