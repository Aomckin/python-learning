from repositories.player_repository import save_player_state
from services.player_service import (
    add_coin,
    add_exp,
    equip_title,
    get_equipped_title_id,
    get_exp,
    unlock_achievement,
    unlock_title,
)
from services.view_service import build_achievement_event_view, build_title_event_view


def check_achievement(core):
    unlocked = core.achievement_manager.check_achievements()

    for achievement in unlocked:
        unlock_achievement(core.player, achievement.get("id"))
        add_coin(core.player, achievement.get("reward_coin", 0))
        add_exp(core.player, achievement.get("reward_exp", 0))

    if unlocked:
        save_player_state(core.player)

    return [
        build_achievement_event_view(achievement)
        for achievement in unlocked
    ]


def check_title(core):
    unlocked = core.title_system.check_titles(core.task_manager.all_tasks)
    should_auto_equip = not get_equipped_title_id(core.player)

    for title in unlocked:
        title_id = title.get("id")
        unlock_title(core.player, title_id)
        if should_auto_equip and title_id:
            equip_title(core.player, title_id)
            should_auto_equip = False

    if unlocked:
        save_player_state(core.player)

    return [
        build_title_event_view(title, core.title_system)
        for title in unlocked
    ]


def check_level_up(core, before_exp):
    return core.level_system.get_level_up_info(before_exp, get_exp(core.player))
