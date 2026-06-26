import json
import os
import tempfile
import unittest
from pathlib import Path

from achievement import Achievement
from level import Level
from player import Otaku


class FakePlayer:
    def __init__(self, exp=0):
        self.energy = 50
        self.exp = exp
        self.coin = 0
        self.unlocked_achievements = []
        self.action_counts = {}
        self.done_task_count = 0
        self.done_special_task_count = 0
        self.saved = False

    def save_state(self):
        self.saved = True


class AchievementTest(unittest.TestCase):
    def setUp(self):
        self.old_cwd = os.getcwd()
        self.temp_dir = tempfile.TemporaryDirectory()
        os.chdir(self.temp_dir.name)

        Path("tasks.json").write_text(
            json.dumps(
                {
                    "tasks": [
                        {
                            "id": "study_python",
                            "name": "学习Python",
                            "reward": 10,
                            "exp": 5,
                            "completed_count": 1,
                            "done": False,
                        },
                        {
                            "id": "exercise",
                            "name": "健身",
                            "reward": 15,
                            "exp": 5,
                            "completed_count": 0,
                            "done": False,
                        },
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        Path("special_tasks.json").write_text(
            json.dumps(
                {
                    "tasks": [
                        {
                            "id": "deep_casting",
                            "name": "进入心流状态1小时",
                            "coin": 30,
                            "exp": 20,
                            "completed_count": 1,
                            "done": False,
                        },
                        {
                            "id": "magic_research",
                            "name": "连续编程90分钟",
                            "coin": 40,
                            "exp": 25,
                            "completed_count": 0,
                            "done": False,
                        },
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        Path("level.json").write_text(
            json.dumps(
                {
                    "initial_level": 1,
                    "max_level": 20,
                    "base_required_exp": 20,
                    "step_levels": 5,
                    "step_increase_exp": 10,
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()

    def write_achievements(self, achievements):
        Path("achievements.json").write_text(
            json.dumps(achievements, ensure_ascii=False),
            encoding="utf-8",
        )

    def test_action_count_unlocks_at_threshold(self):
        self.write_achievements(
            [
                {
                    "id": "study_20",
                    "condition_type": "action_count",
                    "target_action": "学习",
                    "target_value": 20,
                    "reward_coin": 30,
                    "reward_exp": 10,
                }
            ]
        )
        player = FakePlayer()
        player.action_counts["学习"] = 20

        unlocked = Achievement(player).check_achievements()

        self.assertEqual([item["id"] for item in unlocked], ["study_20"])
        self.assertEqual(player.coin, 30)
        self.assertEqual(player.exp, 10)
        self.assertEqual(player.unlocked_achievements, ["study_20"])
        self.assertTrue(player.saved)

    def test_action_count_does_not_unlock_before_threshold(self):
        self.write_achievements(
            [
                {
                    "id": "study_20",
                    "condition_type": "action_count",
                    "target_action": "学习",
                    "target_value": 20,
                    "reward_coin": 30,
                    "reward_exp": 10,
                }
            ]
        )
        player = FakePlayer()
        player.action_counts["学习"] = 19

        unlocked = Achievement(player).check_achievements()

        self.assertEqual(unlocked, [])
        self.assertEqual(player.coin, 0)
        self.assertEqual(player.exp, 0)
        self.assertFalse(player.saved)

    def test_total_action_count_unlocks_after_any_action(self):
        self.write_achievements(
            [
                {
                    "id": "first_action",
                    "condition_type": "total_action_count",
                    "target_value": 1,
                    "reward_coin": 10,
                    "reward_exp": 5,
                }
            ]
        )
        player = FakePlayer()
        player.action_counts["看番"] = 1

        unlocked = Achievement(player).check_achievements()

        self.assertEqual([item["id"] for item in unlocked], ["first_action"])
        self.assertEqual(player.coin, 10)
        self.assertEqual(player.exp, 5)

    def test_multiple_achievements_unlock_in_one_check(self):
        self.write_achievements(
            [
                {
                    "id": "study_20",
                    "condition_type": "action_count",
                    "target_action": "学习",
                    "target_value": 20,
                    "reward_coin": 30,
                    "reward_exp": 10,
                },
                {
                    "id": "first_daily_task",
                    "condition_type": "task_done_count",
                    "target_value": 1,
                    "reward_coin": 15,
                    "reward_exp": 5,
                },
            ]
        )
        player = FakePlayer()
        player.action_counts["学习"] = 20
        player.done_task_count = 1

        unlocked = Achievement(player).check_achievements()

        self.assertEqual(
            [item["id"] for item in unlocked],
            ["study_20", "first_daily_task"],
        )
        self.assertEqual(player.coin, 45)
        self.assertEqual(player.exp, 15)
        self.assertEqual(player.unlocked_achievements, ["study_20", "first_daily_task"])

    def test_unlocked_achievement_does_not_reward_again(self):
        self.write_achievements(
            [
                {
                    "id": "study_20",
                    "condition_type": "action_count",
                    "target_action": "学习",
                    "target_value": 20,
                    "reward_coin": 30,
                    "reward_exp": 10,
                }
            ]
        )
        player = FakePlayer()
        player.action_counts["学习"] = 20
        player.unlocked_achievements = ["study_20"]

        unlocked = Achievement(player).check_achievements()

        self.assertEqual(unlocked, [])
        self.assertEqual(player.coin, 0)
        self.assertEqual(player.exp, 0)

    def test_task_combo_uses_completed_count_after_done_resets(self):
        self.write_achievements(
            [
                {
                    "id": "focused_learner",
                    "condition_type": "task_combo",
                    "requirements": [
                        {"source": "daily", "task_id": "study_python", "count": 1},
                        {"source": "special", "task_id": "deep_casting", "count": 1},
                    ],
                    "reward_coin": 50,
                    "reward_exp": 20,
                }
            ]
        )
        player = FakePlayer()

        unlocked = Achievement(player).check_achievements()

        self.assertEqual([item["id"] for item in unlocked], ["focused_learner"])
        self.assertEqual(player.coin, 50)
        self.assertEqual(player.exp, 20)

    def test_level_achievement_unlocks_at_level_five_without_exp_reward(self):
        self.write_achievements(
            [
                {
                    "id": "level_5",
                    "condition_type": "level",
                    "target_value": 5,
                    "reward_coin": 40,
                    "reward_exp": 0,
                }
            ]
        )
        player = FakePlayer(exp=80)

        unlocked = Achievement(player, level_system=Level()).check_achievements()

        self.assertEqual([item["id"] for item in unlocked], ["level_5"])
        self.assertEqual(player.coin, 40)
        self.assertEqual(player.exp, 80)

    def test_player_loads_old_save_with_missing_optional_fields(self):
        Path("save.json").write_text(
            json.dumps({"energy": 50}, ensure_ascii=False),
            encoding="utf-8",
        )

        player = Otaku({"default_energy": 50, "max_energy": 180})

        self.assertEqual(player.energy, 50)
        self.assertEqual(player.coin, 0)
        self.assertEqual(player.unlocked_achievements, [])
        self.assertEqual(player.done_special_task_count, 0)


if __name__ == "__main__":
    unittest.main()
