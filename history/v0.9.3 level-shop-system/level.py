import json


class Level:
    def __init__(self, level_file="level.json"):
        self.level_file = level_file
        self.config = self.load_config()

    def load_config(self):
        with open(self.level_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_status(self, total_exp):
        level = self.config["initial_level"]
        max_level = self.config["max_level"]
        remaining_exp = total_exp

        while level < max_level:
            required_exp = self.get_required_exp(level)

            if remaining_exp < required_exp:
                return {
                    "level": level,
                    "current_exp": remaining_exp,
                    "required_exp": required_exp,
                    "is_max_level": False
                }

            remaining_exp -= required_exp
            level += 1

        return {
            "level": max_level,
            "current_exp": 0,
            "required_exp": 0,
            "is_max_level": True
        }

    def get_required_exp(self, level):
        base_required_exp = self.config["base_required_exp"]
        step_levels = self.config["step_levels"]
        step_increase_exp = self.config["step_increase_exp"]
        step_index = (level - self.config["initial_level"]) // step_levels

        return base_required_exp + step_index * step_increase_exp

    def get_level(self, total_exp):
        return self.get_status(total_exp)["level"]

    def get_exp_text(self, total_exp):
        status = self.get_status(total_exp)

        if status["is_max_level"]:
            return "经验：满级"

        return f"经验：{status['current_exp']}/{status['required_exp']}"

    def get_level_text(self, total_exp):
        status = self.get_status(total_exp)
        return f"等级：Lv.{status['level']}"

    def get_level_up_info(self, before_exp, after_exp):
        before_level = self.get_level(before_exp)
        after_level = self.get_level(after_exp)

        if after_level <= before_level:
            return None

        return {
            "before_level": before_level,
            "after_level": after_level
        }
