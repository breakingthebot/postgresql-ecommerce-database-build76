# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
