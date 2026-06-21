import tkinter as tk
from tkinter import ttk
from datetime import datetime
import json
import os

# 基础功能区
class Otaku:
    def __init__(self, config):
        self.config = config
        save_data = self.load_save()

        self.energy = save_data["energy"]
        self.exp = save_data.get("exp", 0)

        self.unlocked_achievements = save_data.get("unlocked_achievements",[])
        self.action_counts = save_data.get("action_counts",{})
        self.done_task_count = save_data.get("done_task_count",0)

    def do_action(self, action_name, actions):
        action = actions[action_name]
        change = action["energy_change"]

        self.energy += change
        self.energy = max(0,min(self.config["max_energy"], self.energy))

        self.action_counts[action_name] = \
            self.action_counts.get(action_name,0) + 1

        self.save_state()
        self.save_log(action_name, change)

    def load_save(self):
        try:
            with open("save.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "energy": self.config["default_energy"],
                "exp": 0,
                "unlocked_achievements": [],
                "action_counts": {},
                "done_task_count": 0
            }

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
            "energy": self.energy,
            "exp": self.exp,
            "unlocked_achievements":self.unlocked_achievements,
            "action_counts":self.action_counts,
            "done_task_count":self.done_task_count
        }

        with open("save.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def add_reward(self, reward, exp, task_name):
        self.energy += reward
        self.exp += exp
        self.done_task_count += 1
        self.energy = max(0, min(self.config["max_energy"], self.energy))

        self.save_state()
        self.save_log(
            f"完成任务：{task_name}",
            f"能量+{reward} 经验+{exp}"
        )

# 任务管理器区
class TaskManager:
    def __init__(self):
        self.tasks_data = {}
        self.tasks = []
        self.load_tasks()
        self.refresh_daily_tasks()

    # 每日任务
    def load_tasks(self):

        with open("tasks.json","r",encoding="utf-8") as f:
            self.tasks_data = json.load(f)

        self.tasks = [
            Task.from_dict(t)
            for t in self.tasks_data["tasks"]
        ]

    def save_tasks(self):
        self.tasks_data["tasks"] = [
            t.to_dict() for t in self.tasks
        ]

        with open("tasks.json", "w", encoding="utf-8") as f:
            json.dump(self.tasks_data, f, ensure_ascii=False, indent=4)

    def finish_task(self, index):
        task = self.tasks[index]

        if task.done:
            return 0, 0

        task.done = True
        task.completed_count += 1

        self.save_tasks()

        return task.reward, task.exp

    def refresh_daily_tasks(self):
        today = datetime.now().strftime("%Y-%m-%d")

        if "last_update_date" not in self.tasks_data:
            self.tasks_data["last_update_date"] = today
            self.save_tasks()
            return

        if self.tasks_data["last_update_date"] != today:
            for task in self.tasks:
                task.done = False

            self.tasks_data["last_update_date"] = today
            self.save_tasks()

# 任务区
class Task:
    def __init__(self, name, reward, exp=5):
        self.name = name
        self.reward = reward
        self.exp = exp
        self.created_time = datetime.now()
        self.completed_count = 0
        self.done = False

    @staticmethod
    def from_dict(data):
        task = Task(
            data["name"],
            data["reward"],
            data.get("exp", 5)
        )

        task.done = data.get("done", False)
        task.completed_count = data.get("completed_count", 0)

        # 时间可选恢复
        if "created_time" in data:
            task.created_time = datetime.strptime(
                data["created_time"],
                "%Y-%m-%d %H:%M:%S"
            )

        return task

    def to_dict(self):
        return {
            "name": self.name,
            "reward": self.reward,
            "exp": self.exp,
            "created_time": self.created_time.strftime("%Y-%m-%d %H:%M:%S"),
            "completed_count": self.completed_count,
            "done": self.done
        }

# 称号系统
class TitleSystem:
    def get_title(self, tasks):
        total = sum(t.completed_count for t in tasks)

        if total >= 10:
            return "任务支配者 🐉"
        elif total >= 5:
            return "熟练执行者 ⚙️"
        elif total >= 1:
            return "初学者 🌱"
        return "无称号"

# 成就系统
class AchievementManager:
    def __init__(self, player, achievement_file="achievements.json"):
        self.player = player
        self.achievement_file = achievement_file
        self.achievements = self.load_achievements()

    def load_achievements(self):
        if not os.path.exists(self.achievement_file):
            return []

        with open(self.achievement_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def check_achievements(self):
        unlocked = []

        for achievement in self.achievements:
            achievement_id = achievement["id"]

            if achievement_id in self.player.unlocked_achievements:
                continue

            if self.is_achievement_done(achievement):
                self.unlock_achievement(achievement)
                unlocked.append(achievement)

        return unlocked

    def is_achievement_done(self, achievement):
        condition_type = achievement["condition_type"]

        if condition_type == "energy_reach":
            return self.player.energy >= achievement["target_value"]

        if condition_type == "task_done_count":
            return self.player.done_task_count >= achievement["target_value"]

        if condition_type == "action_count":
            action_name = achievement["target_action"]
            count = self.player.action_counts.get(action_name, 0)
            return count >= achievement["target_value"]

        return False

    def unlock_achievement(self, achievement):
        achievement_id = achievement["id"]

        self.player.unlocked_achievements.append(achievement_id)

        reward_exp = achievement.get("reward_exp", 0)
        self.player.exp += reward_exp

# 交互窗口
class OtakuSystem:
    def __init__(self):
        self.config = self.load_config()
        self.player = Otaku(self.config)
        self.actions = self.load_actions()
        self.task_manager = TaskManager()
        self.window = tk.Tk()
        self.window.title(self.config["window_title"])
        self.window.geometry(self.config["window_size"])
        self.task_buttons = []
        self.title_system=TitleSystem()
        self.achievement_manager = AchievementManager(self.player)

        # 标题
        self.window_title_label = tk.Label(
            self.window,
            text=self.config["window_title"],
            font=("Microsoft YaHei", 18)
        )

        # 能量条
        self.window_title_label.pack(pady=15)
        self.energy_label = tk.Label(
            self.window,
            text=f"宅宅能量：{self.player.energy}/{self.config['max_energy']}",
            font=("Microsoft YaHei", 14)
        )
        self.energy_label.pack()

        # 经验
        self.exp_label = tk.Label(
            self.window,
            text=f"经验：{self.player.exp}",
            font=("Microsoft YaHei", 14)
        )
        self.exp_label.pack()

        # 称号
        self.title_label = tk.Label(
            self.window,
            text="称号：无",
            font=("Microsoft YaHei", 14)
        )
        self.title_label.pack()

        # 成就弹窗
        self.achievement_label = tk.Label(
            self.window,
            text="",
            font=("Microsoft YaHei", 12),
            fg="gold",
            justify="center"
        )

        self.achievement_label.pack(pady=5)

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

        # 任务按钮
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

        unlocked = (
            self.achievement_manager
            .check_achievements()
        )

        if unlocked:
            self.show_achievement(
                unlocked[0]
            )

        self.update_display()

    def get_task_button_text(self, task):
        status = "已完成" if task.done else "未完成"

        return f'{task.name} | 奖励 {task.reward:+} | {status}'

    def handle_task(self, index):
        task = self.task_manager.tasks[index]
        reward, exp = self.task_manager.finish_task(index)

        if reward > 0 or exp > 0:
            self.player.add_reward(reward, exp, task.name)

        unlocked = self.achievement_manager.check_achievements()
        if unlocked:
            self.show_achievement(unlocked[0])
            self.player.save_state()
        self.update_display()

    def show_achievement(self, achievement):

        text = (
            "🏆 成就解锁！\n\n"

            f"【{achievement['name']}】\n\n"

            f"{achievement['desc']}\n\n"

            f"EXP +{achievement['reward_exp']}"
        )

        self.achievement_label.config(
            text=text
        )

        self.window.after(
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

app = OtakuSystem()

app.run()