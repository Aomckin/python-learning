import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from task import DailyTaskSystem, SpecialTaskManager, SpecialTaskSystem, TaskSystem


class SpecialTaskManagerTest(unittest.TestCase):
    def setUp(self):
        self.old_cwd = os.getcwd()
        self.old_data_dir = os.environ.get("OTAKU_ENERGY_DATA_DIR")
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["OTAKU_ENERGY_DATA_DIR"] = self.temp_dir.name
        os.chdir(self.temp_dir.name)
        today = datetime.now().strftime("%Y-%m-%d")
        Path("special_tasks.json").write_text(
            json.dumps(
                {
                    "last_update_date": today,
                    "active_task_id": "task_a",
                    "tasks": [
                        {
                            "id": "task_a",
                            "name": "任务A",
                            "coin": 10,
                            "exp": 5,
                            "created_time": "2026-06-24 00:00:00",
                            "completed_count": 0,
                            "done": False,
                        },
                        {
                            "id": "task_b",
                            "name": "任务B",
                            "coin": 10,
                            "exp": 5,
                            "created_time": "2026-06-24 00:00:00",
                            "completed_count": 0,
                            "done": False,
                        },
                        {
                            "id": "task_c",
                            "name": "任务C",
                            "coin": 10,
                            "exp": 5,
                            "created_time": "2026-06-24 00:00:00",
                            "completed_count": 0,
                            "done": False,
                        },
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        os.chdir(self.old_cwd)
        if self.old_data_dir is None:
            os.environ.pop("OTAKU_ENERGY_DATA_DIR", None)
        else:
            os.environ["OTAKU_ENERGY_DATA_DIR"] = self.old_data_dir
        self.temp_dir.cleanup()

    def test_increasing_slot_count_keeps_existing_active_task(self):
        manager = SpecialTaskManager(slot_count=1)

        manager.set_slot_count(2)

        active_task_ids = manager.tasks_data["active_task_ids"]
        self.assertIn("task_a", active_task_ids)
        self.assertEqual(len(active_task_ids), 2)
        self.assertEqual(len(manager.tasks), 2)

    def test_new_task_system_names_keep_legacy_special_manager_behavior(self):
        manager = SpecialTaskSystem(slot_count=1)

        self.assertIsInstance(manager, TaskSystem)
        self.assertEqual([task.id for task in manager.tasks], ["task_a"])

    def test_daily_task_system_uses_same_active_task_flow(self):
        today = datetime.now().strftime("%Y-%m-%d")
        Path("tasks.json").write_text(
            json.dumps(
                {
                    "last_update_date": today,
                    "active_task_ids": ["daily_a"],
                    "tasks": [
                        {
                            "id": "daily_a",
                            "name": "每日A",
                            "reward": 10,
                            "exp": 5,
                            "created_time": "2026-06-24 00:00:00",
                            "completed_count": 0,
                            "done": False,
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        manager = DailyTaskSystem()
        reward, exp = manager.finish(0)

        self.assertIsInstance(manager, TaskSystem)
        self.assertEqual([task.id for task in manager.tasks], ["daily_a"])
        self.assertEqual((reward, exp), (10, 5))
        self.assertTrue(manager.tasks[0].done)


if __name__ == "__main__":
    unittest.main()
