import tkinter as tk
from tkinter import ttk
from datetime import datetime
import json

# 基础功能区
class Otaku:
    def __init__(self, config):
        self.config = config
        save_data = self.load_save()
        self.energy = save_data["energy"]

    def do_action(self, action_name, actions):
        action = actions[action_name]
        change = action["energy_change"]

        self.energy += change
        self.energy = max(0,min(self.config["max_energy"], self.energy))

        self.save_state()
        self.save_log(action_name, change)

    def load_save(self):
        try:
            with open("save.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"energy": self.config["default_energy"]}

    def load_log(self):
        try:
            with open("log.txt", "r", encoding="utf-8") as f:
                return [line.strip() for line in f]
        except FileNotFoundError:
            return []

    def save_log(self, action, change):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(f"{now}|{action}|能量变化：{change}|当前能量：{self.energy}\n")

    def save_state(self):
        data = {
            "energy": self.energy
        }

        with open("save.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

# 交互窗口
class OtakuSystem:
    def __init__(self):
        self.config = self.load_config()
        self.player = Otaku(self.config)
        self.actions = self.load_actions()
        self.window = tk.Tk()
        self.window.title(self.config["window_title"])
        self.window.geometry(self.config["window_size"])

        # 标题
        self.title_label = tk.Label(
            self.window,
            text=self.config["window_title"],
            font=("Microsoft YaHei", 18)
        )

        # 能量条
        self.title_label.pack(pady=15)
        self.energy_label = tk.Label(
            self.window,
            text=f"宅宅能量：{self.player.energy}/{self.config['max_energy']}",
            font=("Microsoft YaHei", 14)
        )
        self.energy_label.pack()

        # 进度条
        self.energy_bar = ttk.Progressbar(
            self.window,
            length=250,
            maximum=self.config["max_energy"],
            value=self.player.energy
        )

        self.energy_bar.pack()

        # 按钮
        for action_name, action_info in self.actions.items():
            change = action_info["energy_change"]

            button = tk.Button(
                self.window,
                text=f"{action_name} {change:+}",
                command=lambda name=action_name: self.handle_action(name)
            )
            button.pack()

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

    def load_actions(self):
        with open("actions.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def handle_action(self, action_name):
        self.player.do_action(action_name, self.actions)
        self.update_display()

    def update_display(self):
        logs = self.player.load_log()
        self.energy_label.config(
            text=f"宅宅能量：{self.player.energy}/{self.config['max_energy']}"
        )
        self.energy_bar["value"] = self.player.energy
        self.history_text.delete("1.0", tk.END)

        if len(logs) == 0:
            self.history_text.insert(tk.END, "今天还没有行动记录喵")
        else:
            for item in logs:
                self.history_text.insert(tk.END, item + "\n")

    def load_config(self):
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def run(self):
        self.update_display()

        self.window.mainloop()

app = OtakuSystem()

app.run()