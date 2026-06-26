import unittest
from pathlib import Path

from themes import get_theme


class ThemeTests(unittest.TestCase):
    def test_unknown_theme_falls_back_to_default(self):
        default_theme = get_theme("default")

        self.assertEqual(get_theme("missing-theme"), default_theme)

    def test_default_theme_has_required_semantic_keys(self):
        theme = get_theme("default")

        required_keys = {
            "window_bg",
            "card_bg",
            "text",
            "secondary_text",
            "accent",
            "accent_text",
            "button_bg",
            "button_text",
            "button_active",
            "border",
            "success",
            "warning",
            "danger",
            "disabled_text",
        }

        self.assertTrue(required_keys.issubset(theme.keys()))

    def test_status_meta_labels_are_on_separate_centered_row(self):
        ui_source = Path("ui.py").read_text(encoding="utf-8")

        self.assertIn("self.meta_frame = tk.Frame", ui_source)
        self.assertIn("self.level_label = tk.Label(\n            self.meta_frame", ui_source)
        self.assertIn("self.exp_label = tk.Label(\n            self.meta_frame", ui_source)
        self.assertIn("self.coin_label = tk.Label(\n            self.meta_frame", ui_source)

    def test_title_status_label_is_centered(self):
        ui_source = Path("ui.py").read_text(encoding="utf-8")

        self.assertIn('anchor="center"', ui_source)
        self.assertIn("self.title_label.pack(anchor=tk.CENTER)", ui_source)


if __name__ == "__main__":
    unittest.main()
