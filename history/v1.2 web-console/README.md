# 宅宅能量条系统

这是 v1.2 web-console 快照，内容与项目根目录 v1.2 状态一致。

## 当前版本

v1.2

## 本版重点

- FastAPI 提供统一后端状态源与网页入口。
- Tkinter 通过 HTTP 客户端访问 FastAPI，不再创建本地备用 `GameCore()`。
- 网页控制台支持行动番茄钟、任务、商店、成就和称号。
- 网页端商店、成就、称号使用二级弹窗展示。
- 行动经验由 `actions.json` 的 `exp_change` 数据驱动。
- 数据路径统一到项目根目录，并支持测试环境变量覆盖。

## 运行

```bash
uvicorn api:app --reload
```

网页入口：

```text
http://127.0.0.1:8000/
```

Tkinter 入口：

```bash
python main.py
```

## 测试

```bash
node --check static/app.js
python -m unittest discover tests
```
