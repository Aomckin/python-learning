from datetime import datetime
import json


class Otaku:
    def __init__(self, config):
        self.config = config
        save_data = self.load_save()

        self.energy = save_data["energy"]
        self.exp = save_data.get("exp", 0)

        self.unlocked_achievements = save_data.get("unlocked_achievements", [])
        self.action_counts = save_data.get("action_counts", {})
        self.done_task_count = save_data.get("done_task_count", 0)
        self.done_special_task_count = save_data.get("done_special_task_count", 0)
        self.coin = save_data.get("coin", 0)
        self.unlocked_titles = save_data.get("unlocked_titles", [])
        self.equipped_title = save_data.get("equipped_title", "")

    def do_action(self, action_name, actions, energy_bonus_rate=0):
        action = actions[action_name]
        change = action["energy_change"]

        if energy_bonus_rate > 0 and change != 0:
            sign = 1 if change > 0 else -1
            change = sign * int(abs(change) * (1 + energy_bonus_rate) + 0.5)

        self.energy += change
        self.energy = max(0, min(self.config["max_energy"], self.energy))

        self.action_counts[action_name] = (
            self.action_counts.get(action_name, 0) + 1
        )

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
                "done_task_count": 0,
                "done_special_task_count": 0,
                "coin": 0,
                "unlocked_titles": [],
                "equipped_title": ""
            }

    def load_log(self):
        try:
            with open("log.txt", "r", encoding="utf-8") as f:
                return [line.strip() for line in f][-10:]
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
            "unlocked_achievements": self.unlocked_achievements,
            "action_counts": self.action_counts,
            "done_task_count": self.done_task_count,
            "done_special_task_count": self.done_special_task_count,
            "coin": self.coin,
            "unlocked_titles": self.unlocked_titles,
            "equipped_title": self.equipped_title
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

    def add_special_reward(self, coin, exp, task_name):
        self.coin += coin
        self.exp += exp
        self.done_special_task_count += 1

        self.save_state()
        self.save_log(
            f"完成特殊任务：{task_name}",
            f"金币+{coin} 经验+{exp}"
        )
