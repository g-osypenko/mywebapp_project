import argparse
import sys
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
import mariadb

from mywebapp.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MyWebApp: Simple Inventory API")
    parser.add_argument("--port", type=int, default=8080, help="Порт застосунку")
    parser.add_argument("--db-host", type=str, default="127.0.0.1", help="Хост MariaDB")
    parser.add_argument("--db-port", type=int, default=3306, help="Порт MariaDB")
    parser.add_argument("--db-user", type=str, default="mywebapp", help="Користувач БД")
    parser.add_argument("--db-pass", type=str, default="password", help="Пароль БД")
    parser.add_argument("--db-name", type=str, default="mywebapp_db", help="Назва БД")
    return parser.parse_args()


args = parse_args()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        pool = mariadb.ConnectionPool(
            pool_name="webapp_pool",
            pool_size=5,
            host=args.db_host,
            port=args.db_port,
            user=args.db_user,
            password=args.db_pass,
            database=args.db_name
        )
        app.state.db_pool = pool
        logger.info("Connection pool with MariaDB established.")
        yield
    except mariadb.Error as e:
        logger.error(f"Failed to connect to MariaDB: {e}")
        sys.exit(1)
    finally:
        logger.info("Lifespan ended. Connection pool gracefully handled by OS/interpreter exit.")


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
app.include_router(router)


def run() -> None:
    logger.info(f"Starting server on port {args.port}...")
    uvicorn.run(app, host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    run()