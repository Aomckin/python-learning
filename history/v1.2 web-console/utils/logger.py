from pathlib import Path

from utils.time_utils import get_now_str
from utils.paths import resolve_data_path


LOG_FILE = "log.txt"


def log_event(event_type, content):
    write_log_line([get_now_str(), event_type, content])


def log_action(action_name, energy_change, current_energy):
    write_log_line([
        get_now_str(),
        action_name,
        f"能量变化：{energy_change}",
        f"当前能量：{current_energy}",
    ])


def log_system(content):
    write_log_line([get_now_str(), "系统", content])


def log_abandon(action_name, elapsed_minutes):
    write_log_line([
        get_now_str(),
        f"放弃{action_name}",
        f"已进行 {elapsed_minutes}分钟",
    ])


def log_timed_action(action_name, duration_minutes, energy_change, exp_change, current_energy):
    parts = [
        get_now_str(),
        f"完成{action_name}{duration_minutes}分钟",
        f"能量 {energy_change:+}",
    ]

    if exp_change:
        parts.append(f"经验 +{exp_change}")

    parts.append(f"当前能量 {current_energy}")
    write_log_line(parts)


def load_recent_logs(limit=10):
    path = resolve_data_path(LOG_FILE)

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f][-limit:]


def write_log_line(parts):
    with open(resolve_data_path(LOG_FILE), "a", encoding="utf-8") as f:
        f.write("|".join(str(part) for part in parts) + "\n")
