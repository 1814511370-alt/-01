#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import os
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / 'data' / 'daidai.db'
SCRIPT_DIR = ROOT_DIR / 'data' / 'scripts'
PANEL_PYTHON = ROOT_DIR / 'data' / 'deps' / 'python' / '3.11' / 'bin' / 'python'

TARGETS = {
    'dx': {
        'title': '电信保活',
        'script': 'md定时保活-电信.py',
        'required_envs': ['DX_KEEPALIVE_URL', 'DX_KEEPALIVE_COOKIE', 'DX_KEEPALIVE_NAME'],
        'task_name': 'md定时保活-电信',
        'task_command': 'task md定时保活-电信.py',
    },
    'lt': {
        'title': '联通保活',
        'script': 'md定时保活-联通.py',
        'required_envs': ['LT_KEEPALIVE_URL', 'LT_KEEPALIVE_COOKIE', 'LT_KEEPALIVE_NAME'],
        'task_name': 'md定时保活-联通',
        'task_command': 'task md定时保活-联通.py',
    },
}


def get_python_bin():
    if PANEL_PYTHON.exists():
        return str(PANEL_PYTHON)
    return sys.executable


def load_enabled_envs():
    if not DB_PATH.exists():
        raise FileNotFoundError(f'数据库不存在: {DB_PATH}')

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute('SELECT name, value FROM env_vars WHERE enabled = 1').fetchall()
    return {row['name']: row['value'] or '' for row in rows}


def load_tasks():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            'SELECT name, command, task_before, status, cron_expression FROM tasks ORDER BY id'
        ).fetchall()
    return {row['name']: dict(row) for row in rows}


def print_env_status(name, value):
    state = '已配置' if value.strip() else '缺失'
    print(f'  - {name}: {state}')


def check_task_config(target, tasks):
    task = tasks.get(target['task_name'])
    if not task:
        print(f'  - 任务配置: 缺失 {target["task_name"]}')
        return False

    ok = True
    if task['command'] != target['task_command']:
        print(f'  - 任务命令: 当前 {task["command"]}，建议 {target["task_command"]}')
        ok = False
    else:
        print(f'  - 任务命令: 正常 {task["command"]}')

    if task.get('task_before'):
        print('  - 前置命令: 建议清空，避免环境变量传递误判')
        ok = False
    else:
        print('  - 前置命令: 已清空')

    print(f'  - 定时表达式: {task["cron_expression"]}')
    print(f'  - 启用状态: {"启用" if float(task["status"]) == 1 else "停用"}')
    return ok


def run_target(key, envs, tasks):
    target = TARGETS[key]
    print(f'\n[{target["title"]}]')

    missing = []
    for env_name in target['required_envs']:
        value = envs.get(env_name, '')
        print_env_status(env_name, value)
        if not value.strip():
            missing.append(env_name)

    task_ok = check_task_config(target, tasks)
    if missing:
        print(f'  - 执行结果: 跳过，缺少 {", ".join(missing)}')
        return 1

    script_path = SCRIPT_DIR / target['script']
    if not script_path.exists():
        print(f'  - 执行结果: 脚本缺失 {script_path}')
        return 1

    run_env = os.environ.copy()
    run_env.update(envs)
    run_env['PYTHONPATH'] = str(SCRIPT_DIR)

    print('  - 执行结果: 开始手动验证')
    completed = subprocess.run(
        [get_python_bin(), str(script_path)],
        cwd=str(SCRIPT_DIR),
        env=run_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    output = completed.stdout.strip()
    if output:
        for line in output.splitlines():
            print(f'    {line}')

    if completed.returncode == 0 and task_ok:
        print('  - 验证状态: 通过')
        return 0

    print(f'  - 验证状态: 失败 exit={completed.returncode}')
    return 1


def main():
    parser = argparse.ArgumentParser(description='检查并手动验证 md 双线路保活')
    parser.add_argument('--target', choices=['all', 'dx', 'lt'], default='all', help='选择验证目标')
    args = parser.parse_args()

    envs = load_enabled_envs()
    tasks = load_tasks()
    keys = ['dx', 'lt'] if args.target == 'all' else [args.target]

    print('md 双线路保活检查')
    print(f'- 数据库: {DB_PATH}')
    print(f'- 脚本目录: {SCRIPT_DIR}')
    print(f'- Python: {get_python_bin()}')

    failed = 0
    for key in keys:
        failed += run_target(key, envs, tasks)

    if failed:
        print('\n检查完成：存在失败项')
        sys.exit(1)

    print('\n检查完成：全部通过')


if __name__ == '__main__':
    main()
