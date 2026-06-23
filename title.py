import json
import os


class Title:
    def __init__(self, player, title_file="titles.json"):
        self.player = player
        self.title_file = title_file
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
            action_name = title.get("target_action")

            if not action_name:
                return False

            count = self.player.action_counts.get(action_name, 0)
            return count >= target_value

        return False

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
        title = self.get_equipped_title()
        bonus_type = title.get("bonus_type")
        bonus_value = title.get("bonus_value", 0)

        if bonus_type == "exp_rate":
            return f"经验+{int(bonus_value * 100)}%"

        if bonus_type == "energy_change_rate":
            return f"能量变化+{int(bonus_value * 100)}%"

        return "无加成"

    def apply_exp_bonus(self, exp):
        bonus_rate = self.get_exp_bonus_rate()

        if bonus_rate <= 0:
            return exp

        bonus_exp = int(exp * bonus_rate)

        if bonus_exp == 0:
            bonus_exp = 1

        return exp + bonus_exp

    def apply_energy_bonus(self, change):
        bonus_rate = self.get_energy_bonus_rate()

        if bonus_rate <= 0 or change == 0:
            return change

        sign = 1 if change > 0 else -1
        bonus_change = int(abs(change) * (1 + bonus_rate) + 0.5)
        return sign * bonus_change

    def get_title_by_id(self, title_id):
        for title in self.titles:
            if title.get("id") == title_id:
                return title

        return None
