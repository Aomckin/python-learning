import json
import os
import tempfile
import unittest
from pathlib import Path

from core import (
    ActionDurationOption,
    ActionTimerState,
    get_action_duration_options,
)
from player import Otaku
from services.player_service import complete_timed_action


ACTIONS = {
    "学习": {"energy_change": 10},
    "健身": {"energy_change": 15},
    "敲代码": {"energy_change": 20},
    "看番": {"energy_change": -10},
    "推gal": {"energy_change": -15},
    "打游戏": {"energy_change": -20},
}


class TimedActionTest(unittest.TestCase):
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

    def make_player(self, energy=50, exp=0):
        Path("save.json").write_text(
            json.dumps(
                {
                    "energy": energy,
                    "exp": exp,
                    "unlocked_achievements": [],
                    "action_counts": {},
                    "done_task_count": 0,
                    "done_special_task_count": 0,
                    "coin": 0,
                    "shop_daily_purchases": {},
                    "shop_total_purchases": {},
                    "daily_double_exp_date": "",
                    "special_task_slots": 1,
                    "unlocked_titles": [],
                    "equipped_title": "",
                    "completed_timed_actions": 0,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return Otaku({"default_energy": 50, "max_energy": 180})

    def test_learning_25_minutes_adds_base_energy(self):
        player = self.make_player(energy=50)

        result = complete_timed_action(player, "学习", 25, 10, 0)

        self.assertEqual(result["energy_change"], 10)
        self.assertEqual(result["exp_change"], 0)
        self.assertEqual(player.energy, 60)
        self.assertEqual(player.exp, 0)
        self.assertEqual(player.action_counts["学习"], 1)

    def test_coding_60_minutes_adds_double_energy(self):
        player = self.make_player(energy=50)

        result = complete_timed_action(player, "敲代码", 60, 40, 0)

        self.assertEqual(result["energy_change"], 40)
        self.assertEqual(player.energy, 90)
        self.assertEqual(player.action_counts["敲代码"], 1)

    def test_anime_60_minutes_spends_energy_and_adds_two_exp(self):
        player = self.make_player(energy=50)

        result = complete_timed_action(player, "看番", 60, -15, 2)

        self.assertEqual(result["energy_change"], -15)
        self.assertEqual(result["exp_change"], 2)
        self.assertEqual(player.energy, 35)
        self.assertEqual(player.exp, 2)
        self.assertEqual(player.action_counts["看番"], 1)

    def test_completed_action_only_mutates_player_state(self):
        player = self.make_player(energy=50)

        complete_timed_action(player, "学习", 25, 10, 0)

        saved = json.loads(Path("save.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["energy"], 50)
        self.assertFalse(Path("log.txt").exists())
        self.assertEqual(player.energy, 60)
        self.assertEqual(player.action_counts["学习"], 1)

    def test_energy_does_not_exceed_maximum(self):
        player = self.make_player(energy=170)

        result = complete_timed_action(player, "敲代码", 60, 40, 0)

        self.assertEqual(result["energy_change"], 40)
        self.assertEqual(player.energy, 180)

    def test_energy_does_not_go_below_zero(self):
        player = self.make_player(energy=5)

        result = complete_timed_action(player, "打游戏", 90, -40, 3)

        self.assertEqual(result["energy_change"], -40)
        self.assertEqual(result["exp_change"], 3)
        self.assertEqual(player.energy, 0)

    def test_abandoned_timer_does_not_settle_action(self):
        player = self.make_player(energy=50)
        timer = ActionTimerState("学习", 25)

        timer.tick()
        timer.cancel()

        self.assertEqual(player.energy, 50)
        self.assertEqual(player.exp, 0)
        self.assertEqual(player.action_counts, {})
        self.assertTrue(timer.cancelled)

    def test_timer_pause_resume_and_completion_state(self):
        timer = ActionTimerState("敲代码", 1, total_seconds=2)

        self.assertEqual(timer.format_remaining(), "00:02")
        self.assertFalse(timer.is_finished())
        self.assertTrue(timer.tick())
        self.assertEqual(timer.remaining_seconds, 1)
        timer.pause()
        self.assertFalse(timer.tick())
        self.assertEqual(timer.remaining_seconds, 1)
        timer.resume()
        self.assertTrue(timer.tick())
        self.assertTrue(timer.is_finished())
        self.assertEqual(timer.format_remaining(), "00:00")

    def test_positive_action_duration_options(self):
        options = get_action_duration_options({"energy_change": 10})

        self.assertEqual(
            options,
            [
                ActionDurationOption(minutes=25, multiplier=1, exp=0),
                ActionDurationOption(minutes=45, multiplier=1.5, exp=0),
                ActionDurationOption(minutes=60, multiplier=2, exp=0),
            ],
        )

    def test_negative_action_duration_options(self):
        options = get_action_duration_options({"energy_change": -10})

        self.assertEqual(
            options,
            [
                ActionDurationOption(minutes=30, multiplier=1, exp=1),
                ActionDurationOption(minutes=60, multiplier=1.5, exp=2),
                ActionDurationOption(minutes=90, multiplier=2, exp=3),
            ],
        )


if __name__ == "__main__":
    unittest.main()
