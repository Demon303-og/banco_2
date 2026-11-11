import os
from contextlib import contextmanager
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import register_uuid

register_uuid()
_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = ThreadedConnectionPool(
            1, 10,
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "banco"),
            user=os.getenv("DB_USER", "banco"),
            password=os.getenv("DB_PASSWORD", "banco"),
        )
    return _pool


@contextmanager
def tx():
    """Transacción: commit si todo sale bien, rollback si hay error."""
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn, conn.cursor() as cur:
            yield cur
    finally:
        pool.putconn(conn)


def init_db():
    schema = os.path.join(os.path.dirname(__file__), "schema.sql")
    with tx() as cur:
        cur.execute(open(schema, encoding="utf-8").read())
