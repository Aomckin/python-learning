from core_types import OperationResult
from core_event import ERROR, SHOP_PURCHASE, GameEvent
from repositories.player_repository import log_player_action, save_player_state
from services.player_service import (
    apply_shop_effect,
    get_energy,
    get_special_task_slots,
    record_shop_purchase,
    spend_coin,
)


def buy_shop_item(core, item_id):
    result = validate_purchase(core, item_id)

    if not result.get("success"):
        message = result.get("message", "购买失败")
        return OperationResult(
            False,
            message,
            events=[GameEvent(ERROR, {"message": message})],
            state=core.get_state()
        )

    item = result["item"]
    log_player_action(
        f"购买商品：{item.get('name', item_id)}",
        f"金币-{item.get('price', 0)}",
        get_energy(core.player)
    )

    effect_type = result.get("effect_type")
    if effect_type == "refresh_daily_tasks":
        core.task_manager.redraw_daily_tasks()

    if effect_type == "special_task_slot":
        core.special_task_manager.set_slot_count(
            get_special_task_slots(core.player)
        )

    return OperationResult(
        True,
        result.get("message", "购买成功"),
        events=[
            GameEvent(
                SHOP_PURCHASE,
                {"item": item, "effect_type": effect_type}
            )
        ],
        state=core.get_state()
    )


def validate_purchase(core, item_id):
    item = core.shop_manager.get_item(item_id)

    if item is None:
        return {"success": False, "message": "商品不存在"}

    if not core.shop_manager.is_unlocked(item):
        return {"success": False, "message": "商品未解禁"}

    if core.shop_manager.is_sold_out(item):
        return {"success": False, "message": "商品已达购买上限"}

    price = item.get("price", 0)
    if not spend_coin(core.player, price):
        return {"success": False, "message": "金币不足"}

    today = core.shop_manager.today_func()
    record_shop_purchase(core.player, item, today)
    apply_shop_effect(core.player, item, today)
    save_player_state(core.player)

    return {
        "success": True,
        "message": "购买成功",
        "item": item,
        "effect_type": item.get("effect_type"),
        "effect_value": item.get("effect_value", 0),
    }
