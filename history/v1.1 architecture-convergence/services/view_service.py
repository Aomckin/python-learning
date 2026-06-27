from core_types import GameState
from repositories.player_repository import load_player_logs
from services.player_service import (
    get_coin,
    get_energy,
    get_equipped_title_id,
    get_exp,
    get_max_energy,
    get_unlocked_achievement_ids,
    get_unlocked_title_ids,
)


def build_game_state(core):
    title_name = core.title_system.get_title_name()
    bonus_text = core.title_system.get_bonus_text()
    energy = get_energy(core.player)
    max_energy = get_max_energy(core.player)
    coin = get_coin(core.player)
    return GameState(
        window_title=core.config["window_title"],
        window_size=core.config["window_size"],
        energy_text=f"宅宅能量：{energy}/{max_energy}",
        energy_value=energy,
        energy_max=max_energy,
        exp_text=core.level_system.get_exp_text(get_exp(core.player)),
        level_text=core.level_system.get_level_text(get_exp(core.player)),
        coin_text=f"金币：{coin}",
        title_text=f"称号：{title_name} {bonus_text}",
        logs=load_player_logs(),
        action_views=build_action_views(core.actions),
        active_task_views=build_daily_task_views(core.task_manager.tasks),
        active_special_task_views=build_special_task_views(
            core.special_task_manager.tasks
        ),
        shop_category_views=build_shop_category_views(core),
        achievement_sections=build_achievement_sections(core),
        title_views=build_title_views(core),
    )


def build_action_views(actions):
    return [
        {
            "name": action_name,
            "energy_change": action_info["energy_change"],
            "button_text": f"{action_name} {action_info['energy_change']:+}",
            "group": (
                "positive"
                if action_info["energy_change"] > 0
                else "negative"
            ),
            "duration_options_source": action_info,
            "command_payload": {"action_name": action_name},
        }
        for action_name, action_info in actions.items()
    ]


def build_daily_task_views(tasks):
    return [
        {
            "id": task.id,
            "name": task.name,
            "detail_text": (
                f"能量 {task.reward:+} / EXP +{task.exp} / "
                f"{'已完成' if task.done else '未完成'}"
            ),
            "button_text": "已完成" if task.done else "完成",
            "button_state": "disabled" if task.done else "normal",
            "command_payload": {"index": index},
        }
        for index, task in enumerate(tasks)
    ]


def build_special_task_views(tasks):
    return [
        {
            "id": task.id,
            "name": task.name,
            "detail_text": (
                f"金币 +{task.coin} / EXP +{task.exp} / "
                f"{'已完成' if task.done else '未完成'}"
            ),
            "button_text": "已完成" if task.done else "完成",
            "button_state": "disabled" if task.done else "normal",
            "command_payload": {"index": index},
        }
        for index, task in enumerate(tasks)
    ]


def build_shop_category_views(core):
    shop_item_views = build_shop_item_views(core)
    return [
        {
            "category": category,
            "items": [
                item_view for item_view in shop_item_views
                if item_view.get("category") == category
            ],
        }
        for category in core.shop_manager.categories
    ]


def build_shop_item_views(core):
    return [
        {
            "id": item.get("id"),
            "name": item.get("name", "未知商品"),
            "desc": item.get("desc", ""),
            "price": item.get("price", 0),
            "category": item.get("category"),
            "stock_text": core.shop_manager.get_stock_text(item),
            "button_text": core.shop_manager.get_button_state_text(item),
            "button_state": (
                "normal"
                if core.shop_manager.can_buy(item.get("id"))
                else "disabled"
            ),
            "command_payload": {"item_id": item.get("id")},
        }
        for item in core.shop_manager.items
    ]


def build_achievement_sections(core):
    unlocked_ids = get_unlocked_achievement_ids(core.player)
    unlocked = []
    locked = []

    for achievement in core.achievement_manager.achievements:
        view = build_achievement_list_view(
            achievement,
            achievement.get("id") in unlocked_ids
        )
        if view["section"] == "unlocked":
            unlocked.append(view)
        else:
            locked.append(view)

    return [
        {
            "id": "unlocked",
            "title": "已获取",
            "empty_text": "暂时还没有获取成就。",
            "items": unlocked,
        },
        {
            "id": "locked",
            "title": "未获取",
            "empty_text": "所有成就都已获取。",
            "items": locked,
        },
    ]


