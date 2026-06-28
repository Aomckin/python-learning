# 宅宅能量条系统

这是一个 Python/Tkinter + FastAPI 练习项目，用来记录行动、每日任务、特殊任务、经验等级、成就、称号、商店和本地成长日志。

当前版本：v1.2

## 当前功能

- 宅宅能量条与行动番茄钟
- 正向/负向行动从 `actions.json` 读取能量变化和基础经验配置
- 行动计时支持时长选择、暂停、继续、放弃和完成结算
- 每日任务、特殊任务、任务刷新和任务奖励
- 等级系统与当前等级经验进度
- 成就系统与成就查看
- 称号系统、称号查看与称号佩戴
- 商店系统，支持单日限购、永久限购和无限供应商品
- FastAPI 后端命令入口：`GET /state`、`POST /command`
- 原生 HTML/CSS/JavaScript 网页控制台
- Tkinter 本地端通过 HTTP 访问 FastAPI，与网页端共用同一状态源
- JSON 配置与本地存档

## v1.2 重点变化

- 新增 `api.py` FastAPI 入口和 `/` 网页控制台。
- 新增 `static/`，提供最小网页控制台，不依赖前端框架或构建工具。
- 网页端覆盖主要 Tkinter 能力：行动计时、每日任务、特殊任务、商店、成就、称号。
- 网页商店、成就、称号使用二级弹窗显示，避免主界面堆满内容。
- 新增 `clients/api_client.py`，Tkinter 改为 FastAPI HTTP 客户端。
- 生产运行时只有 `api.py` 创建 `GameCore()`，网页端和 Tkinter 共享同一个后端状态。
- 行动经验改为 `actions.json` 的 `exp_change` 数据驱动。
- 新增 `utils/paths.py`，统一数据文件路径，避免不同启动目录读写不同 JSON/日志。
- 扩展 API、客户端、架构、路径、计时行动和网页静态资源测试。

## 运行方式

启动后端和网页控制台：

```bash
uvicorn api:app --reload
```

访问：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/state`

启动 Tkinter 本地端：

```bash
python main.py
```

注意：v1.2 起 Tkinter 需要先启动 FastAPI 后端。

## 测试方式

```bash
python -m unittest discover tests
```

静态网页脚本语法检查：

```bash
node --check static/app.js
```

## 主要文件

- `api.py`：FastAPI 后端入口和网页静态资源入口
- `main.py`：Tkinter 程序入口
- `ui.py`：Tkinter 界面与交互
- `clients/api_client.py`：Tkinter 使用的 HTTP 客户端
- `static/`：网页控制台
- `core.py`：命令 Facade 与系统装配
- `core_command.py` / `core_event.py` / `core_types.py`：命令、事件和展示快照类型
- `services/`：业务服务层
- `repositories/`：玩家存档和日志 IO
- `utils/`：JSON、日志、路径和时间工具
- `actions.json`：行动配置
- `tasks.json`：每日任务配置与状态
- `special_tasks.json`：特殊任务配置与状态
- `level.json`：等级配置
- `shop.json`：商店商品配置
- `achievements.json`：成就配置
- `titles.json`：称号配置
- `tests/`：测试

## 不纳入版本记录的本地文件

- `save.json`：本地玩家存档
- `log.txt`：本地行动日志
- `.idea/`：IDE 配置
- `.venv/`：本地虚拟环境
- `__pycache__/`：Python 缓存
- `build/`、`dist/`：本地构建产物
