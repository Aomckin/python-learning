import json
import os


class Achievement:
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
            achievement_id = achievement.get("id")

            if not achievement_id:
                continue

            if achievement_id in self.player.unlocked_achievements:
                continue

            if self.is_achievement_done(achievement):
                self.unlock_achievement(achievement)
                unlocked.append(achievement)

        if unlocked:
            self.player.save_state()

        return unlocked

    def is_achievement_done(self, achievement):
        condition_type = achievement.get("condition_type")
        target_value = achievement.get("target_value")

        if target_value is None:
            return False

        if condition_type == "energy_reach":
            return self.player.energy >= target_value

        if condition_type == "task_done_count":
            return self.player.done_task_count >= target_value

        if condition_type == "action_count":
            action_name = achievement.get("target_action")

            if not action_name:
                return False

            count = self.player.action_counts.get(action_name, 0)
            return count >= target_value

        return False

    def unlock_achievement(self, achievement):
        achievement_id = achievement.get("id")

        if not achievement_id:
            return

        self.player.unlocked_achievements.append(achievement_id)

        reward_exp = achievement.get("reward_exp", 0)
        self.player.exp += reward_exp
