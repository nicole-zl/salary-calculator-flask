"""数据库初始化与连接 - 同时支持本地 SQLite 和 Turso 云数据库"""
import sqlite3
import libsql_client
from config import Config


def get_db():
    """获取数据库连接

    - 配置了 Turso 环境变量时：连接 Turso 云数据库（同步接口）
    - 本地开发：使用 SQLite 文件
    """
    if Config.USE_TURSO:
        # Turso 云数据库 - 用 libsql-client 的同步接口
        # 注意：URL 必须是 https:// 开头（不能用 libsql://）
        url = Config.TURSO_URL
        if url.startswith('libsql://'):
            url = 'https://' + url[len('libsql://'):]
        client = libsql_client.create_client_sync(
            url,
            auth_token=Config.TURSO_TOKEN,
        )
        return client
    else:
        # 本地 SQLite
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def init_db():
    """初始化数据库表结构"""
    conn = get_db()
    statements = [
        '''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS user_configs (
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
        )''',
        '''CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            unit TEXT NOT NULL,
            selected INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )''',
        '''CREATE TABLE IF NOT EXISTS paid_breaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            start_at TIMESTAMP NOT NULL,
            end_at TIMESTAMP NOT NULL,
            duration_seconds INTEGER NOT NULL,
            earnings REAL NOT NULL,
            note TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )''',
    ]
    for sql in statements:
        conn.execute(sql)
    if hasattr(conn, 'commit'):
        conn.commit()
        conn.close()
    else:
        # libsql-client 没有 commit/close，execute 是立即提交
        pass
    print(f'数据库已初始化: {"Turso" if Config.USE_TURSO else Config.DB_PATH}')


if __name__ == '__main__':
    init_db()
