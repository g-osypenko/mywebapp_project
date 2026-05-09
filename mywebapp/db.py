import mariadb
from typing import Generator
from fastapi import Request


def get_db_connection(request: Request) -> Generator[mariadb.Connection, None, None]:
    pool: mariadb.ConnectionPool = request.app.state.db_pool
    conn = pool.get_connection()
    try:
        yield conn
    finally:
        conn.close()