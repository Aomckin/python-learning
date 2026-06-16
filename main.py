import tkinter as tk
from tkinter import ttk
from datetime import datetime
import json

# 基础功能区
class Otaku:
    def __init__(self):
        save_data = self.load_save()
        self.energy = save_data["energy"]

    def do_action(self, action, change):
        self.change_energy(change)
        self.check_energy()
        self.save_state()
        self.save_log(action, change)

    def change_energy(self, change):
        self.energy += change

    def check_energy(self):
        self.energy = max(0,min(100,self.energy))

    def save_log(self, action, change):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(f"{now}|{action}|能量变化：{change}|当前能量：{self.energy}\n")

    def load_log(self):
        try:
            with open("log.txt", "r", encoding="utf-8") as f:
                return [line.strip() for line in f]
        except FileNotFoundError:
            return []

    def load_save(self):
        try:
            with open("save.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "energy": 50
            }

    def save_state(self):
        data = {
            "energy": self.energy
        }

        with open("save.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def study(self):
        self.do_action("学习", 10)

    def exercise(self):
        self.do_action("健身", 15)

    def anime(self):
        self.do_action("看番", -20)

    def rest(self):
        self.do_action("休息", +5)

# 交互窗口
class OtakuSystem:
    def __init__(self):

        self.player = Otaku()
        self.window = tk.Tk()
        self.window.title("宅宅能量条系统 v0.4")
        self.window.geometry("600x450")

        # 标题
        self.title_label = tk.Label(
            self.window,
            text="宅宅能量条系统",
            font=("Microsoft YaHei", 18)
        )

        # 能量条
        self.title_label.pack(pady=15)
        self.energy_label = tk.Label(
            self.window,
            text=f"宅宅能量：{self.player.energy}/100",
            font=("Microsoft YaHei", 14)
        )
        self.energy_label.pack()

        # 进度条
        self.energy_bar = ttk.Progressbar(
            self.window,
            length=250,
            maximum=100,
            value=self.player.energy
        )

        self.energy_bar.pack()

        # 按钮
        actions = [
            ("学习 +10", self.player.study),
            ("健身 +15", self.player.exercise),
            ("看番 -20", self.player.anime),
            ("休息 +5", self.player.rest)
        ]
        for text, func in actions:
            btn = tk.Button(
                self.window,
                text=text,
                width=12,
                command=lambda f=func: (
                    f(),
                    self.update_display()
                )
            )
            btn.pack()

        # 历史记录
        self.history_label = tk.Label(
            self.window,
            text="行动记录",
            font=("Microsoft YaHei", 12)
        )
        self.history_label.pack()

        self.history_text = tk.Text(
            self.window,
            height=10,
            width=70
        )
        self.history_text.pack()

    def update_display(self):
        logs = self.player.load_log()
        self.energy_label.config(
            text=f"宅宅能量：{self.player.energy}/100"
        )
        self.energy_bar["value"] = self.player.energy
        self.history_text.delete("1.0", tk.END)

        if len(logs) == 0:
            self.history_text.insert(tk.END, "今天还没有行动记录喵")
        else:
            for item in logs:
                self.history_text.insert(tk.END, item + "\n")

    def run(self):
        self.update_display()

        self.window.mainloop()

app = OtakuSystem()

app.run()