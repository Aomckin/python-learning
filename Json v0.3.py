import tkinter as tk
from tkinter import ttk
from datetime import datetime
import json

# 基础功能区
def do_action(action, change):
    change_energy(change)
    check_energy()
    save_state()
    save_log(action, change)
    update_display()

def change_energy(change):
    global energy
    energy += change

def check_energy():
    global energy
    energy = max(0, energy)
    energy = min(100, energy)

def update_display():
    logs = load_log()

    energy_label.config(text=f"宅宅能量：{energy}/100")
    energy_bar["value"] = energy

    history_text.delete("1.0", tk.END)

    if len(logs) == 0:
        history_text.insert(tk.END, "今天还没有行动记录喵")
    else:
        for item in logs:
            history_text.insert(tk.END, item + "\n")

def save_log(action, change):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"{now}|{action}|能量变化：{change}|当前能量：{energy}/100\n")

def load_log():
    try:
        with open("log.txt", "r", encoding="utf-8") as f:
            return [line.strip() for line in f]
    except FileNotFoundError:
        return []

def load_save():
    try:
        with open("save.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "energy": 50
        }

def save_state():
    data = {
        "energy": energy
    }

    with open("save.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

save_data = load_save()
energy = save_data["energy"]

# 行动区
def study():
    do_action("学习", 10)

def exercise():
    do_action("健身", 15)

def anime():
    do_action("看番", -20)

def rest():
    do_action("休息", +5)



# 创建窗口
window = tk.Tk()
window.title("宅宅能量条系统 v0.2")
window.geometry("600x450")


# 标题
title_label = tk.Label(window, text="宅宅能量条系统", font=("Microsoft YaHei", 18))
title_label.pack(pady=15)


# 能量显示
energy_label = tk.Label(window, text=f"宅宅能量：{energy}/100", font=("Microsoft YaHei", 14))
energy_label.pack(pady=10)


# 进度条
energy_bar = ttk.Progressbar(
    window,
    length=250,
    maximum=100,
    value=energy
)
energy_bar.pack(pady=5)


# 按钮区
button_frame = tk.Frame(window)
button_frame.pack(pady=10)

actions = [
    ("学习 +10", "学习", 10),
    ("健身 +15", "健身", 15),
    ("看番 -20", "看番", -20),
    ("休息 +5", "休息", 5),
]

for text, action, change in actions:
    btn = tk.Button(
        button_frame,
        text=text,
        width=12,
        command=lambda a=action, c=change: do_action(a, c)
    )
    btn.pack(side=tk.LEFT, padx=5)


# 行动记录
history_label = tk.Label(window, text="行动记录", font=("Microsoft YaHei", 12))
history_label.pack(pady=5)

history_text = tk.Text(window, height=10, width=70)
history_text.pack(pady=5)

# 初始化显示
update_display()

# 运行窗口
window.mainloop()
