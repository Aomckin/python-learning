import json
import os
import tempfile
import unittest
from pathlib import Path

from player import Otaku
from repositories.player_repository import (
    load_player_logs,
    load_player_state,
    log_player_action,
    save_player_state,
    serialize_player_state,
)
from services.player_service import add_coin


class PlayerRepositoryTest(unittest.TestCase):
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

    def test_load_player_state_uses_default_save_shape(self):
        data = load_player_state({"default_energy": 50})

        self.assertEqual(data["energy"], 50)
        self.assertEqual(data["coin"], 0)
        self.assertEqual(data["completed_timed_actions"], 0)

    def test_save_player_state_preserves_save_json_schema(self):
        player = Otaku({"default_energy": 50, "max_energy": 180})
        add_coin(player, 12)

        save_player_state(player)

        saved = json.loads(Path("save.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["coin"], 12)
        self.assertEqual(
            list(saved.keys()),
            [
                "energy",
                "exp",
                "unlocked_achievements",
                "action_counts",
                "done_task_count",
                "done_special_task_count",
                "coin",
                "shop_daily_purchases",
                "shop_total_purchases",
                "daily_double_exp_date",
                "special_task_slots",
                "unlocked_titles",
                "equipped_title",
                "completed_timed_actions",
            ],
        )

    def test_serialize_player_state_fills_legacy_missing_keys(self):
        class LegacyPlayer:
            energy = 50

        serialized = serialize_player_state(LegacyPlayer())

        self.assertEqual(serialized["energy"], 50)
        self.assertEqual(serialized["coin"], 0)
        self.assertEqual(serialized["completed_timed_actions"], 0)

    def test_logs_are_repository_io(self):
        log_player_action("学习", "+10", 60)

        logs = load_player_logs()

        self.assertTrue(any("学习" in item for item in logs))


if __name__ == "__main__":
    unittest.main()
