# 宅宅能量条系统

这是一个 Python/Tkinter 练习项目，用来记录行动、每日任务、特殊任务、经验等级、成就、称号、商店和本地成长日志。

当前版本：v1.1

## 当前功能

- 宅宅能量条与行动计时器
- 正向行动支持 25/45/60 分钟计时，完成后按时长倍率增加能量
- 娱乐行动支持 30/60/90 分钟计时，完成后消耗能量并获得少量经验
- 行动计时支持暂停、继续和放弃，放弃不会计入行动统计
- 每日任务与任务奖励
- 特殊任务与金币奖励
- 等级系统与当前等级经验进度
- 行动记录，只显示最近 10 条
- 成就系统与成就查看窗口，支持经验和金币奖励
- 称号系统、称号查看窗口与称号佩戴
- 称号加成，支持经验倍率、行动能量加成、负向行动减耗和任务经验加成
- 商店系统，支持单日限量、永久限量和无限供应商品
- 主界面分区布局，包含状态概览、导航、行动、任务和最近记录
- 默认主题配置入口，为后续主题切换预留结构
- JSON 配置与本地存档

## v1.1 架构变化

- 新增 `core.py`、`core_command.py`、`core_event.py`、`core_types.py`，统一 Core 命令入口、事件返回和 UI 展示快照。
- 新增 `services/`，将行动、任务、商店、成就、称号、进度和视图拼装逻辑从 UI/Core 中拆出。
- 新增 `repositories/player_repository.py`，集中管理玩家存档和日志 IO。
- `PlayerService` 收口为唯一玩家状态修改入口，不再负责 JSON 或日志读写。
- UI 改为通过 `GameCommand` 调用 Core，并只处理 `GameEvent` 与 `GameState`。
- 增加架构守卫测试，防止跨模块直接写 `player` 状态、PlayerService 回流 IO、UI 读取业务内部结构。

## 运行方式

```bash
python main.py
```

## 测试方式

```bash
python -m unittest discover -s tests
```

## 主要文件

- `main.py`：程序入口
- `ui.py`：Tkinter 界面与事件展示
- `core.py`：命令 Facade 与系统装配
- `core_command.py` / `core_event.py` / `core_types.py`：命令、事件和展示快照类型
- `services/`：业务服务层
- `repositories/`：玩家存档和日志 IO
- `player.py`：玩家状态实体
- `task.py`：任务对象和任务管理
- `level.py`：等级系统
- `shop.py`：商店系统
- `achievement.py`：成就系统
- `title.py`：称号系统
- `themes.py`：默认主题、字体、间距与尺寸配置
- `actions.json`：行动配置
- `tasks.json`：每日任务配置与状态
- `special_tasks.json`：特殊任务配置与状态
- `level.json`：等级配置
- `shop.json`：商店商品配置
- `achievements.json`：成就配置
- `titles.json`：称号配置
- `tests/`：任务、商店、成就、计时行动、称号和主题相关测试

## 不纳入版本记录的本地文件

- `save.json`：本地玩家存档
- `log.txt`：本地行动日志
- `.idea/`：IDE 配置
- `.venv/`：本地虚拟环境
- `__pycache__/`：Python 缓存
