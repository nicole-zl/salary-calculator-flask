"""数据库初始化脚本 - 创建表结构"""
import sqlite3
import os
from config import Config

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库表结构"""
    conn = get_db()
    cur = conn.cursor()

    # 用户表
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 用户配置表（工资配置）
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            salary REAL DEFAULT 10000,
            work_days_per_month TEXT DEFAULT '',
            work_start TEXT DEFAULT '09:00',
            work_end TEXT DEFAULT '18:00',
            lunch_start TEXT DEFAULT '12:00',
            lunch_end TEXT DEFAULT '13:00',
            pay_day INTEGER DEFAULT 10,
            theme TEXT DEFAULT 'light',
            tips TEXT DEFAULT '下班不是奖励，是边界。',
            settings_open INTEGER DEFAULT 0,
            items_open INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE (user_id)
        )
    ''')

    # 实物换算表
    cur.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            unit TEXT NOT NULL,
            selected INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()
    print(f'数据库已初始化: {Config.DB_PATH}')

if __name__ == '__main__':
    init_db()
