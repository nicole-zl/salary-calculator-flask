"""配置文件"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    # SQLite 数据库路径
    DB_PATH = os.path.join(BASE_DIR, 'salary_calculator.db')
    # Flask Session 密钥（生产环境请改为环境变量或随机生成）
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me-in-production')
    # Session 有效期（30 天）
    PERMANENT_SESSION_LIFETIME = 30 * 24 * 60 * 60
