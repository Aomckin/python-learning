import tkinter as tk
from tkinter import messagebox, ttk

from core import ActionTimerState, GameCore, get_action_duration_options
from core.command import (
    BUY_SHOP_ITEM,
    COMPLETE_ACTION,
    COMPLETE_DAILY_TASK,
    COMPLETE_SPECIAL_TASK,
    COMPLETE_TIMED_ACTION,
    EQUIP_TITLE,
    INITIALIZE_PROGRESSION,
    LOG_ABANDONED_ACTION,
    GameCommand,
)
from core.event import (
    ACHIEVEMENT_UNLOCK,
    ACTION_COMPLETE,
    ERROR,
    LEVEL_UP,
    SHOP_PURCHASE,
    TASK_COMPLETE,
    TITLE_UNLOCK,
)
from themes import FONTS, SIZES, SPACING, get_theme


class GameUI:
    def __init__(self):
        self.core = GameCore()
        initial_state = self.core.get_state()
        self.action_views = initial_state.action_views
        self.theme = get_theme("default")
        self.window = tk.Tk()
        self.window.title(initial_state.window_title)
        self.window.geometry(initial_state.window_size)
        self.action_buttons = []
        self.task_buttons = []
        self.task_status_labels = []
        self.special_task_buttons = []
        self.special_task_rows = []
        self.achievement_clear_job = None
        self.level_notice_clear_job = None
        self.shop_window = None
        self.timer = None
        self.timer_window = None
        self.timer_after_job = None
        self.timer_action_option = None
        self.timer_remaining_label = None
        self.timer_status_label = None
        self.timer_pause_button = None
        self.timer_resume_button = None

        self.configure_window_style()
        self.setup_main_layout()

        result = self.core.execute(GameCommand(INITIALIZE_PROGRESSION))
        self.handle_operation_result(result)

    def configure_window_style(self):
        self.window.configure(bg=self.theme["window_bg"])

    def create_card_frame(self, parent):
        frame = tk.Frame(
            parent,
            bg=self.theme["card_bg"],
            highlightbackground=self.theme["border"],
            highlightthickness=1,
            bd=0
        )
        return frame

    def create_section_label(self, parent, text):
        return tk.Label(
            parent,
            text=text,
            font=FONTS["section"],
            bg=self.theme["card_bg"],
            fg=self.theme["text"],
            anchor="w"
        )

    def create_nav_button(self, parent, text, command):
        return tk.Button(
            parent,
            text=text,
            width=SIZES["nav_button_width"],
            command=command,
            bg=self.theme["button_bg"],
            fg=self.theme["button_text"],
            activebackground=self.theme["button_active"],
            activeforeground=self.theme["button_text"],
            relief=tk.FLAT,
            font=FONTS["normal"]
        )

    def get_tk_state(self, state_text):
        return tk.NORMAL if state_text == "normal" else tk.DISABLED

    def get_button_fg(self, state_text):
        return (
            self.theme["button_text"]
            if state_text == "normal"
            else self.theme["disabled_text"]
        )

    def create_action_button(self, parent, action_name, change):
        color = self.theme["success"] if change > 0 else self.theme["warning"]
        return tk.Button(
            parent,
            text=f"{action_name} {change:+}",
            width=SIZES["action_button_width"],
            command=lambda name=action_name: self.handle_action(name),
            bg=self.theme["button_bg"],
            fg=color,
            activebackground=self.theme["button_active"],
            relief=tk.FLAT,
            font=FONTS["normal"]
        )

    def create_task_row(self, parent, title, detail, button_text, command=None):
        row = tk.Frame(parent, bg=self.theme["card_bg"])
        row.pack(fill=tk.X, pady=SPACING["xs"])

        info_frame = tk.Frame(row, bg=self.theme["card_bg"])
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        name_label = tk.Label(
            info_frame,
            text=title,
            font=FONTS["normal"],
            bg=self.theme["card_bg"],
            fg=self.theme["text"],
            anchor="w"
        )
        name_label.pack(fill=tk.X)

        detail_label = tk.Label(
            info_frame,
            text=detail,
            font=FONTS["small"],
            bg=self.theme["card_bg"],
            fg=self.theme["secondary_text"],
            anchor="w"
        )
        detail_label.pack(fill=tk.X)

        button = tk.Button(
            row,
            text=button_text,
            width=SIZES["task_button_width"],
            command=command,
            bg=self.theme["button_bg"],
            fg=self.theme["button_text"],
            activebackground=self.theme["button_active"],
            relief=tk.FLAT,
            font=FONTS["small"]
        )
        button.pack(side=tk.RIGHT, padx=(SPACING["sm"], 0))

        return row, button, detail_label

    def setup_main_layout(self):
        state = self.core.get_state()
        self.window_title_label = tk.Label(
            self.window,
            text=state.window_title,
            font=FONTS["title"],
            bg=self.theme["window_bg"],
            fg=self.theme["text"]
        )
        self.window_title_label.pack(pady=(SPACING["lg"], SPACING["md"]))

        self.status_card = self.create_card_frame(self.window)
        self.status_card.pack(
            fill=tk.X,
            padx=SPACING["lg"],
            pady=(0, SPACING["md"])
        )

        self.energy_frame = tk.Frame(self.status_card, bg=self.theme["card_bg"])
        self.energy_frame.pack(
            anchor=tk.CENTER,
            padx=SPACING["md"],
            pady=(SPACING["sm"], SPACING["xs"])
        )

        self.energy_label = tk.Label(
            self.energy_frame,
            text=state.energy_text,
            font=FONTS["status"],
            bg=self.theme["card_bg"],
            fg=self.theme["text"]
        )
        self.energy_label.pack(side=tk.LEFT, padx=(0, SPACING["sm"]))

        self.energy_bar = ttk.Progressbar(
            self.energy_frame,
            length=150,
            maximum=state.energy_max,
            value=state.energy_value
        )
        self.energy_bar.pack(side=tk.LEFT)

        self.meta_frame = tk.Frame(self.status_card, bg=self.theme["card_bg"])
        self.meta_frame.pack(
            anchor=tk.CENTER,
            padx=SPACING["md"],
            pady=(SPACING["xs"], SPACING["sm"])
        )

        self.level_label = tk.Label(
            self.meta_frame,
            text=state.level_text,
            font=FONTS["status"],
            bg=self.theme["card_bg"],
            fg=self.theme["text"]
        )
        self.level_label.pack(side=tk.LEFT, padx=(0, SPACING["md"]))

        self.exp_label = tk.Label(
            self.meta_frame,
            text=state.exp_text,
            font=FONTS["status"],
            bg=self.theme["card_bg"],
            fg=self.theme["text"]
        )
        self.exp_label.pack(side=tk.LEFT, padx=(0, SPACING["md"]))

        self.coin_label = tk.Label(
            self.meta_frame,
            text=state.coin_text,
            font=FONTS["status"],
            bg=self.theme["card_bg"],
            fg=self.theme["text"]
        )
        self.coin_label.pack(side=tk.LEFT)

        self.title_status_frame = tk.Frame(
            self.status_card,
            bg=self.theme["card_bg"]
        )
        self.title_status_frame.pack(
            anchor=tk.CENTER,
            padx=SPACING["md"],
            pady=(0, SPACING["sm"])
        )

        self.title_label = tk.Label(
            self.title_status_frame,
            text="称号：无",
            font=FONTS["normal"],
            bg=self.theme["card_bg"],
            fg=self.theme["secondary_text"],
            anchor="center",
            justify=tk.CENTER
        )
        self.title_label.pack(anchor=tk.CENTER)

        self.nav_frame = tk.Frame(self.window, bg=self.theme["window_bg"])
        self.nav_frame.pack(pady=(0, SPACING["md"]))

        self.title_button = self.create_nav_button(
            self.nav_frame,
            text="称号",
            command=self.open_title_window
        )
        self.title_button.pack(side=tk.LEFT, padx=SPACING["xs"])

        self.achievement_button = self.create_nav_button(
            self.nav_frame,
            text="成就",
            command=self.open_achievement_window
        )
        self.achievement_button.pack(side=tk.LEFT, padx=SPACING["xs"])

        self.shop_button = self.create_nav_button(
            self.nav_frame,
            text="商店",
            command=self.open_shop_window
        )
        self.shop_button.pack(side=tk.LEFT, padx=SPACING["xs"])

        self.achievement_label = tk.Label(
            self.window,
            text="",
            font=FONTS["small"],
            bg=self.theme["window_bg"],
            fg=self.theme["warning"],
            justify="center"
        )
        self.achievement_label.pack(pady=(0, SPACING["xs"]))

        self.level_notice_label = tk.Label(
            self.window,
            text="",
            font=FONTS["small"],
            bg=self.theme["window_bg"],
            fg=self.theme["secondary_text"],
            justify="center"
        )
        self.level_notice_label.pack(pady=(0, SPACING["sm"]))

        self.main_area = tk.Frame(self.window, bg=self.theme["window_bg"])
        self.main_area.pack(fill=tk.BOTH, expand=True, padx=SPACING["lg"])

        self.action_card = self.create_card_frame(self.main_area)
        self.action_card.pack(fill=tk.X, pady=(0, SPACING["md"]))

        action_title = self.create_section_label(self.action_card, "行动")
        action_title.pack(fill=tk.X, padx=SPACING["md"], pady=(SPACING["sm"], 0))

        self.action_frame = tk.Frame(self.action_card, bg=self.theme["card_bg"])
        self.action_frame.pack(fill=tk.X, padx=SPACING["md"], pady=SPACING["sm"])
        self.create_action_group("正向行动", "positive", 0)
        self.create_action_group("娱乐行动", "negative", 1)

        self.task_area = tk.Frame(self.main_area, bg=self.theme["window_bg"])
        self.task_area.pack(fill=tk.BOTH, expand=True, pady=(0, SPACING["md"]))

        self.daily_task_frame = self.create_card_frame(self.task_area)
        self.daily_task_frame.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            padx=(0, SPACING["sm"])
        )

        self.special_task_frame = self.create_card_frame(self.task_area)
        self.special_task_frame.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            padx=(SPACING["sm"], 0)
        )

        self.task_label = self.create_section_label(self.daily_task_frame, "每日任务")
        self.task_label.pack(fill=tk.X, padx=SPACING["md"], pady=SPACING["sm"])

        for task_view in state.active_task_views:
            row, button, detail_label = self.create_task_row(
                self.daily_task_frame,
                task_view["name"],
                task_view["detail_text"],
                task_view["button_text"],
                command=lambda payload=task_view["command_payload"]:
                self.handle_task(payload["index"])
            )
            button.config(
                state=self.get_tk_state(task_view["button_state"]),
                fg=self.get_button_fg(task_view["button_state"])
            )
            self.task_buttons.append(button)
            self.task_status_labels.append(detail_label)

        self.special_task_label = self.create_section_label(
            self.special_task_frame,
            "特殊任务"
        )
        self.special_task_label.pack(
            fill=tk.X,
            padx=SPACING["md"],
            pady=SPACING["sm"]
        )

        self.refresh_special_task_buttons()

        self.history_card = self.create_card_frame(self.main_area)
        self.history_card.pack(fill=tk.X, pady=(0, SPACING["md"]))

        self.history_label = self.create_section_label(
            self.history_card,
            "最近行动记录"
        )
        self.history_label.pack(fill=tk.X, padx=SPACING["md"], pady=SPACING["sm"])

        self.history_body = tk.Frame(self.history_card, bg=self.theme["card_bg"])
        self.history_body.pack(fill=tk.X, padx=SPACING["md"], pady=(0, SPACING["sm"]))

        self.history_text = tk.Text(
            self.history_body,
            height=SIZES["history_height"],
            width=SIZES["history_width"],
            bg=self.theme["card_bg"],
            fg=self.theme["text"],
            font=FONTS["small"],
            relief=tk.FLAT,
            wrap=tk.WORD
        )
        self.history_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.history_scrollbar = tk.Scrollbar(
            self.history_body,
            command=self.history_text.yview
        )
        self.history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_text.config(yscrollcommand=self.history_scrollbar.set)

    def create_action_group(self, title, group_name, column):
        group = tk.Frame(self.action_frame, bg=self.theme["card_bg"])
        group.grid(row=column, column=0, sticky="ew", pady=SPACING["xs"])
        self.action_frame.grid_columnconfigure(0, weight=1)

        label = tk.Label(
            group,
            text=title,
            font=FONTS["small"],
            bg=self.theme["card_bg"],
            fg=self.theme["secondary_text"],
            anchor="w"
        )
        label.pack(fill=tk.X)

        button_row = tk.Frame(group, bg=self.theme["card_bg"])
        button_row.pack(fill=tk.X)

        for action_view in self.action_views:
            if action_view["group"] != group_name:
                continue

            button = self.create_action_button(
                button_row,
                action_view["name"],
                action_view["energy_change"]
            )
            button.pack(side=tk.LEFT, padx=(0, SPACING["sm"]), pady=SPACING["xs"])
            self.action_buttons.append(button)

    def handle_action(self, action_name):
        if self.is_action_timer_running():
            self.level_notice_label.config(text="已有行动计时正在进行")
            return

        self.open_action_duration_window(action_name)

    def is_action_timer_running(self):
        return self.timer is not None and not self.timer.cancelled

    def open_action_duration_window(self, action_name):
        action_view = self.get_action_view(action_name)
        options = get_action_duration_options(
            action_view["duration_options_source"]
        )
        window = tk.Toplevel(self.window)
        window.title("选择行动时长")
        window.geometry("260x180")
        window.resizable(False, False)

        tk.Label(
            window,
            text=f"选择「{action_name}」时长",
            font=("Microsoft YaHei", 12)
        ).pack(pady=12)

        for option in options:
            minutes = option.minutes
            tk.Button(
                window,
                text=f"{minutes}分钟",
                width=12,
                command=lambda selected=option: self.start_action_timer(
                    action_name,
                    selected,
                    window
                )
            ).pack(pady=3)

        tk.Button(
            window,
            text="取消",
            width=12,
            command=window.destroy
        ).pack(pady=5)

    def get_action_view(self, action_name):
        for action_view in self.action_views:
            if action_view["name"] == action_name:
                return action_view

        raise KeyError(action_name)

    def start_action_timer(self, action_name, option, selection_window=None):
        if self.is_action_timer_running():
            self.level_notice_label.config(text="已有行动计时正在进行")
            return

        if selection_window is not None and selection_window.winfo_exists():
            selection_window.destroy()

        self.timer = ActionTimerState(action_name, option.minutes)
        self.timer_action_option = option
        self.set_action_buttons_state(tk.DISABLED)
        self.open_action_timer_window()
        self.schedule_timer_tick()

    def open_action_timer_window(self):
        self.timer_window = tk.Toplevel(self.window)
        self.timer_window.title("行动计时")
        self.timer_window.geometry("300x180")
        self.timer_window.resizable(False, False)
        self.timer_window.protocol("WM_DELETE_WINDOW", self.abandon_action_timer)

        self.timer_status_label = tk.Label(
            self.timer_window,
            text=f"正在进行：{self.timer.action_name}",
            font=("Microsoft YaHei", 12)
        )
        self.timer_status_label.pack(pady=12)

        self.timer_remaining_label = tk.Label(
            self.timer_window,
            text=f"剩余时间：{self.timer.format_remaining()}",
            font=("Microsoft YaHei", 16)
        )
        self.timer_remaining_label.pack(pady=8)

        button_frame = tk.Frame(self.timer_window)
        button_frame.pack(pady=8)

        self.timer_pause_button = tk.Button(
            button_frame,
            text="暂停",
            width=8,
            command=self.pause_action_timer
        )
        self.timer_pause_button.pack(side=tk.LEFT, padx=4)

        self.timer_resume_button = tk.Button(
            button_frame,
            text="继续",
            width=8,
            state=tk.DISABLED,
            command=self.resume_action_timer
        )
        self.timer_resume_button.pack(side=tk.LEFT, padx=4)

        tk.Button(
            button_frame,
            text="放弃",
            width=8,
            command=self.abandon_action_timer
        ).pack(side=tk.LEFT, padx=4)

    def schedule_timer_tick(self):
        self.cancel_timer_after()
        self.timer_after_job = self.window.after(1000, self.tick_action_timer)

    def tick_action_timer(self):
        if self.timer is None or self.timer.cancelled:
            return

        if not self.timer.paused:
            self.timer.tick()
            self.refresh_timer_display()

        if self.timer.is_finished():
            self.finish_action_timer()
            return

        self.schedule_timer_tick()

    def refresh_timer_display(self):
        if self.timer_remaining_label is not None and self.timer is not None:
            self.timer_remaining_label.config(
                text=f"剩余时间：{self.timer.format_remaining()}"
            )

    def pause_action_timer(self):
        if self.timer is None:
            return

        self.timer.pause()
        self.cancel_timer_after()
        if self.timer_pause_button is not None:
            self.timer_pause_button.config(state=tk.DISABLED)
        if self.timer_resume_button is not None:
            self.timer_resume_button.config(state=tk.NORMAL)

    def resume_action_timer(self):
        if self.timer is None:
            return

        self.timer.resume()
        if self.timer_pause_button is not None:
            self.timer_pause_button.config(state=tk.NORMAL)
        if self.timer_resume_button is not None:
            self.timer_resume_button.config(state=tk.DISABLED)
        self.schedule_timer_tick()

    def abandon_action_timer(self):
        if self.timer is None:
            return

        self.cancel_timer_after()
        self.timer.cancel()
        self.core.execute(
            GameCommand(
                LOG_ABANDONED_ACTION,
                {
                    "action_name": self.timer.action_name,
                    "elapsed_minutes": self.timer.elapsed_minutes(),
                }
            )
        )
        self.close_timer_window()
        self.clear_action_timer()
        self.set_action_buttons_state(tk.NORMAL)
        self.update_display()

    def finish_action_timer(self):
        if self.timer is None:
            return

        self.cancel_timer_after()
        timer = self.timer
        option = self.timer_action_option
        result = self.core.execute(
            GameCommand(
                COMPLETE_TIMED_ACTION,
                {"action_name": timer.action_name, "option": option}
            )
        )
        self.close_timer_window()
        self.clear_action_timer()
        self.set_action_buttons_state(tk.NORMAL)
        self.handle_operation_result(result)

    def show_action_result(self, result):
        lines = [
            f"本次行动：{result['action_name']}",
            f"持续时间：{result['duration_minutes']}分钟",
            f"能量：{result['energy_change']:+}"
        ]

        if result["exp_change"]:
            lines.append(f"经验：+{result['exp_change']}")

        messagebox.showinfo("行动完成", "\n".join(lines))

    def handle_operation_result(self, result):
        handled_message = False
        for event in result.events:
            if self.handle_event(event):
                handled_message = True

        if result.message and not handled_message:
            self.level_notice_label.config(text=result.message)

        self.update_display()

    def handle_event(self, event):
        if event.type == ERROR:
            self.level_notice_label.config(
                text=event.payload.get("message", "操作失败")
            )
            return True

        if event.type == ACHIEVEMENT_UNLOCK:
            self.show_achievement(event.payload["achievement"])
            return False

        if event.type == TITLE_UNLOCK:
            self.show_title_unlock(event.payload["title"])
            return False

        if event.type == LEVEL_UP:
            self.show_level_notice(event.payload["level_up_info"])
            return True

        if event.type == ACTION_COMPLETE:
            self.show_action_result(event.payload["action_result"])
            return True

        if event.type in (TASK_COMPLETE, SHOP_PURCHASE):
            return False

        return False

    def cancel_timer_after(self):
        if self.timer_after_job is not None:
            self.window.after_cancel(self.timer_after_job)
            self.timer_after_job = None

    def close_timer_window(self):
        if self.timer_window is not None and self.timer_window.winfo_exists():
            self.timer_window.destroy()

        self.timer_window = None
        self.timer_remaining_label = None
        self.timer_status_label = None
        self.timer_pause_button = None
        self.timer_resume_button = None

    def clear_action_timer(self):
        self.timer = None
        self.timer_action_option = None

    def set_action_buttons_state(self, state):
        for button in self.action_buttons:
            button.config(state=state)

    def settle_action_immediately(self, action_name):
        self.handle_operation_result(
            self.core.execute(
                GameCommand(COMPLETE_ACTION, {"action_name": action_name})
            )
        )

    def handle_task(self, index):
        self.handle_operation_result(
            self.core.execute(GameCommand(COMPLETE_DAILY_TASK, {"index": index}))
        )

    def refresh_special_task_buttons(self):
        for row in self.special_task_rows:
            row.destroy()

        self.special_task_buttons = []
        self.special_task_rows = []
        state = self.core.get_state()

        if len(state.active_special_task_views) == 0:
            row, button, _detail_label = self.create_task_row(
                self.special_task_frame,
                "暂无特殊任务",
                "等待新的特殊任务",
                "等待"
            )
            button.config(state=tk.DISABLED, fg=self.theme["disabled_text"])
            self.special_task_rows.append(row)
            self.special_task_buttons.append(button)
            return

        for task_view in state.active_special_task_views:
            row, button, _detail_label = self.create_task_row(
                self.special_task_frame,
                task_view["name"],
                task_view["detail_text"],
                task_view["button_text"],
                command=lambda payload=task_view["command_payload"]:
                self.handle_special_task(payload["index"])
            )
            button.config(
                state=self.get_tk_state(task_view["button_state"]),
                fg=self.get_button_fg(task_view["button_state"])
            )
            self.special_task_rows.append(row)
            self.special_task_buttons.append(button)

    def handle_special_task(self, index):
        self.handle_operation_result(
            self.core.execute(
                GameCommand(COMPLETE_SPECIAL_TASK, {"index": index})
            )
        )

    def open_shop_window(self):
        if self.shop_window is not None and self.shop_window.winfo_exists():
            self.shop_window.lift()
            return

        self.shop_window = tk.Toplevel(self.window)
        self.shop_window.title("商店")
        self.shop_window.geometry("780x420")
        self.shop_window.protocol("WM_DELETE_WINDOW", self.close_shop_window)
        self.refresh_shop_window()

    def close_shop_window(self):
        if self.shop_window is not None:
            self.shop_window.destroy()
            self.shop_window = None

    def refresh_shop_window(self):
        if self.shop_window is None or not self.shop_window.winfo_exists():
            return

        state = self.core.get_state()

        for child in self.shop_window.winfo_children():
            child.destroy()

        top_frame = tk.Frame(self.shop_window)
        top_frame.pack(fill=tk.X, padx=10, pady=8)

        tk.Label(
            top_frame,
            text=state.coin_text,
            font=("Microsoft YaHei", 12)
        ).pack(side=tk.LEFT)

        content = tk.Frame(self.shop_window)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        for column, category_view in enumerate(state.shop_category_views):
            category = category_view["category"]
            category_frame = tk.Frame(content, relief=tk.GROOVE, borderwidth=1)
            category_frame.grid(row=0, column=column, sticky="nsew", padx=4)
            content.grid_columnconfigure(column, weight=1)

            tk.Label(
                category_frame,
                text=f"【{category}】",
                font=("Microsoft YaHei", 11)
            ).pack(pady=5)

            items = category_view["items"]

            if len(items) == 0:
                tk.Label(
                    category_frame,
                    text="敬请期待",
                    font=("Microsoft YaHei", 10),
                    fg="gray"
                ).pack(pady=20)
                continue

            for item in items:
                self.add_shop_item_widget(category_frame, item)

    def add_shop_item_widget(self, parent, item_view):
        item_frame = tk.Frame(parent, relief=tk.RIDGE, borderwidth=1)
        item_frame.pack(fill=tk.X, padx=5, pady=4)

        info_text = (
            f"{item_view['name']}\n"
            f"{item_view['desc']}\n"
            f"价格：{item_view['price']}金币 | "
            f"{item_view['stock_text']}"
        )

        tk.Label(
            item_frame,
            text=info_text,
            font=("Microsoft YaHei", 9),
            justify=tk.LEFT,
            anchor="w",
            wraplength=130
        ).pack(fill=tk.X, padx=5, pady=4)

        button_text = item_view["button_text"]
        tk.Button(
            item_frame,
            text=button_text,
            state=self.get_tk_state(item_view["button_state"]),
            command=lambda payload=item_view["command_payload"]:
            self.handle_buy_shop_item(payload["item_id"])
        ).pack(pady=4)

    def handle_buy_shop_item(self, item_id):
        self.handle_operation_result(
            self.core.execute(GameCommand(BUY_SHOP_ITEM, {"item_id": item_id}))
        )
        self.refresh_shop_window()

    def show_achievement(self, achievements):
        if isinstance(achievements, dict):
            achievements = [achievements]

        if self.achievement_clear_job is not None:
            self.window.after_cancel(self.achievement_clear_job)
            self.achievement_clear_job = None

        text = (
            "🏆 成就解锁！\n\n"
            + "\n".join(
                f"【{achievement.get('name', achievement.get('id', '未知成就'))}】 "
                f"{achievement.get('desc', '')} "
                f"{achievement.get('reward_text', '')}"
                for achievement in achievements
            )
        )

        self.achievement_label.config(
            text=text
        )

        self.achievement_clear_job = self.window.after(
            3000,
            lambda:
            self.achievement_label.config(text="")
        )

    def show_level_notice(self, level_up_info):
        if level_up_info is None:
            return

        if self.level_notice_clear_job is not None:
            self.window.after_cancel(self.level_notice_clear_job)
            self.level_notice_clear_job = None

        self.level_notice_label.config(
            text=f"等级提升：Lv.{level_up_info['after_level']}"
        )

        self.level_notice_clear_job = self.window.after(
            2500,
            lambda:
            self.level_notice_label.config(text="")
        )

    def open_achievement_window(self):
        state = self.core.get_state()
        window = tk.Toplevel(self.window)
        window.title("成就列表")
        window.geometry("620x420")

        unlocked_frame = tk.Frame(window)
        unlocked_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        locked_frame = tk.Frame(window)
        locked_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(
            unlocked_frame,
            text="已获取",
            font=("Microsoft YaHei", 12)
        ).pack()

        tk.Label(
            locked_frame,
            text="未获取",
            font=("Microsoft YaHei", 12)
        ).pack()

        unlocked_text = tk.Text(unlocked_frame, width=35, height=20)
        unlocked_text.pack(fill=tk.BOTH, expand=True)

        locked_text = tk.Text(locked_frame, width=35, height=20)
        locked_text.pack(fill=tk.BOTH, expand=True)

        text_by_section = {
            "unlocked": unlocked_text,
            "locked": locked_text,
        }
        for section in state.achievement_sections:
            target = text_by_section[section["id"]]
            for achievement_view in section["items"]:
                target.insert(
                    tk.END,
                    achievement_view["display_text"] + "\n\n"
                )

        if unlocked_text.get("1.0", tk.END).strip() == "":
            unlocked_text.insert(tk.END, "暂时还没有获取成就。")

        if locked_text.get("1.0", tk.END).strip() == "":
            locked_text.insert(tk.END, "所有成就都已获取。")

        unlocked_text.config(state=tk.DISABLED)
        locked_text.config(state=tk.DISABLED)

    def get_achievement_condition_text(self, achievement):
        for section in self.core.get_state().achievement_sections:
            for achievement_view in section["items"]:
                if achievement_view["id"] == achievement.get("id"):
                    return achievement_view["condition_text"]

        return "未知条件"

    def open_title_window(self):
        state = self.core.get_state()
        window = tk.Toplevel(self.window)
        window.title("称号列表")
        window.geometry("680x480")

        container = tk.Frame(window)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        content = tk.Frame(canvas)
        content.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for title_view in state.title_views:
            title_id = title_view["id"]

            row_frame = tk.Frame(content, relief=tk.GROOVE, borderwidth=1)
            row_frame.pack(fill=tk.X, pady=4)

            tk.Label(
                row_frame,
                text=title_view["display_text"],
                font=("Microsoft YaHei", 10),
                justify=tk.LEFT,
                anchor="w"
            ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=6)

            button = tk.Button(
                row_frame,
                text=title_view["button_text"],
                state=self.get_tk_state(title_view["button_state"]),
                width=8,
                command=lambda payload=title_view["command_payload"],
                current_window=window:
                self.handle_equip_title(payload["title_id"], current_window)
            )

            button.pack(side=tk.RIGHT, padx=8)

        if len(state.title_views) == 0:
            tk.Label(
                content,
                text="还没有配置称号。",
                font=("Microsoft YaHei", 12)
            ).pack(pady=20)

    def handle_equip_title(self, title_id, window):
        result = self.core.execute(GameCommand(EQUIP_TITLE, {"title_id": title_id}))
        if result.success:
            self.update_display()
            window.destroy()
            self.open_title_window()
        else:
            self.handle_operation_result(result)

    def get_title_condition_text(self, title):
        for title_view in self.core.get_state().title_views:
            if title_view["id"] == title.get("id"):
                return title_view["condition_text"]

        return "未知条件"

    def show_title_unlock(self, titles):
        if isinstance(titles, dict):
            titles = [titles]

        if self.achievement_clear_job is not None:
            self.window.after_cancel(self.achievement_clear_job)
            self.achievement_clear_job = None

        text = (
            "🎖 称号解锁！\n\n"
            + "\n".join(
                f"【{title.get('name', title.get('id', '未知称号'))}】 "
                f"{title.get('desc', '')} "
                f"{title.get('bonus_text', '')}"
                for title in titles
            )
        )

        self.achievement_label.config(
            text=text
        )

        self.achievement_clear_job = self.window.after(
            3000,
            lambda:
            self.achievement_label.config(text="")
        )

    def update_display(self):
        state = self.core.get_state()
        self.energy_label.config(
            text=state.energy_text
        )
        self.energy_bar["maximum"] = state.energy_max
        self.energy_bar["value"] = state.energy_value
        self.history_text.delete("1.0", tk.END)
        self.exp_label.config(text=state.exp_text)
        self.level_label.config(text=state.level_text)
        self.coin_label.config(
            text=state.coin_text
        )
        self.title_label.config(text=state.title_text)

        if len(state.logs) == 0:
            self.history_text.insert(tk.END, "今天还没有行动记录喵")
        else:
            for item in state.logs:
                self.history_text.insert(tk.END, item + "\n")

        for index, task_view in enumerate(state.active_task_views):
            if index < len(self.task_status_labels):
                self.task_status_labels[index].config(
                    text=task_view["detail_text"]
                )
            if index < len(self.task_buttons):
                self.task_buttons[index].config(
                    text=task_view["button_text"],
                    state=self.get_tk_state(task_view["button_state"]),
                    fg=self.get_button_fg(task_view["button_state"])
                )

        self.refresh_special_task_buttons()

    def get_title_bonus_text(self, title):
        for title_view in self.core.get_state().title_views:
            if title_view["id"] == title.get("id"):
                return title_view["bonus_text"]

        return "无加成"

    def get_title_condition_text(self, title):
        for title_view in self.core.get_state().title_views:
            if title_view["id"] == title.get("id"):
                return title_view["condition_text"]

        return "未知条件"

    def run(self):
        self.update_display()

        self.window.mainloop()
