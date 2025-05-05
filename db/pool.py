from __future__ import annotations
from psycopg2.pool import SimpleConnectionPool
import streamlit as st

# ------------------------------------------------------------------------
# 1️⃣  Configuration pulled from st.secrets (works both local & Cloud)
# ------------------------------------------------------------------------
DB_CONFIG = {
    "dbname": st.secrets["POSTGRES_DB"],
    "user": st.secrets["POSTGRES_USER"],
    "password": st.secrets["POSTGRES_PASSWORD"],
    "host": st.secrets["POSTGRES_HOST"],
    "port": st.secrets["POSTGRES_PORT"],
    "sslmode": "require",
}

# ------------------------------------------------------------------------
# 2️⃣  One global pool shared by the whole process (thread-safe in psycopg2)
# ------------------------------------------------------------------------
_POOL: SimpleConnectionPool | None = None


def _get_pool() -> SimpleConnectionPool:
    global _POOL
    if _POOL is None:
        _POOL = SimpleConnectionPool(minconn=1, maxconn=5, **DB_CONFIG)
    return _POOL


def get_conn():
    """Borrow a connection from the pool."""
    return _get_pool().getconn()


def put_conn(conn):
    """Return a connection to the pool."""
    _get_pool().putconn(conn)
