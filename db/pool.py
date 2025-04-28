from __future__ import annotations
import streamlit as st
from psycopg2.pool import SimpleConnectionPool

DB_CONFIG = {
    "dbname": st.secrets["POSTGRES_DB"],
    "user": st.secrets["POSTGRES_USER"],
    "password": st.secrets["POSTGRES_PASSWORD"],
    "host": st.secrets["POSTGRES_HOST"],
    "port": st.secrets["POSTGRES_PORT"],
    "sslmode": "require",
}


@st.cache_resource(show_spinner="🔌 Connecting to Postgres…")
def _pool():
    return SimpleConnectionPool(minconn=1, maxconn=5, **DB_CONFIG)


def get_conn():
    return _pool().getconn()


def put_conn(conn):
    _pool().putconn(conn)
