#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import sqlite3
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / 'data' / 'daidai.db'
SCRIPT_DIR = ROOT_DIR / 'data' / 'scripts'
LOG_ROOT = ROOT_DIR / 'data' / 'logs'
TASK_SCRIPT_PATTERN = re.compile(r'^task\s+(.+\.py)\s*$')


def load_rows(query):
    if not DB_PATH.exists():
        raise FileNotFoundError(f'数据库不存在: {DB_PATH}')
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(query).fetchall()]


def status_text(value):
    try:
        return '启用' if float(value) == 1 else '停用'
    except (TypeError, ValueError):
        return f'未知({value})'


def check_cron(expr):
    parts = (expr or '').split()
    if len(parts) in (5, 6):
        return True
    return False


def print_issue(issues, message):
    issues.append(message)
    print(f'  - 问题: {message}')


def check_task(task):
    issues = []
    print(f'\n[{task["id"]}] {task["name"]}')
    print(f'  - 状态: {status_text(task["status"])}')
    print(f'  - 命令: {task["command"]}')
    print(f'  - 定时: {task["cron_expression"]}')

    if not check_cron(task['cron_expression']):
        print_issue(issues, 'cron 表达式字段数量异常')

    match = TASK_SCRIPT_PATTERN.match(task['command'].strip())
    if match:
        script_name = match.group(1)
        script_path = SCRIPT_DIR / script_name
        if script_path.exists():
            print(f'  - 脚本: 存在 {script_name}')
        else:
            print_issue(issues, f'脚本不存在 {script_name}')
    else:
        print('  - 脚本: 非 task Python 脚本命令，跳过文件检查')

    if task.get('task_before'):
        print_issue(issues, 'task_before 非空，面板不会把 export 变量传给 task 进程')
    else:
        print('  - 前置命令: 空')

    if task.get('timeout') and int(task['timeout']) > 0:
        print(f'  - 超时: {task["timeout"]} 秒')
    else:
        print('  - 超时: 未设置')

    expected_log_dir_prefix = f'task_{task["id"]}_'
    log_dirs = [p.name for p in LOG_ROOT.glob(f'{expected_log_dir_prefix}*') if p.is_dir()]
    if log_dirs:
        print(f'  - 日志目录: {", ".join(sorted(log_dirs))}')
    else:
        print('  - 日志目录: 暂无')

    return issues


def check_envs(envs):
    issues = []
    print('\n[环境变量]')
    names = {}
    for env in envs:
        names.setdefault(env['name'], []).append(env)

    for name, rows in sorted(names.items()):
        enabled_rows = [row for row in rows if int(row['enabled']) == 1]
        groups = ', '.join(sorted({row.get('group') or '未分组' for row in rows}))
        state = '启用' if enabled_rows else '停用'
        value_state = '已配置' if any((row.get('value') or '').strip() for row in enabled_rows) else '缺失'
        print(f'  - {name}: {state}, {value_state}, 分组={groups}')
        if len(rows) > 1:
            issues.append(f'环境变量重复: {name}')
        if enabled_rows and value_state == '缺失':
            issues.append(f'启用变量未填写: {name}')

    if not envs:
        issues.append('没有环境变量记录')
    return issues


def main():
    tasks = load_rows(
        'SELECT id, name, command, cron_expression, status, task_before, timeout '
        'FROM tasks ORDER BY id'
    )
    envs = load_rows('SELECT id, name, value, enabled, "group" FROM env_vars ORDER BY id')

    print('呆呆面板任务体检')
    print(f'- 数据库: {DB_PATH}')
    print(f'- 脚本目录: {SCRIPT_DIR}')
    print(f'- 日志目录: {LOG_ROOT}')

    all_issues = []
    if not tasks:
        all_issues.append('没有任务记录')

    for task in tasks:
        all_issues.extend(check_task(task))

    all_issues.extend(check_envs(envs))

    print('\n[结果]')
    if all_issues:
        for issue in all_issues:
            print(f'- {issue}')
        sys.exit(1)

    print('- 未发现配置问题')


if __name__ == '__main__':
    main()
