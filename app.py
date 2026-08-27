"""千薪万苦 · 计算器 - Flask 主应用"""
import os
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from init_db import get_db, init_db
import db

app = Flask(__name__)
app.config.from_object(Config)

# 启动时确保数据库已初始化（Vercel 每次冷启动也会执行，CREATE TABLE IF NOT EXISTS 是幂等的）
try:
    init_db()
except Exception as e:
    print(f'init_db warning: {e}')


# ============== 吞掉 Trae IDE Vite 客户端轮询（避免日志噪音） ==============
@app.route('/@vite/client')
def vite_client():
    return '', 204


# ============== 认证装饰器 ==============
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            # API 调用返回 401，页面跳转登录
            if request.path.startswith('/api/'):
                return jsonify({'error': '未登录'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ============== 页面路由 ==============
@app.route('/')
@login_required
def index():
    """计算器主页"""
    user = db.get_user_by_id(session['user_id'])
    return render_template('calculator.html', username=user['username'])


@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('login.html')
        user = db.get_user_by_username(username)
        if not user or not check_password_hash(user['password_hash'], password):
            flash('用户名或密码错误', 'error')
            return render_template('login.html')
        session.permanent = True
        session['user_id'] = user['id']
        session['username'] = user['username']
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册页"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('register.html')
        if len(username) < 3:
            flash('用户名至少 3 个字符', 'error')
            return render_template('register.html')
        if len(password) < 6:
            flash('密码至少 6 个字符', 'error')
            return render_template('register.html')
        if db.get_user_by_username(username):
            flash('用户名已存在', 'error')
            return render_template('register.html')
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        db.create_user(username, password_hash)
        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    """登出"""
    session.clear()
    return redirect(url_for('login'))


# ============== API 路由 ==============
@app.route('/api/config')
@login_required
def api_get_config():
    """获取当前用户配置"""
    config = db.get_user_config(session['user_id'])
    if not config:
        return jsonify({'error': '配置不存在'}), 404
    return jsonify({
        'salary': config['salary'],
        'workDaysPerMonth': config['work_days_per_month'],
        'workStart': config['work_start'],
        'workEnd': config['work_end'],
        'lunchStart': config['lunch_start'],
        'lunchEnd': config['lunch_end'],
        'payDay': config['pay_day'],
        'theme': config['theme'],
        'tips': config['tips'],
        'settingsOpen': bool(config['settings_open']),
        'itemsOpen': bool(config['items_open']),
    })


@app.route('/api/config', methods=['POST'])
@login_required
def api_save_config():
    """保存当前用户配置"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '无效数据'}), 400
    db.update_user_config(session['user_id'],
        salary=float(data.get('salary', 10000)),
        work_days_per_month=data.get('workDaysPerMonth', ''),
        work_start=data.get('workStart', '09:00'),
        work_end=data.get('workEnd', '18:00'),
        lunch_start=data.get('lunchStart', '12:00'),
        lunch_end=data.get('lunchEnd', '13:00'),
        pay_day=int(data.get('payDay', 10)),
        theme=data.get('theme', 'light'),
        tips=data.get('tips', '下班不是奖励，是边界。'),
        settings_open=1 if data.get('settingsOpen') else 0,
        items_open=1 if data.get('itemsOpen') else 0,
    )
    return jsonify({'ok': True})


@app.route('/api/items')
@login_required
def api_get_items():
    """获取当前用户实物列表"""
    rows = db.get_user_items(session['user_id'])
    return jsonify([{
        'name': r['name'],
        'price': r['price'],
        'unit': r['unit'],
        'selected': bool(r['selected']),
    } for r in rows])


@app.route('/api/items', methods=['POST'])
@login_required
def api_save_items():
    """保存当前用户实物列表"""
    items = request.get_json()
    if not isinstance(items, list):
        return jsonify({'error': '无效数据'}), 400
    db.replace_user_items(session['user_id'], items)
    return jsonify({'ok': True})


@app.route('/api/reset', methods=['POST'])
@login_required
def api_reset():
    """重置当前用户所有数据"""
    uid = session['user_id']
    conn = get_db()
    try:
        conn.execute('DELETE FROM items WHERE user_id = ?', (uid,))
        conn.execute('''
            UPDATE user_configs SET salary=10000, work_days_per_month='',
            work_start='09:00', work_end='18:00', lunch_start='12:00',
            lunch_end='13:00', pay_day=10, theme='light',
            tips='下班不是奖励，是边界。',
            settings_open=0, items_open=0 WHERE user_id = ?
        ''', (uid,))
        # 重置默认实物
        default_items = [
            ('咖啡', 25, '杯', 1, 0),
            ('奶茶', 18, '杯', 0, 1),
            ('盒饭', 30, '份', 0, 2),
        ]
        for name, price, unit, selected, sort_order in default_items:
            conn.execute('''
                INSERT INTO items (user_id, name, price, unit, selected, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (uid, name, price, unit, selected, sort_order))
        conn.commit()
    except Exception:
        conn.rollback()
        return jsonify({'error': '重置失败'}), 500
    finally:
        conn.close()
    return jsonify({'ok': True})


# ============== 带薪离席 API ==============
@app.route('/api/breaks')
@login_required
def api_get_breaks():
    """获取当前用户带薪离席历史"""
    rows = db.get_user_breaks(session['user_id'], limit=50)
    return jsonify([{
        'id': r['id'],
        'startAt': r['start_at'],
        'endAt': r['end_at'],
        'durationSeconds': r['duration_seconds'],
        'earnings': r['earnings'],
        'note': r['note'],
        'createdAt': r['created_at'],
    } for r in rows])


@app.route('/api/breaks', methods=['POST'])
@login_required
def api_add_break():
    """新增一条带薪离席记录"""
    data = request.get_json() or {}
    start_at = data.get('startAt')
    end_at = data.get('endAt')
    duration = data.get('durationSeconds')
    earnings = data.get('earnings')
    note = data.get('note', '')
    if not start_at or not end_at or duration is None or earnings is None:
        return jsonify({'error': '参数缺失'}), 400
    try:
        db.add_paid_break(
            session['user_id'], start_at, end_at,
            int(duration), float(earnings), note
        )
    except Exception as e:
        return jsonify({'error': f'保存失败: {e}'}), 500
    return jsonify({'ok': True})


@app.route('/api/breaks/<int:break_id>', methods=['DELETE'])
@login_required
def api_delete_break(break_id):
    """删除一条带薪离席记录"""
    db.delete_paid_break(session['user_id'], break_id)
    return jsonify({'ok': True})


if __name__ == '__main__':
    # 本地开发模式启动（Vercel 上不会执行此分支，由 api/index.py 暴露 app）
    # 端口 5000 被 macOS AirPlay Receiver 占用，改用 5001
    app.run(host='127.0.0.1', port=5001, debug=True)
