import json
import os


OUTDOOR_DAILY_TASK_IDS = {"walk_20_minutes"}
OUTDOOR_SPECIAL_TASK_IDS = {
    "wind_traveler",
    "city_roaming",
    "face_inner_self",
    "summer_night_walk",
}
NEGATIVE_ACTION_IDS = {"看番", "推gal", "打游戏"}


class Title:
    def __init__(self, player, title_file="titles.json", special_tasks_file="special_tasks.json"):
        self.player = player
        self.title_file = title_file
        self.special_tasks_file = special_tasks_file
        self.titles = self.load_titles()

    def load_titles(self):
        if not os.path.exists(self.title_file):
            return []

        with open(self.title_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def check_titles(self, tasks):
        unlocked = []

        for title in self.titles:
            title_id = title.get("id")

            if not title_id:
                continue

            if title_id in self.player.unlocked_titles:
                continue

            if self.is_title_done(title, tasks):
                self.unlock_title(title)
                unlocked.append(title)

        if unlocked:
            self.player.save_state()

        return unlocked

    def is_title_done(self, title, tasks):
        condition_type = title.get("condition_type")
        target_value = title.get("target_value")

        if condition_type == "always":
            return True

        if target_value is None:
            return False

        if condition_type == "task_completed_count":
            total = sum(task.completed_count for task in tasks)
            return total >= target_value

        if condition_type == "task_done_count":
            return self.player.done_task_count >= target_value

        if condition_type == "energy_reach":
            return self.player.energy >= target_value

        if condition_type == "action_count":
            action_id, count = self.parse_action_count_target(title)
            if not action_id:
                return False

            return self.player.action_counts.get(action_id, 0) >= count

        if condition_type == "action_combo_count":
            return self.is_action_combo_done(target_value)

        if condition_type == "special_task_completed_count":
            task_id = target_value.get("task_id")
            count = target_value.get("count", 1)
            return self.get_special_task_completed_count(task_id) >= count

        if condition_type == "achievement_unlocked_count":
            return len(self.player.unlocked_achievements) >= target_value

        if condition_type == "timed_action_completed_count":
            return getattr(self.player, "completed_timed_actions", 0) >= target_value

        if condition_type == "outdoor_task_completed_count":
            return self.get_outdoor_task_completed_count(tasks) >= target_value

        if condition_type == "shop_purchase":
            return self.player.shop_total_purchases.get(target_value, 0) > 0

        return False

    def parse_action_count_target(self, title):
        target_value = title.get("target_value")

        if isinstance(target_value, dict):
            return target_value.get("action_id"), target_value.get("count", 1)

        return title.get("target_action"), target_value

    def is_action_combo_done(self, requirements):
        if not isinstance(requirements, list):
            return False

        for requirement in requirements:
            action_id = requirement.get("action_id")
            count = requirement.get("count", 1)

            if not action_id:
                return False

            if self.player.action_counts.get(action_id, 0) < count:
                return False

        return True

    def get_special_task_completed_count(self, task_id):
        if not os.path.exists(self.special_tasks_file):
            return 0

        with open(self.special_tasks_file, "r", encoding="utf-8") as f:
            tasks_data = json.load(f)

        for task in tasks_data.get("tasks", []):
            if task.get("id") == task_id:
                return task.get("completed_count", 0)

        return 0

    def get_outdoor_task_completed_count(self, daily_tasks):
        total = 0

        for task in daily_tasks:
            if task.id in OUTDOOR_DAILY_TASK_IDS:
                total += task.completed_count

        for task_id in OUTDOOR_SPECIAL_TASK_IDS:
            total += self.get_special_task_completed_count(task_id)

        return total

    def unlock_title(self, title):
        title_id = title.get("id")

        if not title_id:
            return

        if title_id in self.player.unlocked_titles:
            return

        self.player.unlocked_titles.append(title_id)

        if not self.player.equipped_title:
            self.player.equipped_title = title_id

    def unlock_title_by_id(self, title_id):
        title = self.get_title_by_id(title_id)

        if title is None:
            return False

        self.unlock_title(title)
        self.player.save_state()
        return True

    def equip_title(self, title_id):
        if title_id not in self.player.unlocked_titles:
            return False

        if self.get_title_by_id(title_id) is None:
            return False

        self.player.equipped_title = title_id
        self.player.save_state()
        return True

    def get_equipped_title(self):
        title = self.get_title_by_id(self.player.equipped_title)

        if title is not None:
            return title

        return {
            "id": "",
            "name": "无称号",
            "desc": "还没有佩戴称号。",
            "bonus_type": "none",
            "bonus_value": 0
        }

    def get_title_name(self):
        return self.get_equipped_title().get("name", "无称号")

    def get_exp_bonus_rate(self):
        title = self.get_equipped_title()

        if title.get("bonus_type") != "exp_rate":
            return 0

        return title.get("bonus_value", 0)

    def get_energy_bonus_rate(self):
        title = self.get_equipped_title()

        if title.get("bonus_type") != "energy_change_rate":
            return 0

        return title.get("bonus_value", 0)

    def get_bonus_text(self):
        return self.get_title_bonus_text(self.get_equipped_title())

    def get_title_bonus_text(self, title):
        bonus_type = title.get("bonus_type")
        bonus_value = title.get("bonus_value", 0)

        if bonus_type == "exp_rate":
            return f"经验 +{int(bonus_value * 100)}%"

        if bonus_type == "energy_change_rate":
            return f"能量变化 +{int(bonus_value * 100)}%"

        if bonus_type == "positive_energy_rate":
            return f"正向行动能量收益 +{int(bonus_value * 100)}%"

        if bonus_type == "action_energy_rate":
            return (
                f"{bonus_value.get('action_id', '指定行动')}能量收益 "
                f"+{int(bonus_value.get('rate', 0) * 100)}%"
            )

        if bonus_type == "action_energy_cost_reduction":
            return (
                f"{bonus_value.get('action_id', '指定行动')}能量消耗 "
                f"-{int(bonus_value.get('rate', 0) * 100)}%"
            )

        if bonus_type == "negative_action_exp_rate":
            return f"娱乐行动经验 +{int(bonus_value * 100)}%"

        if bonus_type == "special_task_exp_rate":
            return f"特殊任务经验 +{int(bonus_value * 100)}%"

        if bonus_type == "outdoor_task_exp_rate":
            return f"户外任务经验 +{int(bonus_value * 100)}%"

        return "无加成"

    def get_title_condition_text(self, title):
        condition_type = title.get("condition_type")
        target_value = title.get("target_value")

        if condition_type == "always":
            return "默认解锁"

        if condition_type == "task_completed_count":
            return f"累计完成普通任务 {target_value} 次"

        if condition_type == "task_done_count":
            return f"完成任务 {target_value} 次"

        if condition_type == "energy_reach":
            return f"能量达到 {target_value}"

        if condition_type == "action_count":
            action_id, count = self.parse_action_count_target(title)
            return f"{action_id}累计完成 {count} 次"

        if condition_type == "action_combo_count":
            return "、".join(
                f"{item.get('action_id', '指定行动')} {item.get('count', 1)} 次"
                for item in target_value
            )

        if condition_type == "special_task_completed_count":
            return (
                f"完成特殊任务 {target_value.get('task_id')} "
                f"{target_value.get('count', 1)} 次"
            )

        if condition_type == "achievement_unlocked_count":
            return f"解锁成就 {target_value} 个"

        if condition_type == "timed_action_completed_count":
            return f"完成计时行动 {target_value} 次"

        if condition_type == "outdoor_task_completed_count":
            return f"累计完成户外相关任务 {target_value} 次"

        if condition_type == "shop_purchase":
            return f"在商店购买 {target_value}"

        return "未知条件"

    def apply_exp_bonus(self, exp):
        return self.apply_rate_bonus(exp, self.get_exp_bonus_rate())

    def apply_task_exp_bonus(self, exp, task_id=None, source="daily"):
        title = self.get_equipped_title()
        bonus_type = title.get("bonus_type")
        bonus_value = title.get("bonus_value", 0)

        if bonus_type == "exp_rate":
            return self.apply_rate_bonus(exp, bonus_value)

        if bonus_type == "special_task_exp_rate" and source == "special":
            return self.apply_rate_bonus(exp, bonus_value)

        if bonus_type == "outdoor_task_exp_rate" and self.is_outdoor_task(task_id, source):
            return self.apply_rate_bonus(exp, bonus_value)

        return exp

    def apply_action_exp_bonus(self, action_name, exp):
        title = self.get_equipped_title()

        if title.get("bonus_type") != "negative_action_exp_rate":
            return exp

        if action_name not in NEGATIVE_ACTION_IDS:
            return exp

        return self.apply_rate_bonus(exp, title.get("bonus_value", 0))

    def apply_action_energy_bonus(self, action_name, change):
        title = self.get_equipped_title()
        bonus_type = title.get("bonus_type")
        bonus_value = title.get("bonus_value", 0)

        if bonus_type == "energy_change_rate":
            return self.apply_signed_rate(change, bonus_value)

        if bonus_type == "positive_energy_rate" and change > 0:
            return self.apply_signed_rate(change, bonus_value)

        if bonus_type == "action_energy_rate" and change > 0:
            if bonus_value.get("action_id") == action_name:
                return self.apply_signed_rate(change, bonus_value.get("rate", 0))

        if bonus_type == "action_energy_cost_reduction" and change < 0:
            if bonus_value.get("action_id") == action_name:
                return self.apply_cost_reduction(change, bonus_value.get("rate", 0))

        return change

    def apply_energy_bonus(self, change):
        return self.apply_action_energy_bonus("", change)

    def apply_rate_bonus(self, value, rate):
        if rate <= 0 or value == 0:
            return value

        bonus = int(value * rate)

        if bonus == 0:
            bonus = 1

        return value + bonus

    def apply_signed_rate(self, change, rate):
        if rate <= 0 or change == 0:
            return change

        sign = 1 if change > 0 else -1
        return sign * int(abs(change) * (1 + rate) + 0.5)

    def apply_cost_reduction(self, change, rate):
        if rate <= 0 or change >= 0:
            return change

        return -int(abs(change) * (1 - rate) + 0.5)

    def is_outdoor_task(self, task_id, source):
        if source == "daily":
            return task_id in OUTDOOR_DAILY_TASK_IDS

        if source == "special":
            return task_id in OUTDOOR_SPECIAL_TASK_IDS

        return False

    def get_title_by_id(self, title_id):
        for title in self.titles:
            if title.get("id") == title_id:
                return title

        return None
