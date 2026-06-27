from utils.json_store import file_exists, load_json
from unlockable import UnlockableSystem


class AchievementSystem(UnlockableSystem):
    def __init__(
            self,
            player,
            achievement_file="achievements.json",
            level_system=None,
            daily_tasks_file="tasks.json",
            special_tasks_file="special_tasks.json"
    ):
        self.player = player
        self.achievement_file = achievement_file
        self.level_system = level_system
        self.daily_tasks_file = daily_tasks_file
        self.special_tasks_file = special_tasks_file
        super().__init__(player, achievement_file)
        self.achievement_file = self.data_file
        self.achievements = self.items

    def load_achievements(self):
        return self.load()

    def check_achievements(self):
        return self.check()

    def get_unlocked_ids(self):
        return getattr(self.player, "unlocked_achievements", [])

    def is_done(self, item, context=None):
        return self.is_achievement_done(item)

    def is_achievement_done(self, achievement):
        condition_type = achievement.get("condition_type")
        target_value = achievement.get("target_value")

        if condition_type == "energy_reach":
            if target_value is None:
                return False

            return self.player.energy >= target_value

        if condition_type == "task_done_count":
            if target_value is None:
                return False

            return getattr(self.player, "done_task_count", 0) >= target_value

        if condition_type == "special_task_done_count":
            if target_value is None:
                return False

            return getattr(self.player, "done_special_task_count", 0) >= target_value

        if condition_type == "action_count":
            action_name = achievement.get("target_action")

            if not action_name or target_value is None:
                return False

            count = getattr(self.player, "action_counts", {}).get(action_name, 0)
            return count >= target_value

        if condition_type == "total_action_count":
            if target_value is None:
                return False

            count = sum(getattr(self.player, "action_counts", {}).values())
            return count >= target_value

        if condition_type == "level":
            if target_value is None or self.level_system is None:
                return False

            return self.level_system.get_level(getattr(self.player, "exp", 0)) >= target_value

        if condition_type == "task_combo":
            return self.is_task_combo_done(achievement.get("requirements", []))

        return False

    def is_task_combo_done(self, requirements):
        if not requirements:
            return False

        daily_counts = self.load_task_completed_counts(self.daily_tasks_file)
        special_counts = self.load_task_completed_counts(self.special_tasks_file)

        for requirement in requirements:
            source = requirement.get("source")
            task_id = requirement.get("task_id")
            count = requirement.get("count", 1)

            if not task_id:
                return False

            if source == "daily":
                completed_count = daily_counts.get(task_id, 0)
            elif source == "special":
                completed_count = special_counts.get(task_id, 0)
            else:
                return False

            if completed_count < count:
                return False

        return True

    def load_task_completed_counts(self, task_file):
        if not file_exists(task_file):
            return {}

        task_data = load_json(task_file)

        return {
            task.get("id"): task.get("completed_count", 0)
            for task in task_data.get("tasks", [])
            if task.get("id")
        }

    def unlock_achievement(self, achievement):
        return self.unlock(achievement)


Achievement = AchievementSystem
