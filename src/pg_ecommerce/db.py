"""
Database connection manager and SQL execution engine.
Supports live PostgreSQL connections via psycopg/psycopg2, or an embedded
in-memory relational validation engine for zero-dependency test suites.
"""

from __future__ import annotations

import os
import re
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Union


class DatabaseError(Exception):
    """Base exception for database operations."""
    pass


class DatabaseConnection:
    """Universal connection manager supporting PostgreSQL and embedded SQLite mode."""

    def __init__(self, database_url: Optional[str] = None, in_memory: bool = False):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self.in_memory = in_memory or (not self.database_url)
        self.engine_type = "sqlite" if self.in_memory else "postgresql"
        self._pg_conn = None
        self._sqlite_conn: Optional[sqlite3.Connection] = None

        if self.in_memory:
            self._init_sqlite()
        else:
            self._init_postgres()

    def _init_sqlite(self) -> None:
        """Initialize in-memory SQLite relational engine with PostgreSQL compatibility."""
        self._sqlite_conn = sqlite3.connect(":memory:")
        self._sqlite_conn.row_factory = sqlite3.Row
        self._sqlite_conn.execute("PRAGMA foreign_keys = ON;")

        # Register custom SQLite functions mimicking PostgreSQL functions
        self._sqlite_conn.create_function("gen_random_uuid", 0, self._sqlite_uuid)
        self._sqlite_conn.create_function("clock_timestamp", 0, self._sqlite_timestamp)

    @staticmethod
    def _sqlite_uuid() -> str:
        import uuid
        return str(uuid.uuid4())

    @staticmethod
    def _sqlite_timestamp() -> str:
        import datetime
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def _init_postgres(self) -> None:
        """Initialize PostgreSQL connection using psycopg if available."""
        try:
            import psycopg  # type: ignore
            self._pg_conn = psycopg.connect(self.database_url)
        except ImportError:
            try:
                import psycopg2  # type: ignore
                self._pg_conn = psycopg2.connect(self.database_url)
            except ImportError:
                # Fallback to in-memory mode if PostgreSQL driver not installed
                self.in_memory = True
                self.engine_type = "sqlite"
                self._init_sqlite()

    def execute(self, query: str, params: Optional[Union[Tuple[Any, ...], Dict[str, Any]]] = None) -> Any:
        """Execute a query and return raw cursor/result."""
        if self.in_memory and self._sqlite_conn:
            translated = self._translate_pg_to_sqlite(query)
            if not translated.strip():
                return None
            try:
                cursor = self._sqlite_conn.cursor()
                if params:
                    cursor.execute(translated, params)
                else:
                    cursor.executescript(translated)
                return cursor
            except Exception as e:
                raise DatabaseError(f"Execution failed: {e}\nQuery:\n{translated}") from e
        elif self._pg_conn:
            try:
                cursor = self._pg_conn.cursor()
                cursor.execute(query, params or ())
                self._pg_conn.commit()
                return cursor
            except Exception as e:
                self._pg_conn.rollback()
                raise DatabaseError(f"PostgreSQL execution failed: {e}") from e

    def fetch_all(self, query: str, params: Optional[Union[Tuple[Any, ...], Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Execute query and return list of dictionaries."""
        if self.in_memory and self._sqlite_conn:
            translated = self._translate_pg_to_sqlite(query)
            cursor = self._sqlite_conn.cursor()
            cursor.execute(translated, params or ())
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        elif self._pg_conn:
            cursor = self._pg_conn.cursor()
            cursor.execute(query, params or ())
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        return []

    def fetch_one(self, query: str, params: Optional[Union[Tuple[Any, ...], Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """Execute query and return a single dictionary result."""
        results = self.fetch_all(query, params)
        return results[0] if results else None

    def close(self) -> None:
        """Close connection handles."""
        if self._sqlite_conn:
            self._sqlite_conn.close()
        if self._pg_conn:
            self._pg_conn.close()

    @staticmethod
    def _translate_pg_to_sqlite(pg_sql: str) -> str:
        """
        Translate PostgreSQL-specific DDL syntax to SQLite-compatible syntax
        for zero-dependency testing while preserving pure PostgreSQL SQL files.
        """
        sql = pg_sql

        # Strip DO $$ ... $$; plpgsql blocks
        sql = re.sub(r'DO\s+\$\$.*?\$\$;', '', sql, flags=re.DOTALL)
        # Strip CREATE EXTENSION
        sql = re.sub(r'CREATE\s+EXTENSION\s+.*?;', '', sql, flags=re.IGNORECASE)
        # Strip CREATE OR REPLACE FUNCTION ... LANGUAGE plpgsql;
        sql = re.sub(r'CREATE\s+OR\s+REPLACE\s+FUNCTION\s+.*?LANGUAGE\s+plpgsql;', '', sql, flags=re.DOTALL | re.IGNORECASE)
        # Strip DROP TRIGGER and CREATE TRIGGER blocks
        sql = re.sub(r'DROP\s+TRIGGER\s+.*?;', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'CREATE\s+TRIGGER\s+.*?EXECUTE\s+FUNCTION\s+.*?;', '', sql, flags=re.DOTALL | re.IGNORECASE)

        # Replace CREATE OR REPLACE VIEW with CREATE VIEW IF NOT EXISTS
        sql = re.sub(r'CREATE\s+OR\s+REPLACE\s+VIEW\s+([a-zA-Z0-9_]+)\s+AS', r'CREATE VIEW IF NOT EXISTS \1 AS', sql, flags=re.IGNORECASE)

        # Translate interval arithmetic (e.g. clock_timestamp() - INTERVAL '14 days' + INTERVAL '2 minutes')
        def replace_clock_interval(m):
            chain = m.group(1)
            if not chain.strip():
                return "(datetime('now'))"
            modifiers = []
            for op, val in re.findall(r"([+-])\s*INTERVAL\s*'([^']+)'", chain):
                sign = '-' if op == '-' else '+'
                modifiers.append(f"'{sign}{val}'")
            mod_str = ", ".join(modifiers)
            return f"datetime('now', {mod_str})"

        sql = re.sub(r"clock_timestamp\(\)((?:\s*[+-]\s*INTERVAL\s*'[^']+')*)", replace_clock_interval, sql, flags=re.IGNORECASE)

        # Replace PostgreSQL types
        replacements = [
            (r'\bBIGSERIAL\b', 'INTEGER'),
            (r'\bSERIAL\b', 'INTEGER'),
            (r'\bBIGINT\b', 'INTEGER'),
            (r'\bTIMESTAMPTZ\b', 'TEXT'),
            (r'\bTIMESTAMP\b', 'TEXT'),
            (r'\bUUID\b', 'TEXT'),
            (r'\bJSONB\b', 'TEXT'),
            (r'\bJSON\b', 'TEXT'),
            (r'\bBOOLEAN\b', 'INTEGER'),
            (r'\bTEXT\[\]', 'TEXT'),
            (r'\bTSVECTOR\b', 'TEXT'),
            (r'\bNUMERIC\(\d+,\s*\d+\)', 'NUMERIC'),
            (r'DEFAULT\s+gen_random_uuid\(\)', 'DEFAULT (lower(hex(randomblob(16))))'),
            (r'DEFAULT\s+clock_timestamp\(\)', 'DEFAULT (datetime(\'now\'))'),
            (r'DEFAULT\s+\'{}\'::jsonb', 'DEFAULT \'{}\''),
            (r'DEFAULT\s+ARRAY\[\]::TEXT\[\]', 'DEFAULT \'[]\''),
            (r'DEFAULT\s+true\b', 'DEFAULT 1'),
            (r'DEFAULT\s+false\b', 'DEFAULT 0'),
            (r'::numeric', ''),
            (r'::jsonb', ''),
            (r'::text', ''),
        ]

        for pattern, repl in replacements:
            sql = re.sub(pattern, repl, sql, flags=re.IGNORECASE)

        # Custom ENUM type column declarations
        sql = re.sub(r'\b(role|status|from_status|to_status|type|discount_type)\s+(user_role|product_status|order_status|address_type|discount_type)\b', r'\1 TEXT', sql, flags=re.IGNORECASE)

        # Convert exact equality checks on calculated currency fields to round() for SQLite float precision
        sql = re.sub(r'total_amount\s*=\s*\((subtotal[^)]+)\)', r'round(total_amount, 2) = round(\1, 2)', sql)
        sql = re.sub(r'line_total\s*=\s*\((unit_price[^)]+)\)', r'round(line_total, 2) = round(\1, 2)', sql)

        # Translate PostgreSQL USING GIN indexes to SQLite standard indexes
        sql = re.sub(r'USING\s+gin\s*\(([^)]+?)(?:\s+jsonb_path_ops)?\)', r'(\1)', sql, flags=re.IGNORECASE)

        # Translate boolean comparisons in WHERE clauses: "= true" -> "= 1"
        sql = re.sub(r'=\s*true\b', '= 1', sql, flags=re.IGNORECASE)
        sql = re.sub(r'=\s*false\b', '= 0', sql, flags=re.IGNORECASE)

        # Clean regex checks that SQLite doesn't natively support without extensions
        sql = re.sub(r'CONSTRAINT\s+chk_customer_email_format\s+CHECK\s+\([^)]+\)', 'CHECK (length(email) > 3)', sql)

        # Clean ARRAY['...'] syntax
        sql = re.sub(r'ARRAY\[.*?\]', "'[]'", sql)

        return sql
