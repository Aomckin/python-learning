import ast
import unittest
from dataclasses import fields
from pathlib import Path

from core_types import GameState, OperationResult


class ArchitectureBoundaryTest(unittest.TestCase):
    def test_game_state_is_display_view_model(self):
        self.assertEqual(
            [field.name for field in fields(GameState)],
            [
                "window_title",
                "window_size",
                "energy_text",
                "energy_value",
                "energy_max",
                "exp_text",
                "level_text",
                "coin_text",
                "title_text",
                "logs",
                "action_views",
                "active_task_views",
                "active_special_task_views",
                "shop_category_views",
                "achievement_sections",
                "title_views",
            ],
        )

    def test_operation_result_is_event_only_boundary(self):
        self.assertEqual(
            [field.name for field in fields(OperationResult)],
            ["success", "message", "events", "state"],
        )

    def test_ui_uses_command_event_boundary(self):
        source = Path("ui.py").read_text(encoding="utf-8")

        forbidden = [
            "result.unlocked_",
            "result.level_up_info",
            "result.action_result",
            "core.player",
            "self.core.config",
            "self.core.actions",
            "self.core.initialize_progression",
            "self.core.complete_action_now",
            "self.core.complete_timed_action",
            "self.core.complete_daily_task",
            "self.core.complete_special_task",
            "self.core.buy_shop_item",
            "self.core.equip_title",
            "unlocked_achievement_ids",
            "unlocked_title_ids",
            "equipped_title_id",
        ]
        for text in forbidden:
            self.assertNotIn(text, source)

        self.assertIn("self.core.execute(", source)
        self.assertIn("for event in result.events:", source)

    def test_player_state_mutations_are_only_in_player_service(self):
        allowed = {
            Path("player.py"),
            Path("services") / "player_service.py",
        }
        files = [
            Path("achievement.py"),
            Path("title.py"),
            Path("shop.py"),
            Path("task.py"),
            Path("core.py"),
            *Path("services").glob("*.py"),
            *Path("tests").glob("test_*.py"),
        ]
        for path in files:
            if path in allowed:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            mutations = find_player_mutations(tree)
            self.assertEqual(mutations, [], f"{path}: {mutations}")

    def test_player_service_has_no_io_dependencies(self):
        source = Path("services/player_service.py").read_text(encoding="utf-8")

        forbidden = [
            "utils.json_store",
            "utils.logger",
            "load_player_state",
            "save_player_state",
            "load_player_logs",
            "log_player_action",
            "log_player_timed_action",
            "log_player_abandon",
            "save_json",
            "load_json",
            "log_action",
            "log_timed_action",
        ]
        for text in forbidden:
            self.assertNotIn(text, source)

    def test_player_entity_has_no_business_method_definitions(self):
        source = Path("player.py").read_text(encoding="utf-8")

        forbidden = [
            "def save_state",
            "def save_log",
            "def complete_timed_action",
            "def add_reward",
            "def add_special_reward",
            "def spend_coin",
            "def do_action",
        ]
        for text in forbidden:
            self.assertNotIn(text, source)


if __name__ == "__main__":
    unittest.main()


def find_player_mutations(tree):
    mutations = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            else:
                targets = [node.target]

            for target in targets:
                if is_player_target(target):
                    mutations.append((node.lineno, ast.unparse(target)))

        if isinstance(node, ast.Call):
            func = node.func
            if (
                    isinstance(func, ast.Attribute)
                    and func.attr == "append"
                    and is_player_target(func.value)
            ):
                mutations.append((node.lineno, ast.unparse(func.value)))

    return mutations


def is_player_target(node):
    if isinstance(node, ast.Subscript):
        return is_player_target(node.value)

    if not isinstance(node, ast.Attribute):
        return False

    root = node
    while isinstance(root, ast.Attribute):
        root = root.value

    if isinstance(root, ast.Name) and root.id == "player":
        return True

    if (
            isinstance(root, ast.Name)
            and root.id == "core"
            and ast.unparse(node).startswith("core.player.")
    ):
        return True

    if (
            isinstance(root, ast.Name)
            and root.id == "self"
            and ast.unparse(node).startswith("self.player.")
    ):
        return True

    return False
