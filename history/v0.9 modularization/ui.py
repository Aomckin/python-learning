import tkinter as tk
from tkinter import ttk
import json

from achievement import Achievement
from player import Otaku
from task import TaskManager
from title import Title


class GameUI:
    def __init__(self):
        self.config = self.load_config()
        self.player = Otaku(self.config)
        self.actions = self.load_actions()
        self.task_manager = TaskManager()
        self.window = tk.Tk()
        self.window.title(self.config["window_title"])
        self.window.geometry(self.config["window_size"])
        self.task_buttons = []
        self.title_system = Title()
        self.achievement_manager = Achievement(self.player)
        self.achievement_clear_job = None

        self.window_title_label = tk.Label(
            self.window,
            text=self.config["window_title"],
            font=("Microsoft YaHei", 18)
        )

        self.window_title_label.pack(pady=15)
        self.energy_label = tk.Label(
            self.window,
            text=f"宅宅能量：{self.player.energy}/{self.config['max_energy']}",
            font=("Microsoft YaHei", 14)
        )
        self.energy_label.pack()

        self.exp_label = tk.Label(
            self.window,
            text=f"经验：{self.player.exp}",
            font=("Microsoft YaHei", 14)
        )
        self.exp_label.pack()

        self.title_label = tk.Label(
            self.window,
            text="称号：无",
            font=("Microsoft YaHei", 14)
        )
        self.title_label.pack()

        self.achievement_label = tk.Label(
            self.window,
            text="",
            font=("Microsoft YaHei", 12),
            fg="gold",
            justify="center"
        )

        self.achievement_label.pack(pady=5)

        self.energy_bar = ttk.Progressbar(
            self.window,
            length=250,
            maximum=self.config["max_energy"],
            value=self.player.energy
        )

        self.energy_bar.pack()

        self.action_frame = tk.Frame(self.window)
        self.action_frame.pack(pady=5)

        action_columns = 3

        for index, (action_name, action_info) in enumerate(self.actions.items()):
            change = action_info["energy_change"]
            row = index // action_columns
            column = index % action_columns

            button = tk.Button(
                self.action_frame,
                text=f"{action_name} {change:+}",
                width=10,
                command=lambda name=action_name: self.handle_action(name)
            )
            button.grid(row=row, column=column, padx=5, pady=3)

        self.task_label = tk.Label(
            self.window,
            text="每日任务",
            font=("Microsoft YaHei", 12)
        )
        self.task_label.pack(pady=10)

        for index, task in enumerate(self.task_manager.tasks):
            button_text = self.get_task_button_text(task)

            button = tk.Button(
                self.window,
                text=button_text,
                command=lambda i=index: self.handle_task(i)
            )
            button.pack()

            self.task_buttons.append(button)

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

        unlocked = (
            self.achievement_manager
            .check_achievements()
        )

        if unlocked:
            self.show_achievement(
                unlocked
            )

        self.update_display()

    def get_task_button_text(self, task):
        status = "已完成" if task.done else "未完成"

        return f"{task.name} | 奖励 {task.reward:+} | {status}"

    def handle_task(self, index):
        task = self.task_manager.tasks[index]
        reward, exp = self.task_manager.finish_task(index)

        if reward > 0 or exp > 0:
            self.player.add_reward(reward, exp, task.name)

        unlocked = self.achievement_manager.check_achievements()
        if unlocked:
            self.show_achievement(unlocked)
        self.update_display()

    def show_achievement(self, achievements):
        if isinstance(achievements, dict):
            achievements = [achievements]

        if self.achievement_clear_job is not None:
            self.window.after_cancel(self.achievement_clear_job)
            self.achievement_clear_job = None

        text = (
            "🏆 成就解锁！\n\n"
            + "\n".join(
                f"【{achievement.get('name', achievement.get('id', '未知成就'))}】 "
                f"{achievement.get('desc', '')} "
                f"EXP +{achievement.get('reward_exp', 0)}"
                for achievement in achievements
            )
        )

        self.achievement_label.config(
            text=text
        )

        self.achievement_clear_job = self.window.after(
            3000,
            lambda:
            self.achievement_label.config(text="")
        )

    def update_display(self):
        logs = self.player.load_log()
        self.energy_label.config(
            text=f"宅宅能量：{self.player.energy}/{self.config['max_energy']}"
        )
        self.energy_bar["value"] = self.player.energy
        self.history_text.delete("1.0", tk.END)
        self.exp_label.config(
            text=f"经验：{self.player.exp}"
        )
        title = self.title_system.get_title(self.task_manager.tasks)
        self.title_label.config(text=f"称号：{title}")

        if len(logs) == 0:
            self.history_text.insert(tk.END, "今天还没有行动记录喵")
        else:
            for item in logs:
                self.history_text.insert(tk.END, item + "\n")

        for index, task in enumerate(self.task_manager.tasks):
            self.task_buttons[index].config(
                text=self.get_task_button_text(task)
            )

    def load_config(self):
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def run(self):
        self.update_display()

        self.window.mainloop()
