from __future__ import annotations
import psycopg2.pool
import functools
import streamlit as st

DB_CONFIG = {
    "dbname": st.secrets["POSTGRES_DB"],
    "user": st.secrets["POSTGRES_USER"],
    "password": st.secrets["POSTGRES_PASSWORD"],
    "host": st.secrets["POSTGRES_HOST"],
    "port": st.secrets["POSTGRES_PORT"],
    "sslmode": "require",
}


@functools.lru_cache(maxsize=1)
def _pool():
    return psycopg2.pool.SimpleConnectionPool(minconn=1, maxconn=5, **DB_CONFIG)


def get_conn():
    return _pool().getconn()


def put_conn(conn):
    _pool().putconn(conn)
