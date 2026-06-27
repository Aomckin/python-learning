class GameEvent:
    def __init__(self, event_type: str, payload: dict = None):
        self.type = event_type
        self.payload = payload or {}


LEVEL_UP = "LEVEL_UP"
ACHIEVEMENT_UNLOCK = "ACHIEVEMENT_UNLOCK"
TITLE_UNLOCK = "TITLE_UNLOCK"
ACTION_COMPLETE = "ACTION_COMPLETE"
TASK_COMPLETE = "TASK_COMPLETE"
SHOP_PURCHASE = "SHOP_PURCHASE"
ERROR = "ERROR"
