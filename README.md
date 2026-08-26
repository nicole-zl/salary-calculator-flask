# 千薪万苦 · 计算器 (Flask + SQLite 版)

单文件 HTML 版本的 Flask 重构版，新增用户注册登录功能，数据存储在服务器端 SQLite。

## 快速开始

```bash
# 1. 进入项目目录
cd salary-calculator-flask

# 2. (可选) 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动应用（首次启动会自动创建数据库）
python app.py

# 5. 浏览器打开
# http://127.0.0.1:5001
```

> ⚠️ 默认端口为 **5001**。macOS Monterey+ 的 AirPlay Receiver 会占用 5000 端口，访问会被拦截返回 403。
> 如需用 5000：系统设置 → 通用 → 隔空播放与接力的接收器 → 关闭，再把 `app.py` 末尾端口改回 5000。

## 功能特性

### 用户系统
- **注册**：用户名 ≥ 3 字符，密码 ≥ 6 字符
- **登录**：Flask session 持久化（30 天）
- **登出**：清空 session
- **密码安全**：Werkzeug pbkdf2 哈希

### 数据隔离
- 每个用户拥有独立的工资配置、实物列表、Tips
- 注册时自动初始化默认配置（月薪 10000，09:00-18:00，咖啡/奶茶/盒饭）
- 所有 API 需登录后才能访问，401 自动跳转登录页

### 计算器功能（保留单文件版全部功能）
- 实时倒计时、今日已赚、每分钟/每秒赚
- 实物换算（单选展示 + 需上班分钟高亮）
- 2026 中国法定节假日与调休识别
- 6 个统计卡片（发薪日、本月已赚、时薪等）
- 暗色模式切换（每用户独立持久化）
- 数字滚动动画

## 技术架构

| 层 | 技术 |
|---|---|
| 后端 | Flask 3.x + 原生 sqlite3（无 ORM） |
| 认证 | Flask session + Werkzeug 密码哈希 |
| 模板 | Jinja2（base/login/register/calculator） |
| 前端 | 原生 HTML/CSS/JS，fetch API 调用后端 |
| 存储 | SQLite 单文件，位于项目根目录 |

## 数据库 Schema

```sql
-- 用户表
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户配置表（1:1）
CREATE TABLE user_configs (
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

-- 实物表（1:N）
CREATE TABLE items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  price REAL NOT NULL,
  unit TEXT NOT NULL,
  selected INTEGER DEFAULT 0,
  sort_order INTEGER DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
```

## API 路由

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| GET | `/` | 计算器主页 | ✅ |
| GET/POST | `/login` | 登录 | - |
| GET/POST | `/register` | 注册 | - |
| GET | `/logout` | 登出 | - |
| GET | `/api/config` | 获取配置 | ✅ |
| POST | `/api/config` | 保存配置 | ✅ |
| GET | `/api/items` | 获取实物 | ✅ |
| POST | `/api/items` | 保存实物 | ✅ |
| POST | `/api/reset` | 重置当前用户数据 | ✅ |

## 项目结构

```
salary-calculator-flask/
├── app.py                # Flask 主应用（路由 + 认证）
├── config.py             # 配置（DB 路径、SECRET_KEY）
├── db.py                 # 数据库操作辅助
├── init_db.py            # 数据库初始化（建表）
├── requirements.txt      # Python 依赖
├── salary_calculator.db  # SQLite 数据库（运行时生成）
├── templates/
│   ├── base.html         # 基础模板
│   ├── login.html        # 登录页
│   ├── register.html     # 注册页
│   └── calculator.html   # 计算器主页
└── static/
    ├── css/style.css     # 主样式
    └── js/calculator.js  # 计算器前端逻辑
```

## 安全说明

- **开发模式**：`app.run(debug=True)`，仅本地使用
- **生产部署**：需修改 `config.py` 中的 `SECRET_KEY` 为环境变量，并使用 gunicorn/uwsgi 部署
- **HTTPS**：生产环境需配置 HTTPS，否则 session cookie 易被劫持
- **CSRF**：当前未启用 CSRF 保护，生产环境建议添加 Flask-WTF

## 与单文件版的差异

| 项目 | 单文件版 | Flask 版 |
|---|---|---|
| 启动方式 | 双击 HTML | `python app.py`（端口 5001） |
| 数据存储 | localStorage | SQLite |
| 用户系统 | 无 | 注册登录 |
| 多设备同步 | 无 | 支持（同账号登录即可） |
| 配置默认值 | 10000 | 10000 |
| 默认主题 | 白天 | 白天 |
| 文件数 | 1 | 10+ |
