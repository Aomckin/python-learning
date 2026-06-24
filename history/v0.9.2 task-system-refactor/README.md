# 宅宅能量条系统

这是一个 Python/Tkinter 练习项目，用来记录行动、每日任务、经验、成就和称号。

## 当前功能

- 宅宅能量条与行动按钮
- 每日任务与任务奖励
- 行动记录，只显示最近 10 条
- 成就系统与成就查看窗口
- 称号系统、称号查看窗口与称号佩戴
- 称号加成，当前支持经验倍率和能量变化倍率
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
- `achievement.py`：成就系统
- `title.py`：称号系统
- `actions.json`：行动配置
- `tasks.json`：每日任务配置与状态
- `achievements.json`：成就配置
- `titles.json`：称号配置
