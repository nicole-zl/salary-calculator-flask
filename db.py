"""数据库操作辅助函数"""
from init_db import get_db

def get_user_by_username(username):
    """根据用户名查询用户"""
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    """根据 ID 查询用户"""
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def create_user(username, password_hash):
    """创建新用户，并初始化默认配置和实物"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )
        user_id = cur.lastrowid

        # 初始化默认配置
        cur.execute('''
            INSERT INTO user_configs (user_id, salary, work_days_per_month, work_start, work_end,
                                       lunch_start, lunch_end, pay_day, theme, tips,
                                       settings_open, items_open)
            VALUES (?, 10000, '', '09:00', '18:00', '12:00', '13:00', 10, 'light',
                    '下班不是奖励，是边界。', 0, 0)
        ''', (user_id,))

        # 初始化默认实物
        default_items = [
            ('咖啡', 25, '杯', 1, 0),
            ('奶茶', 18, '杯', 0, 1),
            ('盒饭', 30, '份', 0, 2),
        ]
        for name, price, unit, selected, sort_order in default_items:
            cur.execute('''
                INSERT INTO items (user_id, name, price, unit, selected, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, name, price, unit, selected, sort_order))

        conn.commit()
        return user_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_user_config(user_id):
    """获取用户配置"""
    conn = get_db()
    config = conn.execute('SELECT * FROM user_configs WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    return config

def update_user_config(user_id, **fields):
    """更新用户配置"""
    allowed = {'salary', 'work_days_per_month', 'work_start', 'work_end',
               'lunch_start', 'lunch_end', 'pay_day', 'theme', 'tips',
               'settings_open', 'items_open'}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    set_clause = ', '.join([f'{k} = ?' for k in updates])
    params = list(updates.values()) + [user_id]
    conn = get_db()
    conn.execute(f'UPDATE user_configs SET {set_clause} WHERE user_id = ?', params)
    conn.commit()
    conn.close()

def get_user_items(user_id):
    """获取用户实物列表"""
    conn = get_db()
    items = conn.execute(
        'SELECT id, name, price, unit, selected, sort_order FROM items WHERE user_id = ? ORDER BY sort_order, id',
        (user_id,)
    ).fetchall()
    conn.close()
    return items

def replace_user_items(user_id, items):
    """替换用户所有实物"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute('DELETE FROM items WHERE user_id = ?', (user_id,))
        for idx, it in enumerate(items):
            cur.execute('''
                INSERT INTO items (user_id, name, price, unit, selected, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                it.get('name', ''),
                float(it.get('price', 0)),
                it.get('unit', ''),
                1 if it.get('selected') else 0,
                idx
            ))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
