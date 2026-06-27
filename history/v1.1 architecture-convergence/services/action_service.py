from core_types import OperationResult
from core_event import ACTION_COMPLETE, ERROR, GameEvent
from repositories.player_repository import (
    log_player_action,
    log_player_timed_action,
    save_player_state,
)
from services.player_service import (
    complete_action as service_complete_player_action,
    complete_timed_action as service_complete_player_timed_action,
    get_energy,
    get_exp,
)
from services.progression_service import result_with_progression


def complete_action_now(core, action_name):
    if action_name not in core.actions:
        return OperationResult(
            False,
            "行动不存在",
            events=[GameEvent(ERROR, {"message": "行动不存在"})],
            state=core.get_state()
        )

    before_exp = get_exp(core.player)
    base_change = core.actions[action_name]["energy_change"]
    final_change = core.title_system.apply_action_energy_bonus(
        action_name,
        base_change
    )
    service_complete_player_action(core.player, action_name, final_change)
    save_player_state(core.player)
    log_player_action(
        f"执行行动：{action_name}",
        f"能量{final_change:+}",
        get_energy(core.player)
    )

    return result_with_progression(core, True, "行动完成", before_exp)


def complete_timed_action(core, action_name, option):
    if action_name not in core.actions:
        return OperationResult(
            False,
            "行动不存在",
            events=[GameEvent(ERROR, {"message": "行动不存在"})],
            state=core.get_state()
        )

    before_exp = get_exp(core.player)
    base_change = round(
        core.actions[action_name]["energy_change"] * option.multiplier
    )
    final_energy_change = core.title_system.apply_action_energy_bonus(
        action_name,
        base_change
    )
    final_exp = core.title_system.apply_action_exp_bonus(
        action_name,
        option.exp
    )
    action_result = service_complete_player_timed_action(
        core.player,
        action_name,
        option.minutes,
        final_energy_change,
        final_exp
    )
    save_player_state(core.player)
    log_player_timed_action(
        action_name,
        option.minutes,
        final_energy_change,
        final_exp,
        action_result["current_energy"]
    )

    return result_with_progression(
        core,
        True,
        "行动完成",
        before_exp,
        events=[GameEvent(ACTION_COMPLETE, {"action_result": action_result})]
    )
