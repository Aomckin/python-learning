from utils.json_store import file_exists, load_json, save_json
from utils.logger import (
    load_recent_logs,
    log_abandon,
    log_action,
    log_timed_action,
)


def get_default_save_data(config):
    return {
        "energy": config["default_energy"],
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
        "completed_timed_actions": 0,
    }


def load_player_state(config):
    if not file_exists("save.json"):
        return get_default_save_data(config)

    return load_json("save.json")


def save_player_state(player):
    save_json("save.json", serialize_player_state(player))


def serialize_player_state(player):
    return {
        "energy": player.energy,
        "exp": getattr(player, "exp", 0),
        "unlocked_achievements": getattr(player, "unlocked_achievements", []),
        "action_counts": getattr(player, "action_counts", {}),
        "done_task_count": getattr(player, "done_task_count", 0),
        "done_special_task_count": getattr(player, "done_special_task_count", 0),
        "coin": getattr(player, "coin", 0),
        "shop_daily_purchases": getattr(player, "shop_daily_purchases", {}),
        "shop_total_purchases": getattr(player, "shop_total_purchases", {}),
        "daily_double_exp_date": getattr(player, "daily_double_exp_date", ""),
        "special_task_slots": getattr(player, "special_task_slots", 1),
        "unlocked_titles": getattr(player, "unlocked_titles", []),
        "equipped_title": getattr(player, "equipped_title", ""),
        "completed_timed_actions": getattr(player, "completed_timed_actions", 0),
    }


def load_player_logs():
    return load_recent_logs()


def log_player_action(action, change, current_energy):
    log_action(action, change, current_energy)


def log_player_timed_action(
        action_name,
        duration_minutes,
        energy_change,
        exp_change,
        current_energy
):
    log_timed_action(
        action_name,
        duration_minutes,
        energy_change,
        exp_change,
        current_energy
    )


def log_player_abandon(action_name, elapsed_minutes):
    log_abandon(action_name, elapsed_minutes)
