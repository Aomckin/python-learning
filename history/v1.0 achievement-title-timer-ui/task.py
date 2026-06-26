from datetime import datetime
import json
import random


class TaskManager:
    def __init__(self):
        self.tasks_data = {}
        self.all_tasks = []
        self.tasks = []
        self.load_tasks()
        self.refresh_daily_tasks()
        self.set_active_tasks()

    def load_tasks(self):
        with open("tasks.json", "r", encoding="utf-8") as f:
            self.tasks_data = json.load(f)

        self.tasks_data.setdefault("active_task_ids", [])

        self.all_tasks = [
            Task.from_dict(t)
            for t in self.tasks_data["tasks"]
        ]

    def save_tasks(self):
        self.tasks_data["tasks"] = [
            t.to_dict() for t in self.all_tasks
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

        if self.tasks_data.get("last_update_date") != today:
            for task in self.all_tasks:
                task.done = False

            self.tasks_data["last_update_date"] = today
            self.draw_daily_tasks()
            self.save_tasks()
            return

        if not self.has_valid_active_tasks():
            self.draw_daily_tasks()
            self.save_tasks()

    def draw_daily_tasks(self):
        task_ids = [task.id for task in self.all_tasks]
        draw_count = min(3, len(task_ids))

        if draw_count == 0:
            self.tasks_data["active_task_ids"] = []
            return

        self.tasks_data["active_task_ids"] = random.sample(task_ids, draw_count)

    def has_valid_active_tasks(self):
        active_task_ids = self.tasks_data.get("active_task_ids", [])
        task_ids = {task.id for task in self.all_tasks}
        draw_count = min(3, len(task_ids))

        if len(active_task_ids) != draw_count:
            return False

        return all(task_id in task_ids for task_id in active_task_ids)

    def set_active_tasks(self):
        active_task_ids = self.tasks_data.get("active_task_ids", [])
        task_by_id = {
            task.id: task
            for task in self.all_tasks
        }

        self.tasks = [
            task_by_id[task_id]
            for task_id in active_task_ids
            if task_id in task_by_id
        ]

    def redraw_daily_tasks(self):
        self.draw_daily_tasks()
        self.save_tasks()
        self.set_active_tasks()


class Task:
    def __init__(self, task_id, name, reward, exp=5):
        self.id = task_id
        self.name = name
        self.reward = reward
        self.exp = exp
        self.created_time = datetime.now()
        self.completed_count = 0
        self.done = False

    @staticmethod
    def from_dict(data):
        task = Task(
            data.get("id", Task.make_id(data["name"])),
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
            "id": self.id,
            "name": self.name,
            "reward": self.reward,
            "exp": self.exp,
            "created_time": self.created_time.strftime("%Y-%m-%d %H:%M:%S"),
            "completed_count": self.completed_count,
            "done": self.done
        }

    @staticmethod
    def make_id(name):
        return name.lower().replace(" ", "_")


class SpecialTaskManager:
    def __init__(self, slot_count=1):
        self.slot_count = max(1, slot_count)
        self.tasks_data = {}
        self.all_tasks = []
        self.tasks = []
        self.task = None
        self.load_tasks()
        self.refresh_daily_task()
        self.set_active_task()

    def load_tasks(self):
        with open("special_tasks.json", "r", encoding="utf-8") as f:
            self.tasks_data = json.load(f)

        self.migrate_active_task_ids()

        self.all_tasks = [
            SpecialTask.from_dict(t)
            for t in self.tasks_data["tasks"]
        ]

    def migrate_active_task_ids(self):
        if "active_task_ids" in self.tasks_data:
            return

        active_task_id = self.tasks_data.get("active_task_id", "")

        if active_task_id:
            self.tasks_data["active_task_ids"] = [active_task_id]
        else:
            self.tasks_data["active_task_ids"] = []

    def save_tasks(self):
        self.tasks_data["tasks"] = [
            t.to_dict() for t in self.all_tasks
        ]

        with open("special_tasks.json", "w", encoding="utf-8") as f:
            json.dump(self.tasks_data, f, ensure_ascii=False, indent=4)

    def finish_task(self, index=0):
        if index < 0 or index >= len(self.tasks):
            return 0, 0

        task = self.tasks[index]

        if task.done:
            return 0, 0

        task.done = True
        task.completed_count += 1

        self.save_tasks()

        return task.coin, task.exp

    def refresh_daily_task(self):
        today = datetime.now().strftime("%Y-%m-%d")

        if self.tasks_data.get("last_update_date") != today:
            for task in self.all_tasks:
                task.done = False

            self.tasks_data["last_update_date"] = today
            self.draw_daily_task()
            self.save_tasks()
            return

        if not self.has_valid_active_task():
            self.fill_active_task_slots()
            self.save_tasks()

    def draw_daily_task(self):
        task_ids = [task.id for task in self.all_tasks]
        draw_count = min(self.slot_count, len(task_ids))

        if draw_count == 0:
            self.tasks_data["active_task_ids"] = []
            return

        self.tasks_data["active_task_ids"] = random.sample(task_ids, draw_count)

    def fill_active_task_slots(self):
        task_ids = [task.id for task in self.all_tasks]
        draw_count = min(self.slot_count, len(task_ids))

        if draw_count == 0:
            self.tasks_data["active_task_ids"] = []
            return

        active_task_ids = []

        for task_id in self.tasks_data.get("active_task_ids", []):
            if task_id in task_ids and task_id not in active_task_ids:
                active_task_ids.append(task_id)

        if len(active_task_ids) > draw_count:
            active_task_ids = active_task_ids[:draw_count]

        remaining_task_ids = [
            task_id for task_id in task_ids
            if task_id not in active_task_ids
        ]
        missing_count = draw_count - len(active_task_ids)

        if missing_count > 0:
            active_task_ids.extend(
                random.sample(remaining_task_ids, missing_count)
            )

        self.tasks_data["active_task_ids"] = active_task_ids

    def has_valid_active_task(self):
        active_task_ids = self.tasks_data.get("active_task_ids", [])
        task_ids = {task.id for task in self.all_tasks}
        draw_count = min(self.slot_count, len(task_ids))

        if len(active_task_ids) != draw_count:
            return False

        return all(task_id in task_ids for task_id in active_task_ids)

    def set_active_task(self):
        active_task_ids = self.tasks_data.get("active_task_ids", [])
        task_by_id = {
            task.id: task
            for task in self.all_tasks
        }

        self.tasks = [
            task_by_id[task_id]
            for task_id in active_task_ids
            if task_id in task_by_id
        ]

        if len(self.tasks) > 0:
            self.task = self.tasks[0]
        else:
            self.task = None

    def set_slot_count(self, slot_count):
        self.slot_count = max(1, slot_count)

        if not self.has_valid_active_task():
            self.fill_active_task_slots()
            self.save_tasks()

        self.set_active_task()


class SpecialTask:
    def __init__(self, task_id, name, coin, exp=5):
        self.id = task_id
        self.name = name
        self.coin = coin
        self.exp = exp
        self.created_time = datetime.now()
        self.completed_count = 0
        self.done = False

    @staticmethod
    def from_dict(data):
        task = SpecialTask(
            data.get("id", Task.make_id(data["name"])),
            data["name"],
            data.get("coin", 0),
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
            "id": self.id,
            "name": self.name,
            "coin": self.coin,
            "exp": self.exp,
            "created_time": self.created_time.strftime("%Y-%m-%d %H:%M:%S"),
            "completed_count": self.completed_count,
            "done": self.done
        }
