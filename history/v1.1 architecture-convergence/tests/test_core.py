import json
import os
import tempfile
import unittest
from pathlib import Path

from core import ActionDurationOption, GameCore
from core.command import (
    BUY_SHOP_ITEM,
    COMPLETE_DAILY_TASK,
    COMPLETE_SPECIAL_TASK,
    COMPLETE_TIMED_ACTION,
    INITIALIZE_PROGRESSION,
    REFRESH_DAILY_TASKS,
    GameCommand,
)
from core.event import (
    ACHIEVEMENT_UNLOCK,
    ACTION_COMPLETE,
    ERROR,
    LEVEL_UP,
    SHOP_PURCHASE,
    TASK_COMPLETE,
    TITLE_UNLOCK,
)


class GameCoreTest(unittest.TestCase):
    def setUp(self):
        self.old_cwd = os.getcwd()
        self.temp_dir = tempfile.TemporaryDirectory()
        os.chdir(self.temp_dir.name)
        self.write_project_files()

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()

    def write_json(self, name, data):
        Path(name).write_text(
            json.dumps(data, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )

    def write_project_files(self):
        self.write_json(
            "config.json",
            {
                "window_title": "测试宅宅能量条",
                "window_size": "650x1000",
                "max_energy": 180,
                "default_energy": 50,
                "theme": "default",
            },
        )
        self.write_json(
            "actions.json",
            {
                "学习": {"energy_change": 10, "description": "学习"},
                "看番": {"energy_change": -10, "description": "看番"},
            },
        )
        self.write_json(
            "level.json",
            {
                "initial_level": 1,
                "max_level": 20,
                "base_required_exp": 20,
                "step_levels": 5,
                "step_increase_exp": 10,
            },
        )
        self.write_json(
            "tasks.json",
            {
                "last_update_date": "2026-06-27",
                "active_task_ids": ["study_python"],
                "tasks": [
                    {
                        "id": "study_python",
                        "name": "学习Python",
                        "reward": 10,
                        "exp": 10,
                        "created_time": "2026-06-27 00:00:00",
                        "completed_count": 0,
                        "done": False,
                    }
                ],
            },
        )
        self.write_json(
            "special_tasks.json",
            {
                "last_update_date": "2026-06-27",
                "active_task_ids": ["deep_casting"],
                "tasks": [
                    {
                        "id": "deep_casting",
                        "name": "进入心流状态1小时",
                        "coin": 30,
                        "exp": 10,
                        "created_time": "2026-06-27 00:00:00",
                        "completed_count": 0,
                        "done": False,
                    }
                ],
            },
        )
        self.write_json(
            "shop.json",
            {
                "categories": ["任务", "成长", "称号"],
                "items": [
                    {
                        "id": "refresh_daily_tasks",
                        "name": "刷新每日任务",
                        "category": "任务",
                        "desc": "重新抽取今日普通任务。",
                        "price": 20,
                        "stock_type": "daily",
                        "effect_type": "refresh_daily_tasks",
                        "effect_value": 1,
                    },
                    {
                        "id": "daily_double_exp",
                        "name": "单日双倍经验",
                        "category": "成长",
                        "desc": "今日任务经验翻倍。",
                        "price": 50,
                        "stock_type": "daily",
                        "effect_type": "daily_double_exp",
                        "effect_value": 2,
                    },
                    {
                        "id": "special_task_slot",
                        "name": "增加特殊任务栏位",
                        "category": "任务",
                        "desc": "永久增加一个特殊任务栏位。",
                        "price": 120,
                        "stock_type": "permanent",
                        "effect_type": "special_task_slot",
                        "effect_value": 1,
                    },
                    {
                        "id": "archmage_title",
                        "name": "大魔法师",
                        "category": "称号",
                        "desc": "解锁称号：大魔法师。",
                        "price": 160,
                        "stock_type": "permanent",
                        "effect_type": "unlock_title",
                        "effect_value": "archmage",
                    },
                ],
            },
        )
        self.write_json(
            "achievements.json",
            [
                {
                    "id": "first_daily_task",
                    "name": "任务初体验",
                    "condition_type": "task_done_count",
                    "target_value": 1,
                    "reward_coin": 15,
                    "reward_exp": 0,
                },
                {
                    "id": "first_special_task",
                    "name": "支线开启",
                    "condition_type": "special_task_done_count",
                    "target_value": 1,
                    "reward_coin": 15,
                    "reward_exp": 0,
                },
                {
                    "id": "first_anime",
                    "name": "追番入门",
                    "condition_type": "action_count",
                    "target_action": "看番",
                    "target_value": 1,
                    "reward_coin": 10,
                    "reward_exp": 0,
                },
            ],
        )
        self.write_json(
            "titles.json",
            [
                {
                    "id": "beginner",
                    "name": "初学者",
                    "condition_type": "task_completed_count",
                    "target_value": 1,
                    "bonus_type": "exp_rate",
                    "bonus_value": 0.1,
                },
                {
                    "id": "archmage",
                    "name": "大魔法师",
                    "condition_type": "shop_purchase",
                    "target_value": "archmage_title",
                    "bonus_type": "positive_energy_rate",
                    "bonus_value": 0.25,
                },
            ],
        )
        self.write_json(
            "save.json",
            {
                "energy": 50,
                "exp": 10,
                "unlocked_achievements": [],
                "action_counts": {},
                "done_task_count": 0,
                "done_special_task_count": 0,
                "coin": 400,
                "shop_daily_purchases": {},
                "shop_total_purchases": {},
                "daily_double_exp_date": "",
                "special_task_slots": 1,
                "unlocked_titles": [],
                "equipped_title": "",
                "completed_timed_actions": 0,
            },
        )

    def test_get_state_exposes_ui_ready_data(self):
        core = GameCore(today_func=lambda: "2026-06-27")

        state = core.get_state()

        self.assertEqual(state.energy_value, 50)
        self.assertEqual(state.energy_max, 180)
        self.assertEqual(state.energy_text, "宅宅能量：50/180")
        self.assertEqual(state.level_text, "等级：Lv.1")
        self.assertEqual(state.exp_text, "经验：10/20")
        self.assertEqual(state.coin_text, "金币：400")
        self.assertEqual(
            [task["id"] for task in state.active_task_views],
            ["study_python"],
        )
        self.assertEqual(
            [task["id"] for task in state.active_special_task_views],
            ["deep_casting"],
        )
        self.assertEqual(
            [category["category"] for category in state.shop_category_views],
            ["任务", "成长", "称号"],
        )

    def test_initialize_progression_returns_startup_title_unlocks(self):
        self.write_json(
            "titles.json",
            [
                {
                    "id": "starter",
                    "name": "启动者",
                    "condition_type": "always",
                    "target_value": 0,
                    "bonus_type": "none",
                    "bonus_value": 0,
                }
            ],
        )
        core = GameCore(today_func=lambda: "2026-06-27")

        result = core.execute(GameCommand(INITIALIZE_PROGRESSION))

        self.assertTrue(result.success)
        self.assertEqual(
            [(event.type, event.payload["title"]["id"]) for event in result.events],
            [(TITLE_UNLOCK, "starter")]
        )

    def test_complete_daily_task_applies_rewards_and_progression_once(self):
        core = GameCore(today_func=lambda: "2026-06-27")

        result = core.execute(GameCommand(COMPLETE_DAILY_TASK, {"index": 0}))
        saved = json.loads(Path("save.json").read_text(encoding="utf-8"))

        self.assertTrue(result.success)
        self.assertEqual(saved["energy"], 60)
        self.assertEqual(saved["exp"], 20)
        self.assertEqual(saved["done_task_count"], 1)
        self.assertEqual(
            [event.type for event in result.events],
            [TASK_COMPLETE, ACHIEVEMENT_UNLOCK, TITLE_UNLOCK, LEVEL_UP]
        )
        self.assertEqual(result.events[1].payload["achievement"]["id"], "first_daily_task")
        self.assertEqual(result.events[2].payload["title"]["id"], "beginner")
        self.assertEqual(result.events[3].payload["level_up_info"]["after_level"], 2)

    def test_complete_special_task_applies_coin_exp_and_progression(self):
        core = GameCore(today_func=lambda: "2026-06-27")

        result = core.execute(GameCommand(COMPLETE_SPECIAL_TASK, {"index": 0}))
        saved = json.loads(Path("save.json").read_text(encoding="utf-8"))

        self.assertTrue(result.success)
        self.assertEqual(saved["coin"], 445)
        self.assertEqual(saved["exp"], 20)
        self.assertEqual(saved["done_special_task_count"], 1)
        self.assertEqual(
            [event.type for event in result.events],
            [TASK_COMPLETE, ACHIEVEMENT_UNLOCK, LEVEL_UP]
        )
        self.assertEqual(result.events[1].payload["achievement"]["id"], "first_special_task")

    def test_complete_timed_action_applies_action_result_and_progression(self):
        core = GameCore(today_func=lambda: "2026-06-27")
        option = ActionDurationOption(minutes=60, multiplier=1.5, exp=2)

        result = core.execute(
            GameCommand(
                COMPLETE_TIMED_ACTION,
                {"action_name": "看番", "option": option}
            )
        )
        saved = json.loads(Path("save.json").read_text(encoding="utf-8"))
        log_text = Path("log.txt").read_text(encoding="utf-8")

        self.assertTrue(result.success)
        self.assertEqual(result.events[0].type, ACTION_COMPLETE)
        self.assertEqual(result.events[0].payload["action_result"]["energy_change"], -15)
        self.assertEqual(result.events[0].payload["action_result"]["exp_change"], 2)
        self.assertEqual(saved["energy"], 35)
        self.assertEqual(saved["exp"], 12)
        self.assertEqual(saved["action_counts"]["看番"], 1)
        self.assertIn("60", log_text)
        self.assertIn("-15", log_text)
        self.assertEqual(result.events[1].type, ACHIEVEMENT_UNLOCK)
        self.assertEqual(result.events[1].payload["achievement"]["id"], "first_anime")

    def test_buy_shop_item_applies_core_side_effects(self):
        core = GameCore(today_func=lambda: "2026-06-27")

        double_exp = core.execute(GameCommand(BUY_SHOP_ITEM, {"item_id": "daily_double_exp"}))
        slot = core.execute(GameCommand(BUY_SHOP_ITEM, {"item_id": "special_task_slot"}))
        title = core.execute(GameCommand(BUY_SHOP_ITEM, {"item_id": "archmage_title"}))
        saved = json.loads(Path("save.json").read_text(encoding="utf-8"))

        self.assertTrue(double_exp.success)
        self.assertEqual(double_exp.events[0].type, SHOP_PURCHASE)
        self.assertEqual(saved["daily_double_exp_date"], "2026-06-27")
        self.assertTrue(slot.success)
        self.assertEqual(saved["special_task_slots"], 2)
        self.assertEqual(len(core.get_state().active_special_task_views), 1)
        self.assertTrue(title.success)
        self.assertIn("archmage", saved["unlocked_titles"])

    def test_failed_command_returns_error_event(self):
        core = GameCore(today_func=lambda: "2026-06-27")

        result = core.execute(GameCommand(BUY_SHOP_ITEM, {"item_id": "missing"}))

        self.assertFalse(result.success)
        self.assertEqual(result.events[0].type, ERROR)
        self.assertEqual(result.events[0].payload["message"], "商品不存在")

    def test_refresh_daily_tasks_is_available_as_core_command(self):
        core = GameCore(today_func=lambda: "2026-06-27")

        result = core.execute(GameCommand(REFRESH_DAILY_TASKS))

        self.assertTrue(result.success)
        self.assertEqual(
            [task["id"] for task in result.state.active_task_views],
            ["study_python"],
        )


if __name__ == "__main__":
    unittest.main()