def build_title_views(core):
    unlocked_ids = get_unlocked_title_ids(core.player)
    equipped_id = get_equipped_title_id(core.player)
    return [
        build_title_list_view(
            title,
            core.title_system,
            title.get("id", "") in unlocked_ids,
            title.get("id", "") == equipped_id,
        )
        for title in core.title_system.titles
    ]


def build_achievement_event_view(achievement):
    return {
        "id": achievement.get("id"),
        "name": achievement.get("name", achievement.get("id", "未知成就")),
        "desc": achievement.get("desc", ""),
        "reward_text": get_achievement_reward_text(achievement),
        "display_text": get_achievement_display_text(achievement),
    }


def build_achievement_list_view(achievement, unlocked):
    view = build_achievement_event_view(achievement)
    view["condition_text"] = get_achievement_condition_text(achievement)
    view["section"] = "unlocked" if unlocked else "locked"
    return view


def build_title_event_view(title, title_system):
    name = title.get("name", title.get("id", "未知称号"))
    desc = title.get("desc", "")
    condition = title_system.get_title_condition_text(title)
    bonus = title_system.get_title_bonus_text(title)
    return {
        "id": title.get("id", ""),
        "name": name,
        "desc": desc,
        "condition_text": condition,
        "bonus_text": bonus,
        "display_text": (
            f"【{name}】\n"
            f"{desc}\n"
            f"条件：{condition}\n"
            f"效果：{bonus}"
        ),
    }


def build_title_list_view(title, title_system, unlocked, equipped):
    view = build_title_event_view(title, title_system)
    status_text = "已佩戴" if equipped else ("已解锁" if unlocked else "未解锁")
    view["section"] = "unlocked" if unlocked else "locked"
    view["status_text"] = status_text
    view["display_text"] = (
        f"【{view['name']}】 {status_text}\n"
        f"{view['desc']}\n"
        f"条件：{view['condition_text']}\n"
        f"效果：{view['bonus_text']}"
    )
    view["button_text"] = "已佩戴" if equipped else ("佩戴" if unlocked else "未解锁")
    view["button_state"] = "normal" if unlocked and not equipped else "disabled"
    view["command_payload"] = {"title_id": view["id"]}
    return view


def get_achievement_display_text(achievement):
    name = achievement.get("name", achievement.get("id", "未知成就"))
    desc = achievement.get("desc", "")
    condition = get_achievement_condition_text(achievement)

    return (
        f"【{name}】\n"
        f"{desc}\n"
        f"条件：{condition}\n"
        f"奖励：{get_achievement_reward_text(achievement)}"
    )


def get_achievement_reward_text(achievement):
    rewards = []
    reward_coin = achievement.get("reward_coin", 0)
    reward_exp = achievement.get("reward_exp", 0)

    if reward_coin:
        rewards.append(f"金币 +{reward_coin}")

    if reward_exp:
        rewards.append(f"EXP +{reward_exp}")

    if len(rewards) == 0:
        return "无"

    return " ".join(rewards)


def get_achievement_condition_text(achievement):
    condition_type = achievement.get("condition_type")
    target_value = achievement.get("target_value")

    if condition_type == "energy_reach":
        return f"能量达到 {target_value}"

    if condition_type == "task_done_count":
        return f"完成任务 {target_value} 次"

    if condition_type == "action_count":
        action_name = achievement.get("target_action", "指定行动")
        return f"{action_name} {target_value} 次"

    if condition_type == "total_action_count":
        return f"执行任意行动 {target_value} 次"

    if condition_type == "special_task_done_count":
        return f"完成特殊任务 {target_value} 次"

    if condition_type == "level":
        return f"达到 Lv.{target_value}"

    if condition_type == "task_combo":
        return "完成指定普通任务与特殊任务组合"

    return "未知条件"
