import os

class Config:
    DB_NAME = os.getenv("DB_NAME", "odoo_fastapi")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    MODULES_PATH = os.getenv("MODULES_PATH", "modules")
    DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", 5))
    DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", 20))

config = Config()
