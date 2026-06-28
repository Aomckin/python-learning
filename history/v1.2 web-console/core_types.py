from dataclasses import dataclass, field


@dataclass(frozen=True)
class ActionDurationOption:
    minutes: int
    multiplier: float
    exp: int


@dataclass
class GameState:
    window_title: str
    window_size: str
    energy_text: str
    energy_value: int
    energy_max: int
    exp_text: str
    level_text: str
    coin_text: str
    title_text: str
    logs: list
    action_views: list = field(default_factory=list)
    active_task_views: list = field(default_factory=list)
    active_special_task_views: list = field(default_factory=list)
    shop_category_views: list = field(default_factory=list)
    achievement_sections: list = field(default_factory=list)
    title_views: list = field(default_factory=list)


@dataclass
class OperationResult:
    success: bool
    message: str = ""
    events: list = field(default_factory=list)
    state: GameState | None = None
