from core_types import OperationResult
from core_event import (
    ACHIEVEMENT_UNLOCK,
    LEVEL_UP,
    TITLE_UNLOCK,
    GameEvent,
)
from services.achievement_service import (
    check_achievement,
    check_level_up,
    check_title,
)


def collect_progression(core, before_exp):
    unlocked_achievements = check_achievement(core)
    unlocked_titles = check_title(core)
    level_up_info = check_level_up(core, before_exp)

    return unlocked_achievements, unlocked_titles, level_up_info


def result_with_progression(
        core,
        success,
        message,
        before_exp,
        events=None
):
    unlocked_achievements, unlocked_titles, level_up_info = collect_progression(
        core,
        before_exp
    )
    result_events = list(events or [])
    for achievement in unlocked_achievements:
        result_events.append(
            GameEvent(ACHIEVEMENT_UNLOCK, {"achievement": achievement})
        )
    for title in unlocked_titles:
        result_events.append(GameEvent(TITLE_UNLOCK, {"title": title}))
    if level_up_info:
        result_events.append(
            GameEvent(LEVEL_UP, {"level_up_info": level_up_info})
        )

    return OperationResult(
        success,
        message,
        events=result_events,
        state=core.get_state()
    )
