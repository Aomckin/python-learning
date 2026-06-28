import json
import os
import tempfile
import unittest
from pathlib import Path

from shop import ShopManager


class FakePlayer:
    def __init__(self, coin=200):
        self.energy = 50
        self.exp = 0
        self.unlocked_achievements = []
        self.action_counts = {}
        self.done_task_count = 0
        self.done_special_task_count = 0
        self.coin = coin
        self.shop_daily_purchases = {}
        self.shop_total_purchases = {}
        self.daily_double_exp_date = ""
        self.special_task_slots = 1
        self.unlocked_titles = []
        self.equipped_title = ""
        self.completed_timed_actions = 0


class ShopManagerTest(unittest.TestCase):
    def setUp(self):
        self.old_data_dir = os.environ.get("OTAKU_ENERGY_DATA_DIR")
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["OTAKU_ENERGY_DATA_DIR"] = self.temp_dir.name
        self.shop_file = Path(self.temp_dir.name) / "shop.json"
        self.shop_file.write_text(
            json.dumps(
                {
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
                            "name": "大魔法师 🧙‍♂️",
                            "category": "称号",
                            "desc": "解锁称号：大魔法师 🧙‍♂️。",
                            "price": 160,
                            "stock_type": "permanent",
                            "effect_type": "unlock_title",
                            "effect_value": "archmage",
                        },
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        if self.old_data_dir is None:
            os.environ.pop("OTAKU_ENERGY_DATA_DIR", None)
        else:
            os.environ["OTAKU_ENERGY_DATA_DIR"] = self.old_data_dir
        self.temp_dir.cleanup()

    def make_manager(self, player):
        return ShopManager(
            player,
            shop_file=str(self.shop_file),
            today_func=lambda: "2026-06-24",
        )

    def test_daily_item_can_only_be_bought_once_per_day(self):
        player = FakePlayer()
        manager = self.make_manager(player)

        result = manager.buy_item("refresh_daily_tasks")

        self.assertTrue(result["success"])
        self.assertEqual(player.coin, 180)
        self.assertFalse(manager.can_buy("refresh_daily_tasks"))
        self.assertEqual(
            player.shop_daily_purchases["2026-06-24"]["refresh_daily_tasks"],
            1,
        )

    def test_daily_double_exp_marks_current_date(self):
        player = FakePlayer()
        manager = self.make_manager(player)

        result = manager.buy_item("daily_double_exp")

        self.assertTrue(result["success"])
        self.assertEqual(player.daily_double_exp_date, "2026-06-24")
        self.assertEqual(manager.get_task_exp_multiplier(), 2)

    def test_permanent_slot_item_only_applies_once(self):
        player = FakePlayer()
        manager = self.make_manager(player)

        first = manager.buy_item("special_task_slot")
        second = manager.buy_item("special_task_slot")

        self.assertTrue(first["success"])
        self.assertFalse(second["success"])
        self.assertEqual(player.special_task_slots, 2)
        self.assertEqual(player.coin, 80)
        self.assertEqual(player.shop_total_purchases["special_task_slot"], 1)

    def test_cannot_buy_without_enough_coin(self):
        player = FakePlayer(coin=10)
        manager = self.make_manager(player)

        result = manager.buy_item("refresh_daily_tasks")

        self.assertFalse(result["success"])
        self.assertEqual(player.coin, 10)
        self.assertEqual(player.shop_daily_purchases, {})

    def test_title_item_unlocks_title_once(self):
        player = FakePlayer()
        manager = self.make_manager(player)

        result = manager.buy_item("archmage_title")

        self.assertTrue(result["success"])
        self.assertIn("archmage", player.unlocked_titles)
        self.assertEqual(player.shop_total_purchases["archmage_title"], 1)
        self.assertEqual(player.coin, 40)
        self.assertFalse(manager.can_buy("archmage_title"))


if __name__ == "__main__":
    unittest.main()
