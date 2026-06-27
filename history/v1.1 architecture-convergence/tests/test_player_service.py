import os
import tempfile
import unittest

from player import Otaku
from services.player_service import (
    add_coin,
    add_energy,
    add_exp,
    apply_shop_effect,
    equip_title,
    get_action_counts,
    get_coin,
    get_done_special_task_count,
    get_done_task_count,
    get_energy,
    get_equipped_title_id,
    get_exp,
    get_max_energy,
    get_special_task_slots,
    get_unlocked_achievement_ids,
    get_unlocked_title_ids,
    has_daily_double_exp,
    increment_action,
    increment_special_task_done,
    increment_task_done,
    record_purchase,
    spend_coin,
    unlock_achievement,
    unlock_title,
)


class PlayerServiceTest(unittest.TestCase):
    def setUp(self):
        self.old_cwd = os.getcwd()
        self.temp_dir = tempfile.TemporaryDirectory()
        os.chdir(self.temp_dir.name)

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()

    def test_player_service_mutates_core_player_fields(self):
        player = Otaku({"default_energy": 50, "max_energy": 180})

        add_energy(player, 200)
        add_exp(player, 7)
        add_coin(player, 9)
        increment_action(player, "学习")
        increment_task_done(player)
        increment_special_task_done(player)
        unlock_achievement(player, "first")
        unlock_achievement(player, "first")
        unlock_title(player, "starter")
        unlock_title(player, "starter")
        equip_title(player, "starter")

        self.assertEqual(player.energy, 180)
        self.assertEqual(player.exp, 7)
        self.assertEqual(player.coin, 9)
        self.assertEqual(player.action_counts["学习"], 1)
        self.assertEqual(player.done_task_count, 1)
        self.assertEqual(player.done_special_task_count, 1)
        self.assertEqual(player.unlocked_achievements, ["first"])
        self.assertEqual(player.unlocked_titles, ["starter"])
        self.assertEqual(player.equipped_title, "starter")

    def test_player_service_handles_shop_state(self):
        player = Otaku({"default_energy": 50, "max_energy": 180})
        add_coin(player, 100)
        daily_item = {
            "id": "daily_double_exp",
            "stock_type": "daily",
            "effect_type": "daily_double_exp",
            "effect_value": 2,
        }
        slot_item = {
            "id": "special_task_slot",
            "stock_type": "permanent",
            "effect_type": "special_task_slot",
            "effect_value": 1,
        }
        title_item = {
            "id": "archmage_title",
            "stock_type": "permanent",
            "effect_type": "unlock_title",
            "effect_value": "archmage",
        }

        self.assertTrue(spend_coin(player, 40))
        self.assertFalse(spend_coin(player, 100))
        record_purchase(player, daily_item, "2026-06-27")
        record_purchase(player, slot_item, "2026-06-27")
        apply_shop_effect(player, daily_item, "2026-06-27")
        apply_shop_effect(player, slot_item, "2026-06-27")
        apply_shop_effect(player, title_item, "2026-06-27")

        self.assertEqual(player.coin, 60)
        self.assertEqual(
            player.shop_daily_purchases["2026-06-27"]["daily_double_exp"],
            1,
        )
        self.assertEqual(player.shop_total_purchases["special_task_slot"], 1)
        self.assertEqual(player.daily_double_exp_date, "2026-06-27")
        self.assertEqual(player.special_task_slots, 2)
        self.assertIn("archmage", player.unlocked_titles)

    def test_player_service_read_helpers_expose_state_snapshot_values(self):
        player = Otaku({"default_energy": 50, "max_energy": 180})
        add_energy(player, 5)
        add_exp(player, 3)
        add_coin(player, 4)
        increment_action(player, "学习")
        increment_task_done(player)
        increment_special_task_done(player)
        unlock_achievement(player, "first")
        unlock_title(player, "starter")
        equip_title(player, "starter")
        apply_shop_effect(
            player,
            {"effect_type": "daily_double_exp", "effect_value": 2},
            "2026-06-27",
        )

        self.assertEqual(get_energy(player), 55)
        self.assertEqual(get_max_energy(player), 180)
        self.assertEqual(get_exp(player), 3)
        self.assertEqual(get_coin(player), 4)
        self.assertEqual(get_action_counts(player), {"学习": 1})
        self.assertEqual(get_done_task_count(player), 1)
        self.assertEqual(get_done_special_task_count(player), 1)
        self.assertEqual(get_unlocked_achievement_ids(player), {"first"})
        self.assertEqual(get_unlocked_title_ids(player), {"starter"})
        self.assertEqual(get_equipped_title_id(player), "starter")
        self.assertEqual(get_special_task_slots(player), 1)
        self.assertTrue(has_daily_double_exp(player, "2026-06-27"))
        self.assertFalse(has_daily_double_exp(player, "2026-06-28"))

    def test_player_entity_has_no_io_or_business_methods(self):
        forbidden = [
            "save_state",
            "save_log",
            "save_timed_action_log",
            "save_abandoned_action_log",
            "complete_timed_action",
            "add_reward",
            "add_special_reward",
            "spend_coin",
            "do_action",
        ]
        player = Otaku({"default_energy": 50, "max_energy": 180})

        for method_name in forbidden:
            self.assertFalse(hasattr(player, method_name), method_name)


if __name__ == "__main__":
    unittest.main()
