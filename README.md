# 千薪万苦 · 计算器 (Flask + SQLite/Turso)

单文件 HTML 版本的 Flask 重构版，新增用户注册登录功能，支持本地 SQLite 和 Vercel + Turso 云数据库部署。

## 本地运行

```bash
# 1. 进入项目目录
cd salary-calculator-flask

# 2. 创建虚拟环境（首次）
python3 -m venv venv

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 安装依赖（首次）
pip install -r requirements.txt

# 5. 启动应用
python app.py

# 6. 浏览器打开
# http://127.0.0.1:5001
```

**首次启动会自动创建 SQLite 数据库** `salary_calculator.db`。

> ⚠️ 默认端口为 **5001**。macOS Monterey+ 的 AirPlay Receiver 会占用 5000 端口。
> 如需用 5000：系统设置 → 通用 → 隔空播放与接力的接收器 → 关闭。

## 部署到 Vercel

### 步骤 1：创建 Turso 数据库

```bash
# 安装 Turso CLI（首次）
brew install tursodatabase/tap/turso
# 或: curl -sSfL https://get.tur.so/install.sh | bash

# 登录
turso auth login

# 创建数据库
turso db create salary-calculator

# 获取连接 URL
turso db show salary-calculator --url
# 输出形如: libsql://salary-calculator-xxx.turso.io

# 创建访问令牌
turso db tokens create salary-calculator
# 输出一长串 token

# 初始化表结构（用 Turso 的 SQL shell）
turso db shell salary-calculator < schema.sql
```

### 步骤 2：在 Vercel 配置环境变量

在 Vercel 项目设置 → Environment Variables 添加：

| Key | Value |
|---|---|
| `TURSO_URL` | `libsql://salary-calculator-xxx.turso.io` |
| `TURSO_TOKEN` | （上一步生成的 token） |
| `SECRET_KEY` | （随机字符串，建议用 `openssl rand -hex 32` 生成） |

### 步骤 3：部署

```bash
# 安装 Vercel CLI
npm i -g vercel

# 在项目目录
cd salary-calculator-flask
vercel
```

或直接 push 到 GitHub 让 Vercel 自动部署。

### 步骤 4：初始化 Turso 表

首次部署后，Vercel 冷启动会自动调用 `init_db()` 创建表（CREATE TABLE IF NOT EXISTS）。
也可以手动执行：

```bash
turso db shell salary-calculator < schema.sql
```

## 架构说明

### 双模式数据库

```
本地开发：sqlite3 → salary_calculator.db
Vercel 部署：libsql → Turso 云数据库
```

切换由 `TURSO_URL` 和 `TURSO_TOKEN` 环境变量自动控制，代码零改动。

### Vercel 部署架构

```
Vercel Edge
   ↓ (Python Serverless Function)
api/index.py
   ↓ (sys.path 加项目根目录)
app.py (Flask 应用)
   ↓ (init_db.get_db)
libsql_experimental → Turso 云数据库
```

### Vercel 入口说明

- `api/index.py`：Vercel Python Runtime 入口，暴露 `app` 对象
- `vercel.json`：路由配置，把所有请求转到 `api/index.py`
- `app.py` 中的 `if __name__ == '__main__'` 在 Vercel 不会执行

## 功能特性

### 用户系统
- **注册**：用户名 ≥ 3 字符，密码 ≥ 6 字符
- **登录**：Flask session 持久化（30 天）
- **登出**：清空 session
- **密码安全**：Werkzeug pbkdf2:sha256 哈希
- **唯一性校验**：数据库 `UNIQUE` 约束 + 代码查重双重保障

### 数据隔离
- 每用户独立的工资配置、实物列表、Tips、主题
- 注册时自动初始化默认配置（月薪 10000，09:00-18:00，咖啡/奶茶/盒饭）
- 所有 API 需登录后才能访问，401 自动跳转登录页
- 所有 SQL 查询都以 `user_id` 为过滤条件

### 计算器功能
- 实时倒计时、今日已赚、每分钟/每秒赚
- 实物换算（单选展示 + 需上班分钟高亮）
- 2026 中国法定节假日与调休识别
- 6 个统计卡片（发薪日、本月已赚、时薪等）
- 暗色模式切换（每用户独立持久化）
- 数字滚动动画、防抖保存（500ms）

## 技术架构

| 层 | 技术 |
|---|---|
| 后端 | Flask 3.x + libsql_experimental（无 ORM） |
| 认证 | Flask session + Werkzeug 密码哈希（pbkdf2:sha256） |
| 模板 | Jinja2（base/login/register/calculator） |
| 前端 | 原生 HTML/CSS/JS，fetch API 调用后端 |
| 本地存储 | SQLite 单文件 |
| 云端存储 | Turso（libSQL 云端 SQLite） |
| 部署 | Vercel Python Serverless |

