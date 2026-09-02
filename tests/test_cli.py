"""
Unit tests for CLI commands and argument parsing.
"""

from io import StringIO
import sys
from pg_ecommerce import __version__
from pg_ecommerce.cli import main


def test_cli_version(capsys):
    """Test pg-ecommerce --version outputs the correct version."""
    try:
        main(["--version"])
    except SystemExit as e:
        assert e.code == 0
    captured = capsys.readouterr()
    assert f"pg-ecommerce {__version__}" in captured.out


def test_cli_migrate(capsys):
    """Test pg-ecommerce migrate runs successfully in in-memory mode."""
    exit_code = main(["--in-memory", "migrate"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "[+] Successfully migrated!" in captured.out


def test_cli_verify(capsys):
    """Test pg-ecommerce verify returns valid JSON schema status."""
    exit_code = main(["--in-memory", "verify"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert '"is_valid": true' in captured.out
    assert '"customers"' in captured.out


def test_cli_info(capsys):
    """Test pg-ecommerce info outputs engine, tables, and views list."""
    exit_code = main(["--in-memory", "info"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Database Engine: SQLITE" in captured.out
    assert "Total Tables:" in captured.out
    assert "Total Views:" in captured.out


def test_cli_seed_curated(capsys):
    """Test pg-ecommerce seed in curated mode populates all tables."""
    exit_code = main(["--in-memory", "seed", "--mode", "curated"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "[+] Seeding complete! Populated row counts:" in captured.out
    assert "products" in captured.out
    assert "orders" in captured.out


def test_cli_seed_synthetic(capsys):
    """Test pg-ecommerce seed in synthetic mode with custom volumes."""
    exit_code = main(["--in-memory", "seed", "--mode", "synthetic", "--products", "15", "--customers", "10", "--orders", "20", "--seed", "777"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "[+] Seeding complete! Populated row counts:" in captured.out
    assert "products              : 15 rows" in captured.out
    assert "customers             : 10 rows" in captured.out
    assert "orders                : 20 rows" in captured.out


def test_cli_export_sql(capsys):
    """Test pg-ecommerce export-sql outputs SQL script."""
    exit_code = main(["export-sql"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "CREATE TABLE IF NOT EXISTS products" in captured.out
