# 版本历史

这里统一记录“宅宅能量条系统”的主要版本变化。历史快照文件和目录仍保留在 `history/` 下，本文档作为唯一版本说明入口。

## v0.1 main

快照：`history/v0.1 main.py`

- 搭建最早的命令行版本。
- 包含主菜单、状态查看、学习、健身、看番和历史记录等基础流程。
- 使用简单变量维护能量状态。

## v0.2 GUI_main

快照：`history/v0.2 GUI_main.py`

- 从命令行迁移到 Tkinter GUI。
- 增加窗口标题、能量显示、进度条、行动按钮和行动记录区域。
- 行动仍以函数为主组织。

## v0.3 Json

快照：`history/v0.3 Json.py`

- 加入 JSON 存档读取与写入。
- 增加日志读取与保存。
- 能量和行动记录开始具备持久化能力。

## v0.4 class

快照：`history/v0.4 class.py`

- 引入类结构。
- 新增 `Otaku` 管理玩家状态。
- 新增 `OtakuSystem` 管理 Tkinter 界面。
- 将行动、存档、日志和显示刷新从散函数整理进类中。

## v0.5 configs

快照：`history/v0.5 configs.py`

- 引入配置文件。
- 从 `config.json` 读取窗口标题、窗口大小、最大能量和默认能量。
- 从 `actions.json` 读取行动按钮与能量变化。
- 行动配置开始从代码中分离。

## v0.6 tasks

快照：`history/v0.6 tasks.py`

- 加入每日任务系统。
- 新增 `TaskManager` 管理任务读取、保存、完成和每日刷新。
- 完成任务可获得能量奖励。
- UI 中出现每日任务按钮区域。

## v0.7 tasks update

快照：`history/v0.7 tasks update.py`

- 任务系统增强。
- 新增 `Task` 对象，记录任务名称、奖励、经验、创建时间、完成次数和完成状态。
- 引入经验值。
- 加入基于任务完成次数的称号显示。
- 每日刷新时会重置任务完成状态。

## v0.8 achievement

快照：`history/v0.8 achievement.py`

- 加入成就系统。
- 新增 `AchievementManager` 读取 `achievements.json`。
- 支持按能量、任务完成数、行动次数解锁成就。
- 成就解锁后可奖励经验，并在界面显示提示。

## v0.8.1 achievement-log-layout hotfix

快照：`history/v0.8.1 achievement-log-layout hotfix.py`

- 修复普通行动解锁成就后没有立刻保存的问题。
- 一次触发多个成就时可以一起显示。
- 连续触发成就提示时，会取消上一次清除计时器，避免新提示被提前清空。
- 成就配置读取增加防御，缺少字段时不会直接崩溃。
- 行动记录只显示最后 10 条，避免日志区域往下溢出。
- 行动按钮改成 3 列自动排列，新增按钮后会自动换行。

## v0.9 modularization

快照：`history/v0.9 modularization/`

- 将单文件程序拆成多模块结构。
- `main.py` 精简为程序入口。
- `ui.py` 放置 `GameUI` 界面类。
- `player.py` 放置 `Otaku` 玩家状态、存档和日志逻辑。
- `task.py` 放置 `Task` 和 `TaskManager`。
- `achievement.py` 放置成就系统。
- `title.py` 放置称号系统。
- 保留 JSON 文件作为配置和数据来源。

## v0.9.1 title-achievement-ui

快照：`history/v0.9.1 title-achievement-ui/`

- 新增 `titles.json`，称号改为 JSON 配置驱动。
- `save.json` 支持保存已解锁称号和当前佩戴称号。
- 称号支持经验倍率和能量变化倍率两类加成。
- 主界面显示当前佩戴称号和加成效果。
- 新增成就二级窗口，可查看已获取和未获取成就。
- 新增称号二级窗口，可查看称号条件、简介、加成，并佩戴已解锁称号。
- 移除测试称号的强制解锁和强制佩戴逻辑。
- 更新 README，使说明与当前项目状态一致。

## v0.9.2 task-system-refactor

快照：`history/v0.9.2 task-system-refactor/`

- 普通每日任务改为任务池，每天固定随机抽取 3 个。
- 扩展 `tasks.json`，新增 `active_task_ids` 和稳定任务 `id`。
- 新增 `special_tasks.json`，特殊任务池每天固定随机抽取 1 个。
- 特殊任务使用 `coin` 金币奖励，不再使用能量 `reward`。
- `player.py` 新增 `coin` 和 `done_special_task_count` 字段。
- 特殊任务完成后增加金币、经验和特殊任务计数，不混入普通任务完成统计。
- UI 中每日任务和特殊任务并列展示。
- 特殊任务池替换为“人生RPG”风格任务。

## v0.9.3 level-shop-system

快照：`history/v0.9.3 level-shop-system/`

- 新增 `level.json` 和 `level.py`，经验从累计总经验动态换算为等级与当前等级进度。
- 主界面新增等级显示，经验显示改为当前等级进度，升级时显示低调提示。
- 将宅宅能量数值与能量条放到同一区域。
- 新增 `shop.json` 和 `shop.py`，商店系统独立成模块。
- 主界面新增商店二级窗口，按【任务】【成长】【称号】【娱乐】【收藏】五类横向排布。
- 商店商品支持单日限量、永久限量和无限供应。
- 初始商品包含刷新每日任务、单日双倍经验、增加特殊任务栏位。
- 特殊任务支持多栏位，并兼容旧的单 `active_task_id` 数据。
- 新增可购买称号“大魔法师 🧙‍♂️”，佩戴后能量变化程度 +50%。
- 将行动“写简历”改名为“敲代码”，并迁移当前存档统计键。
- 新增商店和特殊任务栏位相关测试。
