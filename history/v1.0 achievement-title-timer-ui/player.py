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
        self.shop_daily_purchases = save_data.get("shop_daily_purchases", {})
        self.shop_total_purchases = save_data.get("shop_total_purchases", {})
        self.daily_double_exp_date = save_data.get("daily_double_exp_date", "")
        self.special_task_slots = save_data.get("special_task_slots", 1)
        self.unlocked_titles = save_data.get("unlocked_titles", [])
        self.equipped_title = save_data.get("equipped_title", "")
        self.completed_timed_actions = save_data.get("completed_timed_actions", 0)

    def do_action(self, action_name, actions, energy_bonus_rate=0):
        action = actions[action_name]
        change = action["energy_change"]
        change = self.apply_energy_bonus(change, energy_bonus_rate)

        self.energy += change
        self.energy = max(0, min(self.config["max_energy"], self.energy))

        self.action_counts[action_name] = (
            self.action_counts.get(action_name, 0) + 1
        )
        self.completed_timed_actions += 1

        self.save_state()
        self.save_log(action_name, change)

    def complete_timed_action(
            self,
            action_name,
            actions,
            duration_minutes,
            energy_multiplier,
            exp_reward,
            energy_bonus_rate=0,
            energy_change_override=None
    ):
        action = actions[action_name]
        base_change = action["energy_change"]
        if energy_change_override is None:
            energy_change = round(base_change * energy_multiplier)
            energy_change = self.apply_energy_bonus(energy_change, energy_bonus_rate)
        else:
            energy_change = energy_change_override

        self.energy += energy_change
        self.energy = max(0, min(self.config["max_energy"], self.energy))
        self.exp += exp_reward

        self.action_counts[action_name] = (
            self.action_counts.get(action_name, 0) + 1
        )

        self.save_state()
        self.save_timed_action_log(
            action_name,
            duration_minutes,
            energy_change,
            exp_reward
        )

        return {
            "action_name": action_name,
            "duration_minutes": duration_minutes,
            "energy_change": energy_change,
            "exp_change": exp_reward,
            "current_energy": self.energy
        }

    def apply_energy_bonus(self, change, energy_bonus_rate=0):
        if energy_bonus_rate > 0 and change != 0:
            sign = 1 if change > 0 else -1
            return sign * int(abs(change) * (1 + energy_bonus_rate) + 0.5)

        return change

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
                "shop_daily_purchases": {},
                "shop_total_purchases": {},
                "daily_double_exp_date": "",
                "special_task_slots": 1,
                "unlocked_titles": [],
                "equipped_title": "",
                "completed_timed_actions": 0
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

    def save_timed_action_log(self, action_name, duration_minutes, energy_change, exp_change):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        parts = [
            now,
            f"完成{action_name}{duration_minutes}分钟",
            f"能量 {energy_change:+}"
        ]

        if exp_change:
            parts.append(f"经验 +{exp_change}")

        parts.append(f"当前能量 {self.energy}")

        with open("log.txt", "a", encoding="utf-8") as f:
            f.write("|".join(parts) + "\n")

    def save_abandoned_action_log(self, action_name, elapsed_minutes):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(f"{now}|放弃{action_name}|已进行 {elapsed_minutes}分钟\n")

    def save_state(self):
        data = {
            "energy": self.energy,
            "exp": self.exp,
            "unlocked_achievements": self.unlocked_achievements,
            "action_counts": self.action_counts,
            "done_task_count": self.done_task_count,
            "done_special_task_count": self.done_special_task_count,
            "coin": self.coin,
            "shop_daily_purchases": self.shop_daily_purchases,
            "shop_total_purchases": self.shop_total_purchases,
            "daily_double_exp_date": self.daily_double_exp_date,
            "special_task_slots": self.special_task_slots,
            "unlocked_titles": self.unlocked_titles,
            "equipped_title": self.equipped_title,
            "completed_timed_actions": self.completed_timed_actions
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

    def spend_coin(self, amount):
        if self.coin < amount:
            return False

        self.coin -= amount
        self.save_state()
        return True
