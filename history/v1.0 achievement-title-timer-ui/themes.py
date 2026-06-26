THEMES = {
    "default": {
        "window_bg": "#f5f7fb",
        "card_bg": "#ffffff",
        "text": "#20242a",
        "secondary_text": "#666f7a",
        "accent": "#3f7ad9",
        "accent_text": "#ffffff",
        "button_bg": "#e8edf5",
        "button_text": "#20242a",
        "button_active": "#d7e4fa",
        "border": "#d9e0ea",
        "success": "#2f8f5b",
        "warning": "#b7791f",
        "danger": "#c2413a",
        "disabled_text": "#9aa3ad",
    }
}

FONTS = {
    "title": ("Microsoft YaHei UI", 22, "bold"),
    "section": ("Microsoft YaHei UI", 13, "bold"),
    "status": ("Microsoft YaHei UI", 12),
    "normal": ("Microsoft YaHei UI", 11),
    "small": ("Microsoft YaHei UI", 10),
}

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 20,
}

SIZES = {
    "main_width": 720,
    "nav_button_width": 12,
    "action_button_width": 12,
    "task_button_width": 8,
    "history_height": 6,
    "history_width": 82,
}


def get_theme(name):
    return THEMES.get(name, THEMES["default"])
