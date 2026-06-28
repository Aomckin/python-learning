import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from utils.json_store import file_exists, load_json, save_json
from utils.logger import log_abandon, log_action, log_event, log_system
from utils.time_utils import (
    format_datetime,
    get_now_datetime,
    get_now_str,
    get_today_str,
)


class JsonStoreTest(unittest.TestCase):
    def setUp(self):
        self.old_data_dir = os.environ.get("OTAKU_ENERGY_DATA_DIR")

    def tearDown(self):
        if self.old_data_dir is None:
            os.environ.pop("OTAKU_ENERGY_DATA_DIR", None)
        else:
            os.environ["OTAKU_ENERGY_DATA_DIR"] = self.old_data_dir

    def test_load_and_save_json_preserve_utf8_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "data.json"
            data = {"name": "宅宅", "items": [1, 2, 3]}

            save_json(path, data)

            self.assertTrue(file_exists(path))
            self.assertEqual(load_json(path), data)

    def test_relative_paths_resolve_from_data_root_env(self):
        with tempfile.TemporaryDirectory() as data_dir:
            with tempfile.TemporaryDirectory() as other_dir:
                os.environ["OTAKU_ENERGY_DATA_DIR"] = data_dir
                old_cwd = os.getcwd()
                os.chdir(other_dir)
                try:
                    save_json("save.json", {"energy": 5})
                    self.assertFalse(Path(other_dir, "save.json").exists())
                    self.assertEqual(load_json("save.json"), {"energy": 5})
                    self.assertTrue(Path(data_dir, "save.json").exists())
                finally:
                    os.chdir(old_cwd)

    def test_default_data_root_is_project_root_not_cwd(self):
        os.environ.pop("OTAKU_ENERGY_DATA_DIR", None)
        with tempfile.TemporaryDirectory() as other_dir:
            old_cwd = os.getcwd()
            os.chdir(other_dir)
            try:
                config = load_json("config.json")
            finally:
                os.chdir(old_cwd)

        self.assertIn("window_title", config)


class TimeUtilsTest(unittest.TestCase):
    def test_time_strings_use_existing_project_formats(self):
        self.assertRegex(get_today_str(), r"^\d{4}-\d{2}-\d{2}$")
        self.assertRegex(get_now_str(), r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
        self.assertEqual(format_datetime("2026-06-27"), "2026-06-27")
        self.assertIsInstance(get_now_datetime(), datetime)
        self.assertRegex(
            format_datetime(get_now_datetime()),
            r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
        )


class LoggerTest(unittest.TestCase):
    def setUp(self):
        self.old_cwd = os.getcwd()
        self.old_data_dir = os.environ.get("OTAKU_ENERGY_DATA_DIR")
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["OTAKU_ENERGY_DATA_DIR"] = self.temp_dir.name
        os.chdir(self.temp_dir.name)

    def tearDown(self):
        os.chdir(self.old_cwd)
        if self.old_data_dir is None:
            os.environ.pop("OTAKU_ENERGY_DATA_DIR", None)
        else:
            os.environ["OTAKU_ENERGY_DATA_DIR"] = self.old_data_dir
        self.temp_dir.cleanup()

    def read_log_parts(self):
        line = Path("log.txt").read_text(encoding="utf-8").strip()
        return line.split("|")

    def test_log_action_keeps_existing_action_log_shape(self):
        log_action("学习", "+10", 60)

        parts = self.read_log_parts()

        self.assertEqual(parts[1:], ["学习", "能量变化：+10", "当前能量：60"])

    def test_other_log_helpers_write_expected_messages(self):
        log_event("完成任务：学习Python", "能量+10 经验+5")
        log_system("系统消息")
        log_abandon("学习", 3)

        lines = Path("log.txt").read_text(encoding="utf-8").splitlines()

        self.assertIn("|完成任务：学习Python|能量+10 经验+5", lines[0])
        self.assertIn("|系统|系统消息", lines[1])
        self.assertIn("|放弃学习|已进行 3分钟", lines[2])


if __name__ == "__main__":
    unittest.main()
