# 呆呆面板

这是独立于 `呆呆` 和 `代挂` 的第三个部分，目录为 `/workspace/呆呆面板`。

当前安装内容：

- 二进制：`daidai-linux-amd64`
- 配置：`config.yaml`
- 前端静态资源：`web/`
- 数据目录：`data/`

默认端口：

- `5701`

## 启动与停止

推荐使用统一入口：

```bash
cd /workspace/呆呆面板

./panel.sh status

./panel.sh start

./panel.sh restart

./panel.sh stop
```

原始管理脚本仍可直接使用：

```bash
cd /workspace/呆呆面板

./start-automation-panel.sh

./status-automation-panel.sh

./restart-automation-panel.sh

./stop-automation-panel.sh
```

## 日常体检

```bash
cd /workspace/呆呆面板

# 检查服务状态
./panel.sh status

# 检查任务、脚本、环境变量、日志目录
./panel.sh check

# 检查并手动运行 md 双线路保活
./panel.sh md-check
```

## 自启动说明

当前环境的 PID 1 是 `firecracker-init`，没有 `systemd`，因此无法使用 `systemctl enable` 做系统级开机自启动。

当前可用方案：

- 使用 `autostart-automation-panel.sh` 做会话级自启动
- 每次进入当前环境后执行一次即可确保服务拉起

```bash
cd /workspace/呆呆面板

./autostart-automation-panel.sh
```

## 配置文件

`config.yaml` 当前关键项：

- 端口：`5701`
- 数据库：`./data/daidai.db`
- 数据目录：`./data`
- 日志目录：`./data/logs`

## 依赖

已安装：
- `python3.11-venv` - 用于创建托管 Python 虚拟环境（2026-06-10 已安装）

## 说明

- 运行时默认注入 `TZ=Asia/Shanghai`
- 管理日志写入 `data/logs/automation-panel-managed.log`
- 当前目录完全独立，不影响 `/workspace/呆呆` 和 `/workspace/redline-login`
- 已成功完成初始化管理员创建，可直接登录使用

## 双线路 md 定时保活

当前 md 保活已按“共享核心逻辑 + 两个入口脚本 + 两套原始变量”的方式配置。

共享核心逻辑文件：

- `data/scripts/md_keepalive_common.py`

任务入口脚本：

- `data/scripts/md定时保活-电信.py`
- `data/scripts/md定时保活-联通.py`

面板中维护两套原始变量：

- 电信：`DX_KEEPALIVE_URL`、`DX_KEEPALIVE_COOKIE`、`DX_KEEPALIVE_NAME`
- 联通：`LT_KEEPALIVE_URL`、`LT_KEEPALIVE_COOKIE`、`LT_KEEPALIVE_NAME`

当前任务：

- `md定时保活-电信`
- `md定时保活-联通`

任务命令分别为：

```bash
task md定时保活-电信.py

task md定时保活-联通.py
```

维护规则：

- 共享核心逻辑通过入口脚本分别读取 `DX_*` 和 `LT_*`
- 面板里直接修改 `DX_*` 或 `LT_*` 原始变量值
- 新增第三套线路时，继续按相同模式新增一组原始变量和一个任务

## 一键检查 md 保活

日常排查优先使用一键检查脚本，它会直接读取面板数据库中的已启用环境变量，检查任务命令、前置命令、定时表达式，并手动执行对应保活脚本。

```bash
cd /workspace/呆呆面板

# 推荐入口
./panel.sh md-check

# 检查电信和联通
./check-md-keepalive.py

# 只检查电信
./check-md-keepalive.py --target dx

# 只检查联通
./check-md-keepalive.py --target lt
```

脚本只显示变量是否已配置，不会输出 Cookie 内容。
