"""配置文件 - 同时支持本地 SQLite 和 Turso 云数据库"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # === 数据库配置 ===
    # 优先级：TURSO_URL + TURSO_TOKEN > 本地 SQLite
    # Vercel 部署用 Turso，本地开发用 SQLite
    TURSO_URL = os.environ.get('TURSO_URL', '')          # 如 libsql://xxx.turso.io
    TURSO_TOKEN = os.environ.get('TURSO_TOKEN', '')      # Turso 访问令牌
    DB_PATH = os.path.join(BASE_DIR, 'salary_calculator.db')

    # 是否使用 Turso
    USE_TURSO = bool(TURSO_URL and TURSO_TOKEN)

    # === Flask Session ===
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32))
    PERMANENT_SESSION_LIFETIME = 30 * 24 * 60 * 60

    # === Vercel 环境 ===
    IS_VERCEL = os.environ.get('VERCEL', '0') == '1'
