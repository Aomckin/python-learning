from core_event import ERROR, GameEvent
from core_types import OperationResult


def equip_title(core, title_id):
    if not core.title_system.equip_title(title_id):
        message = "称号不可佩戴"
        return OperationResult(
            False,
            message,
            events=[GameEvent(ERROR, {"message": message})],
            state=core.get_state(),
        )

    return OperationResult(True, "称号已佩戴", state=core.get_state())
