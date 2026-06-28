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


def get_action_exp_change(action_info):
    exp_change = action_info.get("exp_change", 0)
    if isinstance(exp_change, (int, float)) and exp_change >= 0:
        return exp_change

    return 0


def can_apply_energy_change(core, energy_change):
    return energy_change >= 0 or get_energy(core.player) + energy_change >= 0


def energy_not_enough_result(core):
    message = "能量不足"
    return OperationResult(
        False,
        message,
        events=[GameEvent(ERROR, {"message": message})],
        state=core.get_state()
    )


def complete_action_now(core, action_name):
    if action_name not in core.actions:
        return OperationResult(
            False,
            "行动不存在",
            events=[GameEvent(ERROR, {"message": "行动不存在"})],
            state=core.get_state()
        )

    before_exp = get_exp(core.player)
    action_info = core.actions[action_name]
    base_change = action_info["energy_change"]
    final_change = core.title_system.apply_action_energy_bonus(
        action_name,
        base_change
    )
    if not can_apply_energy_change(core, final_change):
        return energy_not_enough_result(core)

    final_exp = get_action_exp_change(action_info)
    service_complete_player_action(
        core.player,
        action_name,
        final_change,
        final_exp
    )
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
    option = core.get_duration_option(action_name, option)
    if option is None:
        message = "时长选项无效"
        return OperationResult(
            False,
            message,
            events=[GameEvent(ERROR, {"message": message})],
            state=core.get_state()
        )

    action_info = core.actions[action_name]
    base_change = round(
        action_info["energy_change"] * option.multiplier
    )
    final_energy_change = core.title_system.apply_action_energy_bonus(
        action_name,
        base_change
    )
    if not can_apply_energy_change(core, final_energy_change):
        return energy_not_enough_result(core)

    final_exp = round(get_action_exp_change(action_info) * option.multiplier)
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
