from datetime import datetime
import random

from utils.json_store import load_json, save_json
from utils.time_utils import format_datetime, get_now_datetime, get_today_str


class TaskSystem:
    def __init__(
            self,
            task_file,
            task_class,
            reward_fields,
            slot_count=1,
            invalid_active_strategy="draw",
            invalid_finish_returns_zero=False
    ):
        self.task_file = task_file
        self.task_class = task_class
        self.reward_fields = reward_fields
        self.slot_count = max(1, slot_count)
        self.invalid_active_strategy = invalid_active_strategy
        self.invalid_finish_returns_zero = invalid_finish_returns_zero
        self.tasks_data = {}
        self.all_tasks = []
        self.tasks = []
        self.task = None
        self.load_tasks()
        self.refresh()
        self.set_active()

    def load_tasks(self):
        self.tasks_data = load_json(self.task_file)
        self.prepare_tasks_data()
        self.all_tasks = [
            self.task_class.from_dict(t)
            for t in self.tasks_data["tasks"]
        ]

    def prepare_tasks_data(self):
        self.tasks_data.setdefault("active_task_ids", [])

    def save_tasks(self):
        self.tasks_data["tasks"] = [
            t.to_dict() for t in self.all_tasks
        ]
        save_json(self.task_file, self.tasks_data)

    def refresh(self):
        today = get_today_str()

        if self.tasks_data.get("last_update_date") != today:
            for task in self.all_tasks:
                task.done = False

            self.tasks_data["last_update_date"] = today
            self.draw()
            self.save_tasks()
            return

        if not self.has_valid_active_tasks():
            if self.invalid_active_strategy == "fill":
                self.fill_active_task_slots()
            else:
                self.draw()
            self.save_tasks()

    def draw(self):
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

    def has_valid_active_tasks(self):
        active_task_ids = self.tasks_data.get("active_task_ids", [])
        task_ids = {task.id for task in self.all_tasks}
        draw_count = min(self.slot_count, len(task_ids))

        if len(active_task_ids) != draw_count:
            return False

        return all(task_id in task_ids for task_id in active_task_ids)

    def set_active(self):
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
        self.task = self.tasks[0] if self.tasks else None

    def finish(self, index=0):
        if index < 0 or index >= len(self.tasks):
            if self.invalid_finish_returns_zero:
                return 0, 0
            raise IndexError(index)

        task = self.tasks[index]

        if task.done:
            return 0, 0

        task.done = True
        task.completed_count += 1
        self.save_tasks()

        return tuple(getattr(task, field) for field in self.reward_fields)


class DailyTaskSystem(TaskSystem):
    def __init__(self):
        super().__init__(
            task_file="tasks.json",
            task_class=Task,
            reward_fields=("reward", "exp"),
            slot_count=3,
            invalid_active_strategy="draw",
            invalid_finish_returns_zero=False
        )

    def refresh_daily_tasks(self):
        self.refresh()

    def draw_daily_tasks(self):
        self.draw()

    def has_valid_active_tasks(self):
        return super().has_valid_active_tasks()

    def set_active_tasks(self):
        self.set_active()

    def finish_task(self, index):
        return self.finish(index)

    def redraw_daily_tasks(self):
        self.draw()
        self.save_tasks()
        self.set_active()


class SpecialTaskSystem(TaskSystem):
    def __init__(self, slot_count=1):
        super().__init__(
            task_file="special_tasks.json",
            task_class=SpecialTask,
            reward_fields=("coin", "exp"),
            slot_count=slot_count,
            invalid_active_strategy="fill",
            invalid_finish_returns_zero=True
        )

    def prepare_tasks_data(self):
        if "active_task_ids" in self.tasks_data:
            return

        active_task_id = self.tasks_data.get("active_task_id", "")

        if active_task_id:
            self.tasks_data["active_task_ids"] = [active_task_id]
        else:
            self.tasks_data["active_task_ids"] = []

    def migrate_active_task_ids(self):
        self.prepare_tasks_data()

    def refresh_daily_task(self):
        self.refresh()

    def draw_daily_task(self):
        self.draw()

    def has_valid_active_task(self):
        return self.has_valid_active_tasks()

    def set_active_task(self):
        self.set_active()

    def finish_task(self, index=0):
        return self.finish(index)

    def set_slot_count(self, slot_count):
        self.slot_count = max(1, slot_count)

        if not self.has_valid_active_tasks():
            self.fill_active_task_slots()
            self.save_tasks()

        self.set_active()


class Task:
    def __init__(self, task_id, name, reward, exp=5):
        self.id = task_id
        self.name = name
        self.reward = reward
        self.exp = exp
        self.created_time = get_now_datetime()
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
            "created_time": format_datetime(self.created_time),
            "completed_count": self.completed_count,
            "done": self.done
        }

    @staticmethod
    def make_id(name):
        return name.lower().replace(" ", "_")


class SpecialTask:
    def __init__(self, task_id, name, coin, exp=5):
        self.id = task_id
        self.name = name
        self.coin = coin
        self.exp = exp
        self.created_time = get_now_datetime()
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
            "created_time": format_datetime(self.created_time),
            "completed_count": self.completed_count,
            "done": self.done
        }


TaskManager = DailyTaskSystem
SpecialTaskManager = SpecialTaskSystem
