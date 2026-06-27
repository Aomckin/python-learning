from core_types import OperationResult
from core_event import ERROR, TASK_COMPLETE, GameEvent
from repositories.player_repository import log_player_action, save_player_state
from services.player_service import (
    get_energy,
    get_exp,
    grant_daily_task_reward,
    grant_special_task_reward,
)
from services.progression_service import result_with_progression


def complete_daily_task(core, index):
    if index < 0 or index >= len(core.task_manager.tasks):
        return OperationResult(
            False,
            "任务不存在",
            events=[GameEvent(ERROR, {"message": "任务不存在"})],
            state=core.get_state()
        )

    task = core.task_manager.tasks[index]
    before_exp = get_exp(core.player)
    reward, exp = core.task_manager.finish_task(index)

    if reward > 0 or exp > 0:
        final_reward = core.title_system.apply_energy_bonus(reward)
        final_exp = apply_task_exp_bonus(core, exp, task.id, "daily")
        grant_daily_task_reward(core.player, final_reward, final_exp, task.name)
        save_player_state(core.player)
        log_player_action(
            f"完成任务：{task.name}",
            f"能量+{final_reward} 经验+{final_exp}",
            get_energy(core.player)
        )

    return result_with_progression(
        core,
        True,
        "任务完成",
        before_exp,
        events=[GameEvent(TASK_COMPLETE, {"task": task, "source": "daily"})]
    )


def complete_special_task(core, index):
    if index < 0 or index >= len(core.special_task_manager.tasks):
        return OperationResult(
            False,
            "特殊任务不存在",
            events=[GameEvent(ERROR, {"message": "特殊任务不存在"})],
            state=core.get_state()
        )

    task = core.special_task_manager.tasks[index]
    before_exp = get_exp(core.player)
    coin, exp = core.special_task_manager.finish_task(index)

    if coin > 0 or exp > 0:
        final_exp = apply_task_exp_bonus(core, exp, task.id, "special")
        grant_special_task_reward(core.player, coin, final_exp, task.name)
        save_player_state(core.player)
        log_player_action(
            f"完成特殊任务：{task.name}",
            f"金币+{coin} 经验+{final_exp}",
            get_energy(core.player)
        )

    return result_with_progression(
        core,
        True,
        "特殊任务完成",
        before_exp,
        events=[GameEvent(TASK_COMPLETE, {"task": task, "source": "special"})]
    )


def refresh_daily_tasks(core):
    core.task_manager.redraw_daily_tasks()
    return OperationResult(True, "每日任务已刷新", state=core.get_state())


def apply_task_exp_bonus(core, exp, task_id=None, source="daily"):
    final_exp = core.title_system.apply_task_exp_bonus(exp, task_id, source)
    final_exp *= core.shop_manager.get_task_exp_multiplier()

    return final_exp
