import tkinter as tk
from tkinter import ttk
from datetime import datetime

energy = 50
history = []


def do_action(action, change):

    change_energy(change)

    save_log(action, change)

def check_energy():
    global energy
    energy = max(0, energy)
    energy = min(100, energy)

def update_display():
    energy_label.config(text=f"宅宅能量：{energy}/100")
    energy_bar["value"] = energy

    history_text.delete("1.0", tk.END)

    if len(history) == 0:
        history_text.insert(tk.END, "今天还没有行动记录喵")
    else:
        for item in history:
            history_text.insert(tk.END, item + "\n")

def study():
    global energy
    energy += 10
    check_energy()
    current_time = datetime.now().strftime("%H:%M:%S")

    history.append(
        f"{current_time} 学习 +10"
    )
    update_display()
    save_log("学习", "+10")

def exercise():
    global energy
    energy += 15
    check_energy()
    current_time = datetime.now().strftime("%H:%M:%S")

    history.append(
        f"{current_time} 健身 +15"
    )
    update_display()
    save_log("健身", "+15")

def watch_anime():
    global energy
    energy -= 20
    check_energy()
    current_time = datetime.now().strftime("%H:%M:%S")

    history.append(
        f"{current_time} 看番 -20"
    )
    update_display()
    save_log("看番", "-20")

def rest():
    global energy
    energy += 5
    check_energy()
    current_time = datetime.now().strftime("%H:%M:%S")

    history.append(
        f"{current_time} 休息 +5"
    )
    update_display()
    save_log("休息", "+5")

def save_log(action, change):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"{now} | {action} | 能量变化：{change}\n")


# 创建窗口
window = tk.Tk()
window.title("宅宅能量条系统 v0.2")
window.geometry("400x450")

# 标题
title_label = tk.Label(window, text="宅宅能量条系统", font=("Microsoft YaHei", 18))
title_label.pack(pady=15)


# 能量显示
energy_label = tk.Label(window, text=f"宅宅能量：{energy}/100", font=("Microsoft YaHei", 14))
energy_label.pack(pady=10)


#进度条
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

study_button = tk.Button(button_frame, text="学习 +10", width=12, command=study)
study_button.grid(row=0, column=0, padx=5, pady=5)

exercise_button = tk.Button(button_frame, text="健身 +15", width=12, command=exercise)
exercise_button.grid(row=0, column=1, padx=5, pady=5)

anime_button = tk.Button(button_frame, text="看番 -20", width=12, command=watch_anime)
anime_button.grid(row=1, column=0, padx=5, pady=5)

rest_button = tk.Button(button_frame, text="休息 +5", width=12, command=rest)
rest_button.grid(row=1, column=1, padx=5, pady=5)

# 行动记录
history_label = tk.Label(window, text="行动记录", font=("Microsoft YaHei", 12))
history_label.pack(pady=5)

history_text = tk.Text(window, height=10, width=40)
history_text.pack(pady=5)

# 初始化显示
update_display()

# 运行窗口
window.mainloop()