# 千薪万苦 · 计算器 (Flask + SQLite 版)

> 单文件 HTML 版本的重构版，新增用户注册登录功能，数据存储在服务器端 SQLite，支持多设备同步。

## 快速运行

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

> ⚠️ **端口说明**：默认端口为 **5001**（不是 5000）。
> macOS Monterey+ 默认开启的 AirPlay Receiver 会占用 5000 端口，访问会被拦截并返回 403。
> 如果坚持使用 5000 端口：系统设置 → 通用 → 隔空播放与接力的接收器 → 关闭。

### 后续启动

```bash
cd salary-calculator-flask
source venv/bin/activate
python app.py
```

### 停止应用
在运行终端按 `Ctrl + C`。

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

### 计算器功能（保留单文件版全部功能）
- 实时倒计时（HH:MM:SS）+ 工作进度条
- 今日已赚、再坚持赚、今日收入、每分钟/每秒赚
- 实物换算（单选展示 + 需上班分钟高亮）
- 2026 中国法定节假日与调休识别
- 6 个统计卡片（发薪日、本月已赚、时薪等）
- 暗色模式切换（每用户独立持久化）
- 数字滚动动画（requestAnimationFrame）
- 防抖保存（500ms 避免频繁请求）

## 技术架构

| 层 | 技术 |
|---|---|
| 后端 | Flask 3.x + 原生 sqlite3（无 ORM） |
| 认证 | Flask session + Werkzeug 密码哈希（pbkdf2:sha256） |
| 模板 | Jinja2（base/login/register/calculator） |
| 前端 | 原生 HTML/CSS/JS，fetch API 调用后端 |
| 存储 | SQLite 单文件，位于项目根目录 |

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
| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| user_id | INTEGER | - | 外键 |
| salary | REAL | 10000 | 税前月薪 |
| work_days_per_month | TEXT | '' | 每月工作日 |
| work_start | TEXT | '09:00' | 上班时间 |
| work_end | TEXT | '18:00' | 下班时间 |
| lunch_start | TEXT | '12:00' | 午休开始 |
| lunch_end | TEXT | '13:00' | 午休结束 |
| pay_day | INTEGER | 10 | 每月发薪日 |
| theme | TEXT | 'light' | 主题 |
| tips | TEXT | '下班不是奖励，是边界。' | Tips 文本 |
| settings_open | INTEGER | 0 | 工资配置面板展开 |
| items_open | INTEGER | 0 | 实物面板展开 |

**items**：实物表（1:N）
| 字段 | 类型 | 说明 |
|---|---|---|
| user_id | INTEGER | 外键 |
| name | TEXT | 实物名称 |
| price | REAL | 单价 |
| unit | TEXT | 单位 |
| selected | INTEGER | 是否选中展示 |
| sort_order | INTEGER | 排序 |

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
├── app.py                # Flask 主应用（路由 + 认证）
├── config.py             # 配置（DB 路径、SECRET_KEY）
├── db.py                 # 数据库操作辅助
├── init_db.py            # 数据库初始化（建表）
├── show_db.py            # 数据库查看脚本
├── requirements.txt      # Python 依赖
├── salary_calculator.db  # SQLite 数据库（运行时生成）
├── venv/                 # Python 虚拟环境（运行时生成）
├── templates/
│   ├── base.html         # 基础模板
│   ├── login.html        # 登录页
│   ├── register.html     # 注册页
│   └── calculator.html   # 计算器主页
└── static/
    ├── css/style.css     # 主样式
    └── js/calculator.js  # 计算器前端逻辑
```

## 数据库查看方法

### 方式 1：Python 脚本（推荐）
```bash
cd salary-calculator-flask
source venv/bin/activate
python show_db.py
```
显示所有表结构 + 表数据。

### 方式 2：sqlite3 命令行
```bash
sqlite3 salary_calculator.db
sqlite> .tables
sqlite> SELECT * FROM users;
sqlite> SELECT * FROM user_configs;
sqlite> SELECT * FROM items;
sqlite> .quit
```

### 方式 3：图形工具
- DB Browser for SQLite
- VS Code 插件：SQLite Viewer

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

- **开发模式**：`app.run(debug=True)`，仅本地使用
- **密码哈希**：使用 pbkdf2:sha256（避开当前 Python 环境 hashlib.scrypt 不可用的问题）
- **生产部署**：
  - 修改 `config.py` 中的 `SECRET_KEY` 为环境变量
  - 关闭 debug 模式
  - 使用 gunicorn/uwsgi 部署
  - 配置 HTTPS
  - 添加 Flask-WTF 的 CSRF 保护
  - 对 `/register` 接口加 rate limiting

## 与单文件版的对比

| 项目 | 单文件 HTML 版 | Flask 版 |
|---|---|---|
| 启动方式 | 双击 HTML | `python app.py` |
| 数据存储 | localStorage | SQLite |
| 用户系统 | 无 | 注册登录 |
| 多设备同步 | 无 | 支持（同账号登录即可） |
| 配置默认值 | 10000 | 10000 |
| 默认主题 | 白天 | 白天 |
| 文件数 | 1 | 10+ |

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| 1.0 | 2026-08-24 | 单文件 HTML 版完整功能 |
| 2.0 | 2026-08-26 | 重构为 Flask + SQLite，新增注册登录、数据隔离、API |
| 2.1 | 2026-08-26 | 修复 hashlib.scrypt 不可用问题（改用 pbkdf2:sha256） |
| 2.2 | 2026-08-26 | 吞掉 Trae IDE Vite 客户端轮询请求 |
| 2.3 | 2026-08-26 | 端口改为 5001（避开 macOS AirPlay Receiver 占用 5000） |
