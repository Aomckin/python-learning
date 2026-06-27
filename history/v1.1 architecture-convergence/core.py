import sys

import core_command
import core_event
from achievement import Achievement
from core_types import ActionDurationOption, OperationResult
from core_command import (
    BUY_SHOP_ITEM,
    COMPLETE_ACTION,
    COMPLETE_DAILY_TASK,
    COMPLETE_SPECIAL_TASK,
    COMPLETE_TIMED_ACTION,
    EQUIP_TITLE,
    INITIALIZE_PROGRESSION,
    LOG_ABANDONED_ACTION,
    REFRESH_DAILY_TASKS,
)
from core_event import ERROR, GameEvent
from level import Level
from player import Otaku
from services.action_service import (
    complete_action_now as service_complete_action_now,
    complete_timed_action as service_complete_timed_action,
)
from services.progression_service import (
    collect_progression,
    result_with_progression,
)
from services.shop_service import buy_shop_item as service_buy_shop_item
from services.task_service import (
    apply_task_exp_bonus as service_apply_task_exp_bonus,
    complete_daily_task as service_complete_daily_task,
    complete_special_task as service_complete_special_task,
    refresh_daily_tasks as service_refresh_daily_tasks,
)
from services.title_service import equip_title as service_equip_title
from services.view_service import build_game_state
from services.player_service import get_exp, get_special_task_slots
from shop import ShopManager
from task import SpecialTaskManager, TaskManager
from title import Title
from utils.json_store import load_json
from repositories.player_repository import log_player_abandon


sys.modules.setdefault("core.command", core_command)
sys.modules.setdefault("core.event", core_event)


POSITIVE_ACTION_OPTIONS = [
    ActionDurationOption(minutes=25, multiplier=1, exp=0),
    ActionDurationOption(minutes=45, multiplier=1.5, exp=0),
    ActionDurationOption(minutes=60, multiplier=2, exp=0),
]

NEGATIVE_ACTION_OPTIONS = [
    ActionDurationOption(minutes=30, multiplier=1, exp=1),
    ActionDurationOption(minutes=60, multiplier=1.5, exp=2),
    ActionDurationOption(minutes=90, multiplier=2, exp=3),
]


def get_action_duration_options(action_info):
    energy_change = action_info.get("energy_change", 0)

    if energy_change >= 0:
        return POSITIVE_ACTION_OPTIONS

    return NEGATIVE_ACTION_OPTIONS


class ActionTimerState:
    def __init__(self, action_name, duration_minutes, total_seconds=None):
        self.action_name = action_name
        self.duration_minutes = duration_minutes
        self.total_seconds = (
            total_seconds
            if total_seconds is not None
            else duration_minutes * 60
        )
        self.remaining_seconds = self.total_seconds
        self.paused = False
        self.cancelled = False

    def tick(self):
        if self.paused or self.cancelled or self.is_finished():
            return False

        self.remaining_seconds -= 1
        return True

    def pause(self):
        self.paused = True

    def resume(self):
        if not self.cancelled:
            self.paused = False

    def cancel(self):
        self.cancelled = True
        self.paused = False

    def is_finished(self):
        return self.remaining_seconds <= 0

    def elapsed_minutes(self):
        elapsed_seconds = self.total_seconds - self.remaining_seconds
        return elapsed_seconds // 60

    def format_remaining(self):
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"


class GameCore:
    def __init__(self, today_func=None):
        self.config = self.load_config()
        self.actions = self.load_actions()
        self.player = Otaku(self.config)
        self.task_manager = TaskManager()
        self.special_task_manager = SpecialTaskManager(
            get_special_task_slots(self.player)
        )
        self.level_system = Level()
        self.title_system = Title(self.player)
        self.achievement_manager = Achievement(
            self.player,
            level_system=self.level_system
        )
        self.shop_manager = ShopManager(self.player, today_func=today_func)

    def load_config(self):
        config = load_json("config.json")

        config.setdefault("theme", "default")
        return config

    def load_actions(self):
        return load_json("actions.json")

    def get_state(self):
        return build_game_state(self)

    def execute(self, command):
        payload = command.payload

        if command.type == INITIALIZE_PROGRESSION:
            return self.initialize_progression()

        if command.type == COMPLETE_ACTION:
            return self.complete_action_now(payload.get("action_name"))

        if command.type == COMPLETE_TIMED_ACTION:
            return self.complete_timed_action(
                payload.get("action_name"),
                payload.get("option")
            )

        if command.type == COMPLETE_DAILY_TASK:
            return self.complete_daily_task(payload.get("index", -1))

        if command.type == COMPLETE_SPECIAL_TASK:
            return self.complete_special_task(payload.get("index", -1))

        if command.type == BUY_SHOP_ITEM:
            return self.buy_shop_item(payload.get("item_id"))

        if command.type == EQUIP_TITLE:
            return self.equip_title(payload.get("title_id"))

        if command.type == REFRESH_DAILY_TASKS:
            return self.refresh_daily_tasks()

        if command.type == LOG_ABANDONED_ACTION:
            self.log_abandoned_action(
                payload.get("action_name"),
                payload.get("elapsed_minutes", 0)
            )
            return OperationResult(True, "已记录放弃行动", state=self.get_state())

        message = "未知指令"
        return OperationResult(
            False,
            message,
            events=[GameEvent(ERROR, {"message": message})],
            state=self.get_state()
        )

    def initialize_progression(self):
        return result_with_progression(
            self,
            True,
            "",
            get_exp(self.player)
        )

    def complete_action_now(self, action_name):
        return service_complete_action_now(self, action_name)

    def complete_timed_action(self, action_name, option):
        return service_complete_timed_action(self, action_name, option)

    def complete_daily_task(self, index):
        return service_complete_daily_task(self, index)

    def complete_special_task(self, index):
        return service_complete_special_task(self, index)

    def buy_shop_item(self, item_id):
        return service_buy_shop_item(self, item_id)

    def equip_title(self, title_id):
        return service_equip_title(self, title_id)

    def refresh_daily_tasks(self):
        return service_refresh_daily_tasks(self)

    def log_abandoned_action(self, action_name, elapsed_minutes):
        log_player_abandon(action_name, elapsed_minutes)

    def apply_task_exp_bonus(self, exp, task_id=None, source="daily"):
        return service_apply_task_exp_bonus(self, exp, task_id, source)

    def _result_with_progression(
            self,
            success,
            message,
            before_exp
    ):
        return result_with_progression(
            self,
            success,
            message,
            before_exp
        )

    def _collect_progression(self, before_exp):
        return collect_progression(self, before_exp)
