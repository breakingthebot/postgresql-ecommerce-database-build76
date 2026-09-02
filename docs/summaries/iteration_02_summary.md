# Iteration 02 Summary: Deterministic Synthetic Data Generator & Seeder

- **Project**: PostgreSQL E-Commerce Database (Build 76)
- **Version**: `v1.1.0`
- **Date**: 2026-09-02
- **Status**: Completed & Verified

---

## 1. What Was Built (Plain English)
In this iteration, we engineered a high-performance, deterministic synthetic data generator and database seeder (`DataSeeder`) and introduced curated SQL seeding capabilities. Populating empty relational schemas with realistic, high-cardinality data is essential for testing query optimization, index efficiency, and full-text search relevance.

The seeder operates in two distinct modes:
1. **Curated Mode (`sql/02_seed_data.sql`)**: Injects rich human-readable e-commerce data including real-world brand profiles (Apex Audio, Volt Electronics, Nordic Gear), hierarchical category trees, realistic audio and apparel products with multi-variant SKUs, active inventory reservations, valid customer accounts, coupon codes, and verified customer reviews.
2. **Synthetic Mode (`pg-ecommerce seed --mode synthetic`)**: Deterministically generates arbitrary scale data (e.g. 50 products, 30 customers, 60 orders, or thousands of records) using reproducible pseudo-random seeds. It builds the relational graph topologically in DAG order, automatically computing line totals and orders totals to strictly satisfy database `CHECK` constraints (`chk_line_total_matches`, `chk_order_total_balance`, `chk_inventory_reserved_lte_hand`).

---

## 2. Key Files Introduced & Component Connections

| File Path | Role & Purpose | Connections / Dependencies |
| :--- | :--- | :--- |
| `sql/02_seed_data.sql` | Production SQL script with curated records for all 12 tables; supports direct execution via `psql` or CLI. | Executed by `seeder.py` and PostgreSQL tools. |
| `src/pg_ecommerce/seeder.py` | `DataSeeder` engine with reproducible random seed generation, topological DAG generation, and row count reporting. | Uses `db.py` to insert records across all 12 tables. |
| `src/pg_ecommerce/cli.py` | Added `seed` subcommand with options (`--mode`, `--products`, `--customers`, `--orders`, `--seed`). | Main CLI entry point registered in `pyproject.toml`. |
| `tests/test_seeder.py` | Pytest suite verifying curated and synthetic seeding, constraint satisfaction, and view aggregations. | Tests `seeder.py` and `sql/02_seed_data.sql`. |
| `tests/test_cli.py` | Extended CLI test suite testing `seed --mode curated` and `seed --mode synthetic`. | Tests CLI arguments and output formats. |
| `src/pg_ecommerce/db.py` | Enhanced SQLite translation engine with interval arithmetic parsing (`INTERVAL '...'`) and float rounding. | Shared database connection engine. |

---

## 3. Automated Test Verification
All 16 unit and integration tests passed in 0.41 seconds:
- `test_cli_version`: PASSED
- `test_cli_migrate`: PASSED
- `test_cli_verify`: PASSED
- `test_cli_info`: PASSED
- `test_cli_seed_curated`: PASSED
- `test_cli_seed_synthetic`: PASSED
- `test_cli_export_sql`: PASSED
- `test_schema_file_exists`: PASSED
- `test_tables_created`: PASSED
- `test_views_created`: PASSED
- `test_schema_verification_passes`: PASSED
- `test_customer_address_relational_cascade`: PASSED
- `test_product_variant_inventory_integrity`: PASSED
- `test_curated_seed_application`: PASSED
- `test_synthetic_seed_generation_and_constraints`: PASSED
- `test_view_aggregations_with_seed_data`: PASSED

---

## 4. Manual Verification Steps
To test this iteration manually in another terminal window:

```bash
# 1. Navigate to Build_76 folder and activate venv
cd C:\Users\marve\Desktop\AI-286-Builds\Build_76
.\venv\Scripts\activate

# 2. Seed database in curated mode
pg-ecommerce --in-memory seed --mode curated

# 3. Seed database in synthetic mode with custom volumes
pg-ecommerce --in-memory seed --mode synthetic --products 25 --customers 20 --orders 50 --seed 123

# 4. Run automated test suite
pytest -v
```
