import json
import os
import tempfile
import unittest
from pathlib import Path

from player import Otaku
from title import Title


class FakeTask:
    def __init__(self, task_id, completed_count):
        self.id = task_id
        self.completed_count = completed_count


class TitleSystemTest(unittest.TestCase):
    def setUp(self):
        self.old_cwd = os.getcwd()
        self.temp_dir = tempfile.TemporaryDirectory()
        os.chdir(self.temp_dir.name)
        Path("special_tasks.json").write_text(
            json.dumps(
                {
                    "tasks": [
                        {"id": "offline_training", "completed_count": 3},
                        {"id": "wind_traveler", "completed_count": 2},
                        {"id": "city_roaming", "completed_count": 2},
                        {"id": "face_inner_self", "completed_count": 2},
                        {"id": "summer_night_walk", "completed_count": 2},
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()

    def write_titles(self, titles):
        Path("titles.json").write_text(
            json.dumps(titles, ensure_ascii=False),
            encoding="utf-8",
        )

    def make_player(self, save_data=None):
        data = {
            "energy": 50,
            "exp": 0,
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
        }
        if save_data:
            data.update(save_data)

        Path("save.json").write_text(
            json.dumps(data, ensure_ascii=False),
            encoding="utf-8",
        )
        return Otaku({"default_energy": 50, "max_energy": 180})

    def test_task_count_titles_unlock_at_new_thresholds(self):
        self.write_titles(
            [
                {
                    "id": "beginner",
                    "condition_type": "task_completed_count",
                    "target_value": 1,
                    "bonus_type": "exp_rate",
                    "bonus_value": 0.05,
                },
                {
                    "id": "executor",
                    "condition_type": "task_completed_count",
                    "target_value": 10,
                    "bonus_type": "exp_rate",
                    "bonus_value": 0.1,
                },
                {
                    "id": "task_master",
                    "condition_type": "task_completed_count",
                    "target_value": 50,
                    "bonus_type": "exp_rate",
                    "bonus_value": 0.15,
                },
            ]
        )
        player = self.make_player()
        tasks = [FakeTask("study_python", 50)]

        unlocked = Title(player).check_titles(tasks)

        self.assertEqual([title["id"] for title in unlocked], ["beginner", "executor", "task_master"])

    def test_action_count_titles_unlock_with_object_target_value(self):
        self.write_titles(
            [
                {
                    "id": "magic_apprentice",
                    "condition_type": "action_count",
                    "target_value": {"action_id": "学习", "count": 20},
                    "bonus_type": "action_energy_rate",
                    "bonus_value": {"action_id": "学习", "rate": 0.1},
                },
                {
                    "id": "bug_tamer",
                    "condition_type": "action_count",
                    "target_value": {"action_id": "敲代码", "count": 50},
                    "bonus_type": "action_energy_rate",
                    "bonus_value": {"action_id": "敲代码", "rate": 0.2},
                },
                {
                    "id": "muscle_mage",
                    "condition_type": "action_count",
                    "target_value": {"action_id": "健身", "count": 20},
                    "bonus_type": "action_energy_rate",
                    "bonus_value": {"action_id": "健身", "rate": 0.15},
                },
            ]
        )
        player = self.make_player(
            {
                "action_counts": {
                    "学习": 20,
                    "敲代码": 50,
                    "健身": 20,
                }
            }
        )

        unlocked = Title(player).check_titles([])

        self.assertEqual([title["id"] for title in unlocked], ["magic_apprentice", "bug_tamer", "muscle_mage"])

    def test_combo_special_timed_achievement_shop_and_outdoor_conditions_unlock(self):
        self.write_titles(
            [
                {
                    "id": "legal_slacker",
                    "condition_type": "action_combo_count",
                    "target_value": [
                        {"action_id": "看番", "count": 20},
                        {"action_id": "推gal", "count": 20},
                        {"action_id": "打游戏", "count": 20},
                    ],
                    "bonus_type": "negative_action_exp_rate",
                    "bonus_value": 0.2,
                },
                {
                    "id": "information_insulator",
                    "condition_type": "special_task_completed_count",
                    "target_value": {"task_id": "offline_training", "count": 3},
                    "bonus_type": "special_task_exp_rate",
                    "bonus_value": 0.1,
                },
                {
                    "id": "focus_caster",
                    "condition_type": "timed_action_completed_count",
                    "target_value": 20,
                    "bonus_type": "positive_energy_rate",
                    "bonus_value": 0.1,
                },
                {
                    "id": "achievement_collector",
                    "condition_type": "achievement_unlocked_count",
                    "target_value": 20,
                    "bonus_type": "exp_rate",
                    "bonus_value": 0.15,
                },
                {
                    "id": "archmage",
                    "condition_type": "shop_purchase",
                    "target_value": "archmage_title",
                    "bonus_type": "positive_energy_rate",
                    "bonus_value": 0.25,
                },
                {
                    "id": "wind_traveler_title",
                    "condition_type": "outdoor_task_completed_count",
                    "target_value": 10,
                    "bonus_type": "outdoor_task_exp_rate",
                    "bonus_value": 0.15,
                },
            ]
        )
        player = self.make_player(
            {
                "action_counts": {"看番": 20, "推gal": 20, "打游戏": 20},
                "completed_timed_actions": 20,
                "unlocked_achievements": [f"achievement_{index}" for index in range(20)],
                "shop_total_purchases": {"archmage_title": 1},
            }
        )
        tasks = [FakeTask("walk_20_minutes", 2)]

        unlocked = Title(player).check_titles(tasks)

        self.assertEqual(
            [title["id"] for title in unlocked],
            [
                "legal_slacker",
                "information_insulator",
                "focus_caster",
                "achievement_collector",
                "archmage",
                "wind_traveler_title",
            ],
        )

    def test_old_save_without_completed_timed_actions_defaults_to_zero(self):
        self.write_titles([])
        Path("save.json").write_text(
            json.dumps({"energy": 50}, ensure_ascii=False),
            encoding="utf-8",
        )

        player = Otaku({"default_energy": 50, "max_energy": 180})

        self.assertEqual(player.completed_timed_actions, 0)

    def test_only_equipped_title_effect_applies_and_switching_replaces_effect(self):
        self.write_titles(
            [
                {
                    "id": "magic_apprentice",
                    "condition_type": "action_count",
                    "target_value": {"action_id": "学习", "count": 20},
                    "bonus_type": "action_energy_rate",
                    "bonus_value": {"action_id": "学习", "rate": 0.1},
                },
                {
                    "id": "bug_tamer",
                    "condition_type": "action_count",
                    "target_value": {"action_id": "敲代码", "count": 50},
                    "bonus_type": "action_energy_rate",
                    "bonus_value": {"action_id": "敲代码", "rate": 0.2},
                },
            ]
        )
        player = self.make_player(
            {
                "unlocked_titles": ["magic_apprentice", "bug_tamer"],
                "equipped_title": "magic_apprentice",
            }
        )
        title_system = Title(player)

        self.assertEqual(title_system.apply_action_energy_bonus("学习", 10), 11)
        self.assertEqual(title_system.apply_action_energy_bonus("敲代码", 20), 20)

        title_system.equip_title("bug_tamer")

        self.assertEqual(title_system.apply_action_energy_bonus("学习", 10), 10)
        self.assertEqual(title_system.apply_action_energy_bonus("敲代码", 20), 24)

    def test_negative_action_cost_reduction_direction_is_correct(self):
        self.write_titles(
            [
                {
                    "id": "dimension_observer",
                    "condition_type": "action_count",
                    "target_value": {"action_id": "看番", "count": 20},
                    "bonus_type": "action_energy_cost_reduction",
                    "bonus_value": {"action_id": "看番", "rate": 0.1},
                }
            ]
        )
        player = self.make_player(
            {
                "unlocked_titles": ["dimension_observer"],
                "equipped_title": "dimension_observer",
            }
        )

        self.assertEqual(Title(player).apply_action_energy_bonus("看番", -10), -9)


if __name__ == "__main__":
    unittest.main()
