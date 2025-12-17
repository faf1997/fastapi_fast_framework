import os

class Config:
    DB_NAME = os.getenv("DB_NAME", "odoo_fastapi")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    MODULES_PATH = os.getenv("MODULES_PATH", "modules")

config = Config()
