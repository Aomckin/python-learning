import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient

import api
from core import GameCore
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
from core_event import ACTION_COMPLETE, ERROR

_test_core = importlib.import_module("test_core")


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.old_cwd = os.getcwd()
        self.old_data_dir = os.environ.get("OTAKU_ENERGY_DATA_DIR")
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["OTAKU_ENERGY_DATA_DIR"] = self.temp_dir.name
        os.chdir(self.temp_dir.name)
        _test_core.GameCoreTest.write_project_files(self)
        api.core = GameCore(today_func=lambda: "2026-06-27")
        self.client = TestClient(api.app)

    def tearDown(self):
        os.chdir(self.old_cwd)
        if self.old_data_dir is None:
            os.environ.pop("OTAKU_ENERGY_DATA_DIR", None)
        else:
            os.environ["OTAKU_ENERGY_DATA_DIR"] = self.old_data_dir
        self.temp_dir.cleanup()

    def write_json(self, name, data):
        Path(name).write_text(
            json.dumps(data, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )

    def command(self, command_type, payload=None):
        return self.client.post(
            "/command",
            json={"type": command_type, "payload": payload or {}},
        )

    def get_action_name(self, group):
        state = self.client.get("/state").json()
        for action in state["action_views"]:
            if action["group"] == group:
                return action["name"]

        raise AssertionError(f"Missing {group} action")

    def test_state_returns_query_view_model(self):
        response = self.client.get("/state")

        self.assertEqual(response.status_code, 200)
        state = response.json()
        self.assertEqual(state["energy_value"], 50)
        self.assertEqual(state["energy_max"], 180)
        self.assertEqual(len(state["active_task_views"]), 1)
        self.assertEqual(len(state["active_special_task_views"]), 1)
        self.assertEqual(len(state["shop_category_views"]), 3)
        self.assertEqual(len(state["achievement_sections"]), 2)
        self.assertEqual(len(state["title_views"]), 2)

    def test_home_serves_static_console(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("宅宅能量条控制台", response.text)

    def test_static_app_js_is_served(self):
        response = self.client.get("/static/app.js")

        self.assertEqual(response.status_code, 200)
        self.assertIn("duration-options", response.text)
        self.assertIn("COMPLETE_TIMED_ACTION", response.text)
        self.assertIn("LOG_ABANDONED_ACTION", response.text)
        self.assertIn("TIMER_SECOND_SCALE = 1", response.text)
        self.assertNotIn('type: "COMPLETE_ACTION"', response.text)

    def test_static_console_covers_main_tkinter_views(self):
        home = self.client.get("/").text
        script = self.client.get("/static/app.js").text

        for element_id in [
            "dailyTasks",
            "specialTasks",
            "shopDialog",
            "achievementsDialog",
            "titlesDialog",
            "openShopButton",
            "openAchievementsButton",
            "openTitlesButton",
        ]:
            self.assertIn(f'id="{element_id}"', home)

        for dialog_markup in [
            '<dialog id="shopDialog"',
            '<dialog id="achievementsDialog"',
            '<dialog id="titlesDialog"',
        ]:
            self.assertIn(dialog_markup, home)

        for function_name in [
            "renderDailyTasks",
            "renderSpecialTasks",
            "renderShop",
            "renderAchievements",
            "renderTitles",
            "executeCommand",
        ]:
            self.assertIn(f"function {function_name}", script)

        self.assertIn(".showModal()", script)
        for command_type in [
            "COMPLETE_DAILY_TASK",
            "COMPLETE_SPECIAL_TASK",
            "REFRESH_DAILY_TASKS",
            "BUY_SHOP_ITEM",
            "EQUIP_TITLE",
        ]:
            self.assertIn(command_type, script)

    def test_command_completes_action(self):
        action_name = self.get_action_name("positive")

        response = self.command(COMPLETE_ACTION, {"action_name": action_name})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["state"]["energy_value"], 60)

    def test_command_gets_duration_options_and_completes_timed_action(self):
        action_name = self.get_action_name("negative")
        options_response = self.client.get(
            f"/actions/{action_name}/duration-options"
        )
        option = options_response.json()["events"][0]["payload"]["options"][1]

        response = self.command(
            COMPLETE_TIMED_ACTION,
            {"action_name": action_name, "option": option},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["events"][0]["type"], ACTION_COMPLETE)
        self.assertEqual(
            body["events"][0]["payload"]["action_result"]["duration_minutes"],
            option["minutes"],
        )

    def test_command_routes_task_shop_title_refresh_and_progression(self):
        daily = self.command(COMPLETE_DAILY_TASK, {"index": 0})
        special = self.command(COMPLETE_SPECIAL_TASK, {"index": 0})
        shop = self.command(BUY_SHOP_ITEM, {"item_id": "archmage_title"})
        title = self.command(EQUIP_TITLE, {"title_id": "archmage"})
        refresh = self.command(REFRESH_DAILY_TASKS)
        progression = self.command(INITIALIZE_PROGRESSION)
        abandon = self.command(
            LOG_ABANDONED_ACTION,
            {"action_name": self.get_action_name("positive"), "elapsed_minutes": 1},
        )

        self.assertTrue(daily.json()["success"])
        self.assertTrue(special.json()["success"])
        self.assertTrue(shop.json()["success"])
        self.assertTrue(title.json()["success"])
        self.assertTrue(refresh.json()["success"])
        self.assertTrue(progression.json()["success"])
        self.assertTrue(abandon.json()["success"])

    def test_old_business_routes_are_removed(self):
        action_name = self.get_action_name("positive")
        removed_paths = [
            f"/actions/{action_name}/complete",
            "/daily-tasks/0/complete",
            "/special-tasks/0/complete",
            "/shop/items/archmage_title/buy",
            "/titles/archmage/equip",
            "/daily-tasks/refresh",
            "/progression/initialize",
        ]

        for path in removed_paths:
            self.assertEqual(self.client.post(path).status_code, 404, path)

    def test_unknown_command_stays_core_operation_result(self):
        response = self.command("UNKNOWN_COMMAND")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["events"][0]["type"], ERROR)

    def test_get_commands_are_not_api_commands(self):
        for command_type in ["GET_STATE", "GET_ACTION_DURATION_OPTIONS"]:
            response = self.command(command_type)
            body = response.json()
            self.assertFalse(body["success"])
            self.assertEqual(body["events"][0]["type"], ERROR)


if __name__ == "__main__":
    unittest.main()
