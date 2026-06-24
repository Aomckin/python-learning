# 宅宅能量条系统

这是一个 Python/Tkinter 练习项目，用来记录行动、每日任务、特殊任务、经验等级、成就、称号和商店。

## 当前功能

- 宅宅能量条与行动按钮
- 每日任务与任务奖励
- 特殊任务与金币奖励
- 等级系统与当前等级经验进度
- 行动记录，只显示最近 10 条
- 成就系统与成就查看窗口
- 称号系统、称号查看窗口与称号佩戴
- 称号加成，当前支持经验倍率和能量变化倍率
- 商店系统，支持单日限量、永久限量和无限供应商品
- JSON 配置与本地存档

## 运行方式

```bash
python main.py
```

## 主要文件

- `main.py`：程序入口
- `ui.py`：Tkinter 界面
- `player.py`：玩家状态、存档和日志
- `task.py`：任务对象和任务管理
- `level.py`：等级系统
- `shop.py`：商店系统
- `achievement.py`：成就系统
- `title.py`：称号系统
- `actions.json`：行动配置
- `tasks.json`：每日任务配置与状态
- `special_tasks.json`：特殊任务配置与状态
- `level.json`：等级配置
- `shop.json`：商店商品配置
- `achievements.json`：成就配置
- `titles.json`：称号配置
