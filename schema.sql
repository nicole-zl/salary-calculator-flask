-- 千薪万苦 · 计算器 - Turso 数据库 schema
-- 用于: turso db shell salary-calculator < schema.sql

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户配置表（1:1）
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
);

-- 实物换算表（1:N）
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    unit TEXT NOT NULL,
    selected INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
