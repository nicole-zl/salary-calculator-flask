"""数据库查看脚本 - 显示所有表结构和数据"""
import sqlite3
from config import Config

def show_schema(conn):
    """显示所有表结构"""
    print('\n' + '=' * 60)
    print('表结构')
    print('=' * 60)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    for (table_name,) in tables:
        print(f'\n■ 表: {table_name}')
        cols = conn.execute(f'PRAGMA table_info({table_name})').fetchall()
        for col in cols:
            cid, name, ctype, notnull, default, pk = col
            flags = []
            if pk: flags.append('PK')
            if notnull: flags.append('NOT NULL')
            if default is not None: flags.append(f'DEFAULT={default}')
            print(f'  {name:24s} {ctype:12s} {", ".join(flags)}')


def show_data(conn):
    """显示所有表数据"""
    print('\n' + '=' * 60)
    print('表数据')
    print('=' * 60)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    for (table_name,) in tables:
        print(f'\n■ 表: {table_name}')
        rows = conn.execute(f'SELECT * FROM {table_name}').fetchall()
        if not rows:
            print('  (空)')
            continue
        # 列名
        col_names = [d[0] for d in conn.execute(f'SELECT * FROM {table_name} LIMIT 1').description]
        print('  ' + ' | '.join(col_names))
        print('  ' + '-' * 60)
        for row in rows:
            print('  ' + ' | '.join(str(v) for v in row))


def main():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    show_schema(conn)
    show_data(conn)
    conn.close()
    print('\n' + '=' * 60)


if __name__ == '__main__':
    main()
