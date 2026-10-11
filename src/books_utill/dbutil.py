"""Backward-compatible alias: use PostgresDb instead of the old psycopg2 pool."""

from books_utill.postgres_db import PostgresDb

DbUtil = PostgresDb
