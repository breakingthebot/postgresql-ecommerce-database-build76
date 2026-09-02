# PostgreSQL E-Commerce Database

[![CI](https://github.com/breakingthebot/postgresql-ecommerce-database-build76/actions/workflows/ci.yml/badge.svg)](https://github.com/breakingthebot/postgresql-ecommerce-database-build76/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%2B-blue.svg)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)

Production-grade PostgreSQL relational database architecture for modern e-commerce platforms. Features a fully normalized schema across 12 core tables, composite constraints, JSONB attribute specifications, concurrency-safe inventory reservation locks, financial balance validation, automated PL/pgSQL audit triggers, analytical views, and an installable Python management CLI (`pg-ecommerce`).

---

## Architectural Overview

### Relational Entity-Relationship Diagram

```mermaid
erDiagram
    CUSTOMERS ||--o{ ADDRESSES : "has many"
    CUSTOMERS ||--o{ ORDERS : "places"
    CUSTOMERS ||--o{ REVIEWS : "writes"
    CATEGORIES ||--o{ CATEGORIES : "parent of"
    CATEGORIES ||--o{ PRODUCTS : "contains"
    BRANDS ||--o{ PRODUCTS : "manufactures"
    PRODUCTS ||--|{ PRODUCT_VARIANTS : "has variants"
    PRODUCTS ||--o{ REVIEWS : "receives"
    PRODUCT_VARIANTS ||--|| INVENTORY : "tracks stock"
    PRODUCT_VARIANTS ||--o{ ORDER_ITEMS : "purchased as"
    COUPONS ||--o{ ORDERS : "applies to"
    ORDERS ||--|{ ORDER_ITEMS : "contains"
    ORDERS ||--o{ ORDER_STATUS_HISTORY : "audits state"

    CUSTOMERS {
        uuid id PK
        string email UK
        string full_name
        enum role
        jsonb metadata
        timestamptz created_at
    }

    PRODUCTS {
        bigint id PK
        int brand_id FK
        int category_id FK
        string name
        string slug UK
        numeric base_price
        enum status
        tsvector search_vector
    }

    PRODUCT_VARIANTS {
        bigint id PK
        bigint product_id FK
        string sku UK
        jsonb attributes
        numeric price_override
    }

    INVENTORY {
        bigint variant_id PK,FK
        string warehouse_code
        int quantity_on_hand
        int quantity_reserved
        int reorder_point
    }

    ORDERS {
        uuid id PK
        uuid customer_id FK
        int coupon_id FK
        string order_number UK
        enum status
        numeric subtotal
        numeric discount_amount
        numeric tax_amount
        numeric shipping_fee
        numeric total_amount
    }

    ORDER_ITEMS {
        bigint id PK
        uuid order_id FK
        bigint variant_id FK
        string product_name_snapshot
        string sku_snapshot
        numeric unit_price
        int quantity
        numeric line_total
    }
```

---

## Core Schema Features

1. **Normalized Multi-Domain Schema**:
   - **Identity & Address Management**: `customers` and `addresses` with UUID primary keys, role-based access control (`customer`, `staff`, `admin`), email regex verification, and cascading address deletions.
   - **Catalog & JSONB Variant Attributes**: Multi-level hierarchical `categories` (parent-child adjacency with path tracking), `brands`, `products`, and `product_variants` supporting flexible JSONB attribute key-values (e.g. `{"color": "Midnight Blue", "storage": "512GB"}`).
   - **Inventory Reservation Engine**: `inventory` table tracking `quantity_on_hand` and `quantity_reserved` with database-enforced CHECK constraints (`quantity_reserved <= quantity_on_hand`) preventing overselling under high concurrency.
   - **Immutable Order Snapshots & Financial Integrity**: `orders` and `order_items` snapshot product names, SKUs, and historical unit prices at time of checkout. Constraints guarantee `line_total = unit_price * quantity` and `total_amount = subtotal - discount + tax + shipping`.
   - **Automated Audit Logging**: PL/pgSQL triggers (`fn_audit_order_status_change`) log all state changes into `order_status_history`.
   - **Analytical Views**:
     - `vw_product_catalog_details`: Real-time denormalized product overview with brand names, category paths, effective price ranges, active variant counts, total available stock, and review averages.
     - `vw_customer_order_summary`: Customer lifetime value (CLV) rollup calculating order frequency, total spend, and average order value.

---

## Repository Structure

```
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI matrix (Py 3.10-3.13 + Postgres 16)
├── sql/
│   └── 01_schema.sql            # Production PostgreSQL 16+ DDL & PL/pgSQL triggers
├── src/
│   └── pg_ecommerce/
│       ├── __init__.py          # Package metadata and version definition (v1.0.0)
│       ├── db.py                # PostgreSQL client with zero-dependency SQLite fallback
│       ├── schema.py            # Migration runner and schema integrity verification
│       └── cli.py               # CLI tool entry point (pg-ecommerce)
├── tests/
│   ├── test_schema.py           # Unit tests for DDL migrations, tables, and cascades
│   └── test_cli.py              # Unit tests for CLI flags and subcommands
├── docs/
│   └── summaries/
│       └── iteration_01_summary.md  # Detailed Iteration 01 summary archive
├── CHANGELOG.md                 # Project version changelog (Keep a Changelog)
├── ITERATIONS.md                # Public iteration and git commit audit log
├── LICENSE                      # MIT License
├── pyproject.toml               # Python package configuration and CLI entry points
└── requirements.txt             # Development and testing dependencies
```

---

## Installation & Quickstart

### Prerequisites
- Python 3.10 or higher
- *(Optional)* PostgreSQL 16+ (for live database execution)

### 1. Set Up Virtual Environment

```bash
# Create and activate virtual environment
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Linux / macOS
source venv/bin/activate

# Install package in editable development mode
pip install -e ".[dev]"
```

### 2. Configure Environment

Copy the template configuration:

```bash
cp .env.example .env
```

If connecting to a live PostgreSQL server, update `DATABASE_URL`:
```env
DATABASE_URL=postgresql://postgres:postgrespassword@localhost:5432/ecommerce_db
```

### 3. CLI Commands

```bash
# Display CLI version
pg-ecommerce --version

# Run schema migrations (in-memory verification engine or live PostgreSQL)
pg-ecommerce --in-memory migrate

# Verify schema completeness and table inventory
pg-ecommerce --in-memory verify

# Inspect table and view metadata
pg-ecommerce --in-memory info

# Populate database with curated realistic e-commerce seed data
pg-ecommerce --in-memory seed --mode curated

# Populate database with configurable-scale synthetic datasets
pg-ecommerce --in-memory seed --mode synthetic --products 100 --customers 50 --orders 150 --seed 42

# Export consolidated PostgreSQL DDL
pg-ecommerce export-sql --output ecommerce_schema.sql
```

---

## Running Automated Tests

Run the test suite using `pytest`:

```bash
pytest -v
```

All 16 unit and integration tests run in under 0.45 seconds without external service dependencies:
```
tests/test_cli.py::test_cli_version PASSED                      [  6%]
tests/test_cli.py::test_cli_migrate PASSED                      [ 12%]
tests/test_cli.py::test_cli_verify PASSED                       [ 18%]
tests/test_cli.py::test_cli_info PASSED                         [ 25%]
tests/test_cli.py::test_cli_seed_curated PASSED                 [ 31%]
tests/test_cli.py::test_cli_seed_synthetic PASSED               [ 37%]
tests/test_cli.py::test_cli_export_sql PASSED                   [ 43%]
tests/test_schema.py::test_schema_file_exists PASSED            [ 50%]
tests/test_schema.py::test_tables_created PASSED                [ 56%]
tests/test_schema.py::test_views_created PASSED                 [ 62%]
tests/test_schema.py::test_schema_verification_passes PASSED    [ 68%]
tests/test_schema.py::test_customer_address_relational_cascade PASSED [ 75%]
tests/test_schema.py::test_product_variant_inventory_integrity PASSED [ 81%]
tests/test_seeder.py::test_curated_seed_application PASSED      [ 87%]
tests/test_seeder.py::test_synthetic_seed_generation_and_constraints PASSED [ 93%]
tests/test_seeder.py::test_view_aggregations_with_seed_data PASSED [100%]
```

---

## Iterations & Git Commit History

| Iteration | Commit | Version | Summary | Tests | Documentation |
| :---: | :---: | :---: | :--- | :---: | :--- |
| **01** | [`293f217`](https://github.com/breakingthebot/postgresql-ecommerce-database-build76/commit/293f217) | `v1.0.0` | **Foundation & Core Relational E-Commerce Schema**: 12 normalized tables, PL/pgSQL triggers, analytical views, and Python CLI suite (`pg-ecommerce`). | 11 / 11 | [Summary](docs/summaries/iteration_01_summary.md) |
| **02** | *(pending)* | `v1.1.0` | **Deterministic Synthetic Data Generator & Seeder**: Curated & synthetic data seeder (`pg-ecommerce seed`), DAG generation, and constraint validation. | 16 / 16 | [Summary](docs/summaries/iteration_02_summary.md) |

---

## License

Distributed under the [MIT License](LICENSE). Copyright (c) 2026 BreakingTheBot.
