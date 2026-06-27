from repositories.player_repository import load_player_state


class Otaku:
    def __init__(self, config):
        self.max_energy = config["max_energy"]
        save_data = load_player_state(config)

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
