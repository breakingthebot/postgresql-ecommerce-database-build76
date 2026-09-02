# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-09-02

### Added
- Advanced indexing suite in `sql/03_indexes.sql` featuring 14 production indexes:
  - Composite B-Tree indexes: `idx_products_category_status_price`, `idx_orders_customer_placed_at`, `idx_order_items_order_variant`, `idx_reviews_product_rating_helpful`, and `idx_categories_parent_path`.
  - Partial indexes: `idx_orders_unfulfilled_queue` (excluding >80% fulfilled orders), `idx_products_active_featured`, `idx_inventory_reorder_alerts`, and `idx_coupons_active_valid`.
  - Expression / Functional indexes: `idx_customers_lower_email` and `idx_variants_lower_sku` for fast case-insensitive lookups.
  - GIN indexes: `idx_variants_attributes_gin` (`jsonb_path_ops` for fast JSONB containment `@>`), `idx_products_tags_gin` (array overlap), and `idx_orders_shipping_address_gin`.
- Index inspection and verification methods in `SchemaManager` (`apply_indexes`, `get_indexes`, `verify_indexes`).
- New CLI command `pg-ecommerce indexes` with `--apply`, `--list`, and `--verify` actions.
- GIN and partial index SQL syntax translation in `src/pg_ecommerce/db.py` for SQLite in-memory execution.
- Comprehensive unit test suite covering index creation, plan inspection, and expression lookups (8 new tests, 24 total tests).

## [1.1.0] - 2026-09-02

### Added
- Deterministic synthetic data generator and seeder engine (`src/pg_ecommerce/seeder.py`).
- Curated production-grade SQL seed dataset in `sql/02_seed_data.sql` with real-world products, categories, variants, inventory, and reviews.
- New CLI command `pg-ecommerce seed` supporting `--mode [curated|synthetic]`, `--products`, `--customers`, `--orders`, and `--seed`.
- Constraint verification for orders totals (`chk_order_total_balance`), line items (`chk_line_total_matches`), and inventory limits (`chk_inventory_reserved_lte_hand`).
- Interval arithmetic translation (`INTERVAL '...'`) and float rounding translation in `src/pg_ecommerce/db.py` for SQLite in-memory execution.
- Comprehensive test suite for seeder and seed CLI commands (5 new tests, 16 total tests).

## [1.0.0] - 2026-09-02

### Added
- Core relational database schema in `sql/01_schema.sql` supporting 12 normalized tables:
  - `customers` (UUID PK, role ENUM, email format validation)
  - `addresses` (shipping/billing address types, cascade deletion)
  - `categories` (hierarchical tree with parent-child adjacency)
  - `brands` (manufacturer/brand profiles)
  - `products` (status ENUM, price check constraints, tags, metadata JSONB, TSVECTOR search column)
  - `product_variants` (SKU uniqueness, JSONB attribute specifications, weight, price overrides)
  - `inventory` (warehouse codes, quantity on hand, quantity reserved, non-negative check constraints)
  - `coupons` (promotional codes, percentage/fixed discounts, usage tracking, date range checks)
  - `orders` (UUID PK, order numbers, calculated total balance constraint, JSONB address snapshots)
  - `order_items` (immutable price/SKU/name snapshots, calculated line total check)
  - `order_status_history` (automated audit log tracking status transitions)
  - `reviews` (1-5 star ratings, verified purchase flag, unique customer-product constraint)
- PL/pgSQL triggers and functions:
  - `fn_trigger_update_timestamp()` for automatic `updated_at` timestamps on customers, products, variants, and orders.
  - `fn_audit_order_status_change()` for automated audit logging into `order_status_history`.
- Analytical database views:
  - `vw_product_catalog_details` for aggregated product catalog metrics, price ranges, and live stock.
  - `vw_customer_order_summary` for customer lifetime order counts, revenue, and average order value.
- Python management package and CLI (`src/pg_ecommerce`):
  - Universal database client (`db.py`) supporting live PostgreSQL connections via `psycopg` and zero-dependency in-memory translation.
  - Schema manager (`schema.py`) executing migrations and schema validation.
  - Command-line interface (`cli.py`) with `--version`, `migrate`, `verify`, `info`, and `export-sql`.
- Automated test suite covering schema migrations, foreign keys, cascades, and CLI workflows (11 tests).
- GitHub Actions CI workflow (`.github/workflows/ci.yml`) testing on Python 3.10-3.13 with PostgreSQL 16 Alpine container.
