"""数据库操作辅助函数 - 兼容 sqlite3 和 libsql-client"""
from init_db import get_db
from config import Config


def _row_to_dict(row, columns):
    """把一行数据转成 dict（兼容 sqlite3.Row 和 libsql ResultSet）"""
    if row is None:
        return None
    if hasattr(row, 'keys'):
        # sqlite3.Row 或类似 dict-like
        return {k: row[k] for k in columns}
    # libsql-client 返回 tuple
    return dict(zip(columns, row))


def _fetchone_dict(conn, sql, params, columns):
    """执行 SQL 并返回单行 dict"""
    if Config.USE_TURSO:
        rs = conn.execute(sql, params)
        rows = rs.rows
        if not rows:
            return None
        return _row_to_dict(rows[0], columns)
    else:
        row = conn.execute(sql, params).fetchone()
        return _row_to_dict(row, columns)


def _fetchall_dict(conn, sql, params, columns):
    """执行 SQL 并返回多行 dict 列表"""
    if Config.USE_TURSO:
        rs = conn.execute(sql, params)
        return [_row_to_dict(r, columns) for r in rs.rows]
    else:
        rows = conn.execute(sql, params).fetchall()
        return [_row_to_dict(r, columns) for r in rows]


def _close(conn):
    """关闭连接（libsql-client 不需要 close）"""
    if hasattr(conn, 'close'):
        conn.close()


def get_user_by_username(username):
    """根据用户名查询用户"""
    cols = ['id', 'username', 'password_hash', 'created_at']
    conn = get_db()
    try:
        return _fetchone_dict(conn, 'SELECT * FROM users WHERE username = ?', (username,), cols)
    finally:
        _close(conn)


def get_user_by_id(user_id):
    """根据 ID 查询用户"""
    cols = ['id', 'username', 'password_hash', 'created_at']
    conn = get_db()
    try:
        return _fetchone_dict(conn, 'SELECT * FROM users WHERE id = ?', (user_id,), cols)
    finally:
        _close(conn)