## 数据库 Schema

### 表关系
```
users (1) ──── (1) user_configs    工资配置
       ──── (N) items              实物换算
```

### 表结构

**users**：用户表
| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 主键 |
| username | TEXT UNIQUE NOT NULL | 用户名（唯一） |
| password_hash | TEXT NOT NULL | 密码哈希 |
| created_at | TIMESTAMP | 注册时间 |

**user_configs**：用户配置表（1:1）
| 字段 | 默认值 | 说明 |
|---|---|---|
| user_id | - | 外键 |
| salary | 10000 | 税前月薪 |
| work_days_per_month | '' | 每月工作日 |
| work_start | '09:00' | 上班时间 |
| work_end | '18:00' | 下班时间 |
| lunch_start | '12:00' | 午休开始 |
| lunch_end | '13:00' | 午休结束 |
| pay_day | 10 | 每月发薪日 |
| theme | 'light' | 主题 |
| tips | '下班不是奖励，是边界。' | Tips 文本 |
| settings_open | 0 | 工资配置面板展开 |
| items_open | 0 | 实物面板展开 |

**items**：实物表（1:N）
| 字段 | 说明 |
|---|---|
| user_id | 外键 |
| name | 实物名称 |
| price | 单价 |
| unit | 单位 |
| selected | 是否选中展示 |
| sort_order | 排序 |

## API 路由

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| GET | `/` | 计算器主页 | ✅ |
| GET/POST | `/login` | 登录 | - |
| GET/POST | `/register` | 注册 | - |
| GET | `/logout` | 登出 | - |
| GET | `/api/config` | 获取配置 | ✅ |
| POST | `/api/config` | 保存配置 | ✅ |
| GET | `/api/items` | 获取实物列表 | ✅ |
| POST | `/api/items` | 保存实物列表 | ✅ |
| POST | `/api/reset` | 重置当前用户数据 | ✅ |

## 项目结构

```
salary-calculator-flask/
├── api/
│   └── index.py          # Vercel Serverless 入口
├── app.py                # Flask 主应用（路由 + 认证）
├── config.py             # 配置（Turso 环境变量、本地 DB）
├── db.py                 # 数据库操作辅助
├── init_db.py            # 数据库连接 + 初始化（libsql/sqlite3 双模式）
├── show_db.py            # 数据库查看脚本
├── vercel.json           # Vercel 部署配置
├── requirements.txt      # Python 依赖
├── salary_calculator.db  # SQLite 数据库（本地，运行时生成）
├── venv/                 # Python 虚拟环境（本地）
├── templates/
│   ├── base.html         # 基础模板
│   ├── login.html        # 登录页
│   ├── register.html     # 注册页
│   └── calculator.html   # 计算器主页
└── static/
    ├── css/style.css     # 主样式
    └── js/calculator.js  # 计算器前端逻辑
```

## 数据库查看

### 本地（SQLite）
```bash
cd salary-calculator-flask
source venv/bin/activate
python show_db.py
```

### Turso
```bash
turso db shell salary-calculator
sqlite> .tables
sqlite> SELECT * FROM users;
sqlite> SELECT * FROM user_configs;
sqlite> SELECT * FROM items;
sqlite> .quit
```

## 计算规则

```
每分钟收入 = 月薪 ÷ (每月工作日 × 每日工作分钟数)
每日工作分钟数 = (下班时间 - 上班时间) - (午休结束 - 午休开始)
今日已赚 = 每分钟收入 × 今日已工作分钟数
今日收入 = 每分钟收入 × 每日工作分钟数
再坚持赚 = 今日收入 - 今日已赚
实物可买 = 今日已赚 ÷ 实物单价
需上班分钟 = 实物单价 ÷ 每分钟收入
```

## 安全说明

- **密码哈希**：pbkdf2:sha256（避开 macOS Python 3.9 的 hashlib.scrypt 不可用问题）
- **生产部署**：
  - 已支持环境变量配置 `SECRET_KEY` / `TURSO_URL` / `TURSO_TOKEN`
  - Vercel 自动启用 HTTPS
  - 建议添加 Flask-WTF 的 CSRF 保护
  - 建议对 `/register` 加 rate limiting

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| 1.0 | 2026-08-24 | 单文件 HTML 版完整功能 |
| 2.0 | 2026-08-26 | 重构为 Flask + SQLite，新增注册登录、数据隔离、API |
| 2.1 | 2026-08-26 | 修复 hashlib.scrypt 不可用问题（改用 pbkdf2:sha256） |
| 2.2 | 2026-08-26 | 吞掉 Trae IDE Vite 客户端轮询请求 |
| 2.3 | 2026-08-26 | 端口改为 5001（避开 macOS AirPlay Receiver 占用 5000） |
| 3.0 | 2026-08-26 | 支持 Vercel 部署：libsql + Turso 云数据库 |
