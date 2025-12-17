import psycopg2.pool
from core.tools.config import config
import logging

logger = logging.getLogger(__name__)

class Database:
    _pool = None

    @classmethod
    def initialize(cls):
        if cls._pool is None:
            logger.info(f"Initializing DB Pool (Min: {config.DB_POOL_MIN}, Max: {config.DB_POOL_MAX})")
            cls._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=config.DB_POOL_MIN,
                maxconn=config.DB_POOL_MAX,
                dbname=config.DB_NAME,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                host=config.DB_HOST,
                port=config.DB_PORT
            )

    @classmethod
    def get_connection(cls):
        if cls._pool:
            return cls._pool.getconn()
        raise Exception("Database pool not initialized")

    @classmethod
    def return_connection(cls, conn):
        if cls._pool and conn:
            cls._pool.putconn(conn)

    @classmethod
    def close_all(cls):
        if cls._pool:
            logger.info("Closing DB Pool")
            cls._pool.closeall()
            cls._pool = None
