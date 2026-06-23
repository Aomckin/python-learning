from datetime import datetime
import json


class TaskManager:
    def __init__(self):
        self.tasks_data = {}
        self.tasks = []
        self.load_tasks()
        self.refresh_daily_tasks()

    def load_tasks(self):
        with open("tasks.json", "r", encoding="utf-8") as f:
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