def create_user(username, password_hash):
    """创建新用户，并初始化默认配置和实物"""
    conn = get_db()
    try:
        if Config.USE_TURSO:
            # libsql-client：每条 execute 立即提交
            rs = conn.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, password_hash)
            )
            # libsql-client 的 last_insert_rowid
            user_id = rs.last_insert_rowid

            conn.execute('''
                INSERT INTO user_configs (user_id, salary, work_days_per_month, work_start, work_end,
                                          lunch_start, lunch_end, pay_day, theme, tips,
                                          settings_open, items_open)
                VALUES (?, 10000, '', '09:00', '18:00', '12:00', '13:00', 10, 'light',
                        '下班不是奖励，是边界。', 0, 0)
            ''', (user_id,))

            default_items = [
                ('咖啡', 25, '杯', 1, 0),
                ('奶茶', 18, '杯', 0, 1),
                ('盒饭', 30, '份', 0, 2),
            ]
            for name, price, unit, selected, sort_order in default_items:
                conn.execute('''
                    INSERT INTO items (user_id, name, price, unit, selected, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, name, price, unit, selected, sort_order))
            return user_id
        else:
            # sqlite3：用事务
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, password_hash)
            )
            user_id = cur.lastrowid

            cur.execute('''
                INSERT INTO user_configs (user_id, salary, work_days_per_month, work_start, work_end,
                                          lunch_start, lunch_end, pay_day, theme, tips,
                                          settings_open, items_open)
                VALUES (?, 10000, '', '09:00', '18:00', '12:00', '13:00', 10, 'light',
                        '下班不是奖励，是边界。', 0, 0)
            ''', (user_id,))

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
        if hasattr(conn, 'rollback'):
            conn.rollback()
        raise
    finally:
        _close(conn)


def get_user_config(user_id):
    """获取用户配置"""
    cols = ['id', 'user_id', 'salary', 'work_days_per_month', 'work_start', 'work_end',
            'lunch_start', 'lunch_end', 'pay_day', 'theme', 'tips',
            'settings_open', 'items_open']
    conn = get_db()
    try:
        return _fetchone_dict(conn, 'SELECT * FROM user_configs WHERE user_id = ?', (user_id,), cols)
    finally:
        _close(conn)


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
    try:
        conn.execute(f'UPDATE user_configs SET {set_clause} WHERE user_id = ?', params)
        if hasattr(conn, 'commit'):
            conn.commit()
    finally:
        _close(conn)


def get_user_items(user_id):
    """获取用户实物列表"""
    cols = ['id', 'name', 'price', 'unit', 'selected', 'sort_order']
    conn = get_db()
    try:
        return _fetchall_dict(
            conn,
            'SELECT id, name, price, unit, selected, sort_order FROM items WHERE user_id = ? ORDER BY sort_order, id',
            (user_id,),
            cols
        )
    finally:
        _close(conn)


def replace_user_items(user_id, items):
    """替换用户所有实物"""
    conn = get_db()
    try:
        if Config.USE_TURSO:
            # libsql-client：用 batch execute
            conn.execute('DELETE FROM items WHERE user_id = ?', (user_id,))
            for idx, it in enumerate(items):
                conn.execute('''
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
        else:
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
        _close(conn)


def reset_user_data(user_id):
    """重置当前用户的所有数据"""
    conn = get_db()
    try:
        if Config.USE_TURSO:
            conn.execute('DELETE FROM items WHERE user_id = ?', (user_id,))
            conn.execute('UPDATE user_configs SET salary=10000, work_days_per_month="", '
                         'work_start="09:00", work_end="18:00", lunch_start="12:00", '
                         'lunch_end="13:00", pay_day=10, theme="light", '
                         'tips="下班不是奖励，是边界。", settings_open=0, items_open=0 '
                         'WHERE user_id = ?', (user_id,))
            default_items = [
                ('咖啡', 25, '杯', 1, 0),
                ('奶茶', 18, '杯', 0, 1),
                ('盒饭', 30, '份', 0, 2),
            ]
            for name, price, unit, selected, sort_order in default_items:
                conn.execute('''
                    INSERT INTO items (user_id, name, price, unit, selected, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, name, price, unit, selected, sort_order))
        else:
            cur = conn.cursor()
            try:
                cur.execute('DELETE FROM items WHERE user_id = ?', (user_id,))
                cur.execute('UPDATE user_configs SET salary=10000, work_days_per_month="", '
                            'work_start="09:00", work_end="18:00", lunch_start="12:00", '
                            'lunch_end="13:00", pay_day=10, theme="light", '
                            'tips="下班不是奖励，是边界。", settings_open=0, items_open=0 '
                            'WHERE user_id = ?', (user_id,))
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
            except Exception:
                conn.rollback()
                raise
    finally:
        _close(conn)


# ============== 带薪离席 ==============
def add_paid_break(user_id, start_at, end_at, duration_seconds, earnings, note=''):
    """新增一条带薪离席记录"""
    conn = get_db()
    try:
        conn.execute('''
            INSERT INTO paid_breaks (user_id, start_at, end_at, duration_seconds, earnings, note)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, start_at, end_at, int(duration_seconds), float(earnings), note))
        if hasattr(conn, 'commit'):
            conn.commit()
    finally:
        _close(conn)


def get_user_breaks(user_id, limit=50):
    """获取用户带薪离席历史（按时间倒序）"""
    cols = ['id', 'start_at', 'end_at', 'duration_seconds', 'earnings', 'note', 'created_at']
    conn = get_db()
    try:
        return _fetchall_dict(
            conn,
            'SELECT id, start_at, end_at, duration_seconds, earnings, note, created_at '
            'FROM paid_breaks WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
            (user_id, limit),
            cols
        )
    finally:
        _close(conn)


def delete_paid_break(user_id, break_id):
    """删除一条带薪离席记录（带 user_id 校验）"""
    conn = get_db()
    try:
        conn.execute('DELETE FROM paid_breaks WHERE id = ? AND user_id = ?', (break_id, user_id))
        if hasattr(conn, 'commit'):
            conn.commit()
    finally:
        _close(conn)
