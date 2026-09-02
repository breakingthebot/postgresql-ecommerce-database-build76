"""
Unit tests for curated and synthetic database seeding.
Verifies data distributions, foreign key references, and mathematical constraints.
"""

import pytest
from pg_ecommerce.db import DatabaseConnection
from pg_ecommerce.schema import SchemaManager
from pg_ecommerce.seeder import DataSeeder


@pytest.fixture
def test_db():
    """Provides an isolated in-memory test database with core schema applied."""
    conn = DatabaseConnection(in_memory=True)
    schema_mgr = SchemaManager(db=conn)
    schema_mgr.apply_schema("01_schema.sql")
    yield conn
    conn.close()


def test_curated_seed_application(test_db):
    """Verify curated seed data loads successfully and populates all tables."""
    seeder = DataSeeder(db=test_db)
    seeder.apply_curated_seed()

    counts = seeder.get_table_counts()
    assert counts["brands"] == 5
    assert counts["categories"] == 7
    assert counts["customers"] == 4
    assert counts["addresses"] == 3
    assert counts["products"] == 5
    assert counts["product_variants"] == 8
    assert counts["inventory"] == 8
    assert counts["coupons"] == 3
    assert counts["orders"] == 3
    assert counts["order_items"] == 5
    assert counts["order_status_history"] == 9
    assert counts["reviews"] == 4


def test_synthetic_seed_generation_and_constraints(test_db):
    """Verify synthetic seeder creates non-empty datasets satisfying all constraints."""
    seeder = DataSeeder(db=test_db, seed=123)
    counts = seeder.generate_synthetic_dataset(
        num_products=30,
        num_customers=20,
        num_orders=40,
    )

    assert counts["products"] == 30
    assert counts["customers"] == 20
    assert counts["orders"] == 40
    assert counts["product_variants"] >= 30
    assert counts["inventory"] == counts["product_variants"]
    assert counts["order_items"] >= 40
    assert counts["reviews"] >= 30

    # Verify inventory constraint: quantity_reserved <= quantity_on_hand
    inventory_violations = test_db.fetch_all(
        "SELECT * FROM inventory WHERE quantity_reserved > quantity_on_hand;"
    )
    assert len(inventory_violations) == 0, f"Found inventory constraint violations: {inventory_violations}"

    # Verify order items constraint: line_total = unit_price * quantity (within floating point precision)
    items = test_db.fetch_all("SELECT unit_price, quantity, line_total FROM order_items;")
    for itm in items:
        expected_line = round(itm["unit_price"] * itm["quantity"], 2)
        assert abs(itm["line_total"] - expected_line) < 0.01

    # Verify orders total constraint: total_amount = subtotal - discount + tax + shipping
    orders = test_db.fetch_all(
        "SELECT subtotal, discount_amount, tax_amount, shipping_fee, total_amount FROM orders;"
    )
    for ord_row in orders:
        expected_total = round(
            ord_row["subtotal"] - ord_row["discount_amount"] + ord_row["tax_amount"] + ord_row["shipping_fee"], 2
        )
        assert abs(ord_row["total_amount"] - expected_total) < 0.01


def test_view_aggregations_with_seed_data(test_db):
    """Verify analytical views produce accurate aggregations against seeded data."""
    seeder = DataSeeder(db=test_db, seed=999)
    seeder.apply_curated_seed()

    # Test catalog view
    catalog_rows = test_db.fetch_all("SELECT * FROM vw_product_catalog_details ORDER BY product_id;")
    assert len(catalog_rows) == 5
    first_product = catalog_rows[0]
    assert first_product["product_name"] == "Apex Studio Pro ANC Headphones"
    assert first_product["brand_name"] == "Apex Audio"
    assert first_product["total_variants"] == 2
    assert first_product["total_available_stock"] == (120 - 15) + (85 - 10)  # 180 total stock
    assert first_product["total_reviews"] == 1
    assert first_product["average_rating"] == 5.0

    # Test customer summary view
    customer_summaries = test_db.fetch_all("SELECT * FROM vw_customer_order_summary WHERE total_orders > 0;")
    assert len(customer_summaries) == 3
    for cs in customer_summaries:
        assert cs["total_orders"] >= 1
        assert cs["lifetime_spend"] > 0
        assert cs["average_order_value"] > 0
