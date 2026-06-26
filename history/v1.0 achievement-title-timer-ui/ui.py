import tkinter as tk
from tkinter import messagebox, ttk
import json

from achievement import Achievement
from level import Level
from player import Otaku
from shop import ShopManager
from task import SpecialTaskManager, TaskManager
from themes import FONTS, SIZES, SPACING, get_theme
from title import Title


POSITIVE_ACTION_OPTIONS = [
    {"minutes": 25, "multiplier": 1, "exp": 0},
    {"minutes": 45, "multiplier": 1.5, "exp": 0},
    {"minutes": 60, "multiplier": 2, "exp": 0},
]

NEGATIVE_ACTION_OPTIONS = [
    {"minutes": 30, "multiplier": 1, "exp": 1},
    {"minutes": 60, "multiplier": 1.5, "exp": 2},
    {"minutes": 90, "multiplier": 2, "exp": 3},
]


def get_action_duration_options(action_info):
    energy_change = action_info.get("energy_change", 0)

    if energy_change >= 0:
        return POSITIVE_ACTION_OPTIONS

    return NEGATIVE_ACTION_OPTIONS


class ActionTimerState:
    def __init__(self, action_name, duration_minutes, total_seconds=None):
        self.action_name = action_name
        self.duration_minutes = duration_minutes
        self.total_seconds = (
            total_seconds
            if total_seconds is not None
            else duration_minutes * 60
        )
        self.remaining_seconds = self.total_seconds
        self.paused = False
        self.cancelled = False

    def tick(self):
        if self.paused or self.cancelled or self.is_finished():
            return False

        self.remaining_seconds -= 1
        return True

    def pause(self):
        self.paused = True

    def resume(self):
        if not self.cancelled:
            self.paused = False

    def cancel(self):
        self.cancelled = True
        self.paused = False

    def is_finished(self):
        return self.remaining_seconds <= 0

    def elapsed_minutes(self):
        elapsed_seconds = self.total_seconds - self.remaining_seconds
        return elapsed_seconds // 60

    def format_remaining(self):
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"


class GameUI:
    def __init__(self):
        self.config = self.load_config()
        self.theme = get_theme(self.config.get("theme", "default"))
        self.player = Otaku(self.config)
        self.actions = self.load_actions()
        self.task_manager = TaskManager()
        self.special_task_manager = SpecialTaskManager(self.player.special_task_slots)
        self.shop_manager = ShopManager(self.player)
        self.window = tk.Tk()
        self.window.title(self.config["window_title"])
        self.window.geometry(self.config["window_size"])
        self.action_buttons = []
        self.task_buttons = []
        self.task_status_labels = []
        self.special_task_buttons = []
        self.special_task_rows = []
        self.level_system = Level()
        self.title_system = Title(self.player)
        self.achievement_manager = Achievement(self.player, level_system=self.level_system)
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

        unlocked_titles = self.title_system.check_titles(self.task_manager.all_tasks)
        if unlocked_titles:
            self.show_title_unlock(unlocked_titles)

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
        self.window_title_label = tk.Label(
            self.window,
            text=self.config["window_title"],
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
            text=f"宅宅能量：{self.player.energy}/{self.config['max_energy']}",
            font=FONTS["status"],
            bg=self.theme["card_bg"],
            fg=self.theme["text"]
        )
        self.energy_label.pack(side=tk.LEFT, padx=(0, SPACING["sm"]))

        self.energy_bar = ttk.Progressbar(
            self.energy_frame,
            length=150,
            maximum=self.config["max_energy"],
            value=self.player.energy
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
            text=self.level_system.get_level_text(self.player.exp),
            font=FONTS["status"],
            bg=self.theme["card_bg"],
            fg=self.theme["text"]
        )
        self.level_label.pack(side=tk.LEFT, padx=(0, SPACING["md"]))

        self.exp_label = tk.Label(
            self.meta_frame,
            text=self.level_system.get_exp_text(self.player.exp),
            font=FONTS["status"],
            bg=self.theme["card_bg"],
            fg=self.theme["text"]
        )
        self.exp_label.pack(side=tk.LEFT, padx=(0, SPACING["md"]))

        self.coin_label = tk.Label(
            self.meta_frame,
            text=f"金币：{self.player.coin}",
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
        self.create_action_group("正向行动", lambda change: change > 0, 0)
        self.create_action_group("娱乐行动", lambda change: change < 0, 1)

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

        for index, task in enumerate(self.task_manager.tasks):
            row, button, detail_label = self.create_task_row(
                self.daily_task_frame,
                task.name,
                self.get_task_detail_text(task),
                self.get_task_action_text(task),
                command=lambda i=index: self.handle_task(i)
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

    def create_action_group(self, title, predicate, column):
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

        for action_name, action_info in self.actions.items():
            change = action_info["energy_change"]
            if not predicate(change):
                continue

            button = self.create_action_button(button_row, action_name, change)
            button.pack(side=tk.LEFT, padx=(0, SPACING["sm"]), pady=SPACING["xs"])
            self.action_buttons.append(button)

    def load_actions(self):
        with open("actions.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def handle_action(self, action_name):
        if self.is_action_timer_running():
            self.level_notice_label.config(text="已有行动计时正在进行")
            return

        self.open_action_duration_window(action_name)

    def is_action_timer_running(self):
        return self.timer is not None and not self.timer.cancelled

    def open_action_duration_window(self, action_name):
        action_info = self.actions[action_name]
        options = get_action_duration_options(action_info)
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
            minutes = option["minutes"]
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

    def start_action_timer(self, action_name, option, selection_window=None):
        if self.is_action_timer_running():
            self.level_notice_label.config(text="已有行动计时正在进行")
            return

        if selection_window is not None and selection_window.winfo_exists():
            selection_window.destroy()

        self.timer = ActionTimerState(action_name, option["minutes"])
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
        self.player.save_abandoned_action_log(
            self.timer.action_name,
            self.timer.elapsed_minutes()
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
        before_exp = self.player.exp
        base_change = round(
            self.actions[timer.action_name]["energy_change"] * option["multiplier"]
        )
        final_energy_change = self.title_system.apply_action_energy_bonus(
            timer.action_name,
            base_change
        )
        final_exp = self.title_system.apply_action_exp_bonus(
            timer.action_name,
            option["exp"]
        )
        result = self.player.complete_timed_action(
            timer.action_name,
            self.actions,
            option["minutes"],
            option["multiplier"],
            final_exp,
            energy_change_override=final_energy_change
        )

        unlocked = self.achievement_manager.check_achievements()
        unlocked_titles = self.title_system.check_titles(self.task_manager.all_tasks)

        if unlocked:
            self.show_achievement(unlocked)

        if unlocked_titles:
            self.show_title_unlock(unlocked_titles)

        self.show_level_notice_if_needed(before_exp)
        self.close_timer_window()
        self.clear_action_timer()
        self.set_action_buttons_state(tk.NORMAL)
        self.update_display()
        self.show_action_result(result)

    def show_action_result(self, result):
        lines = [
            f"本次行动：{result['action_name']}",
            f"持续时间：{result['duration_minutes']}分钟",
            f"能量：{result['energy_change']:+}"
        ]

        if result["exp_change"]:
            lines.append(f"经验：+{result['exp_change']}")

        messagebox.showinfo("行动完成", "\n".join(lines))

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
        before_exp = self.player.exp
        base_change = self.actions[action_name]["energy_change"]
        final_change = self.title_system.apply_action_energy_bonus(action_name, base_change)
        self.player.energy += final_change
        self.player.energy = max(0, min(self.config["max_energy"], self.player.energy))
        self.player.action_counts[action_name] = (
            self.player.action_counts.get(action_name, 0) + 1
        )
        self.player.save_state()
        self.player.save_log(action_name, final_change)

        unlocked = (
            self.achievement_manager
            .check_achievements()
        )
        unlocked_titles = self.title_system.check_titles(self.task_manager.all_tasks)

        if unlocked:
            self.show_achievement(
                unlocked
            )

        if unlocked_titles:
            self.show_title_unlock(unlocked_titles)

        self.show_level_notice_if_needed(before_exp)

        self.update_display()

    def get_task_button_text(self, task):
        status = "已完成" if task.done else "未完成"

        return f"{task.name} | 奖励 {task.reward:+} | {status}"

    def get_task_detail_text(self, task):
        status = "已完成" if task.done else "未完成"
        return f"能量 {task.reward:+} / EXP +{task.exp} / {status}"

    def get_task_action_text(self, task):
        return "已完成" if task.done else "完成"

    def apply_task_exp_bonus(self, exp, task_id=None, source="daily"):
        final_exp = self.title_system.apply_task_exp_bonus(exp, task_id, source)
        final_exp *= self.shop_manager.get_task_exp_multiplier()

        return final_exp

    def handle_task(self, index):
        task = self.task_manager.tasks[index]
        reward, exp = self.task_manager.finish_task(index)
        before_exp = self.player.exp

        if reward > 0 or exp > 0:
            final_reward = self.title_system.apply_energy_bonus(reward)
            final_exp = self.apply_task_exp_bonus(exp, task.id, "daily")
            self.player.add_reward(final_reward, final_exp, task.name)

        unlocked = self.achievement_manager.check_achievements()
        unlocked_titles = self.title_system.check_titles(self.task_manager.all_tasks)

        if unlocked:
            self.show_achievement(unlocked)

        if unlocked_titles:
            self.show_title_unlock(unlocked_titles)

        self.show_level_notice_if_needed(before_exp)

        self.update_display()

    def get_special_task_button_text(self, task):
        status = "已完成" if task.done else "未完成"
        return f"{task.name} | 金币 +{task.coin} | {status}"

    def get_special_task_detail_text(self, task):
        status = "已完成" if task.done else "未完成"
        return f"金币 +{task.coin} / EXP +{task.exp} / {status}"

    def get_special_task_action_text(self, task):
        return "已完成" if task.done else "完成"

    def refresh_special_task_buttons(self):
        for row in self.special_task_rows:
            row.destroy()

        self.special_task_buttons = []
        self.special_task_rows = []

        if len(self.special_task_manager.tasks) == 0:
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

        for index, task in enumerate(self.special_task_manager.tasks):
            row, button, _detail_label = self.create_task_row(
                self.special_task_frame,
                task.name,
                self.get_special_task_detail_text(task),
                self.get_special_task_action_text(task),
                command=lambda i=index: self.handle_special_task(i)
            )
            if task.done:
                button.config(state=tk.DISABLED, fg=self.theme["disabled_text"])
            self.special_task_rows.append(row)
            self.special_task_buttons.append(button)

    def handle_special_task(self, index):
        if index < 0 or index >= len(self.special_task_manager.tasks):
            return

        task = self.special_task_manager.tasks[index]
        coin, exp = self.special_task_manager.finish_task(index)
        before_exp = self.player.exp

        if coin > 0 or exp > 0:
            final_exp = self.apply_task_exp_bonus(exp, task.id, "special")
            self.player.add_special_reward(coin, final_exp, task.name)

        unlocked = self.achievement_manager.check_achievements()
        unlocked_titles = self.title_system.check_titles(self.task_manager.all_tasks)

        if unlocked:
            self.show_achievement(unlocked)

        if unlocked_titles:
            self.show_title_unlock(unlocked_titles)

        self.show_level_notice_if_needed(before_exp)

        self.update_display()

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

        for child in self.shop_window.winfo_children():
            child.destroy()

        top_frame = tk.Frame(self.shop_window)
        top_frame.pack(fill=tk.X, padx=10, pady=8)

        tk.Label(
            top_frame,
            text=f"当前金币：{self.player.coin}",
            font=("Microsoft YaHei", 12)
        ).pack(side=tk.LEFT)

        content = tk.Frame(self.shop_window)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        for column, category in enumerate(self.shop_manager.categories):
            category_frame = tk.Frame(content, relief=tk.GROOVE, borderwidth=1)
            category_frame.grid(row=0, column=column, sticky="nsew", padx=4)
            content.grid_columnconfigure(column, weight=1)

            tk.Label(
                category_frame,
                text=f"【{category}】",
                font=("Microsoft YaHei", 11)
            ).pack(pady=5)

            items = self.shop_manager.get_items_by_category(category)

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

    def add_shop_item_widget(self, parent, item):
        item_frame = tk.Frame(parent, relief=tk.RIDGE, borderwidth=1)
        item_frame.pack(fill=tk.X, padx=5, pady=4)

        info_text = (
            f"{item.get('name', '未知商品')}\n"
            f"{item.get('desc', '')}\n"
            f"价格：{item.get('price', 0)}金币 | "
            f"{self.shop_manager.get_stock_text(item)}"
        )

        tk.Label(
            item_frame,
            text=info_text,
            font=("Microsoft YaHei", 9),
            justify=tk.LEFT,
            anchor="w",
            wraplength=130
        ).pack(fill=tk.X, padx=5, pady=4)

        item_id = item.get("id")
        button_text = self.shop_manager.get_button_state_text(item)
        button_state = (
            tk.NORMAL
            if self.shop_manager.can_buy(item_id)
            else tk.DISABLED
        )

        tk.Button(
            item_frame,
            text=button_text,
            state=button_state,
            command=lambda value=item_id: self.handle_buy_shop_item(value)
        ).pack(pady=4)

    def handle_buy_shop_item(self, item_id):
        result = self.shop_manager.buy_item(item_id)

        if not result.get("success"):
            self.level_notice_label.config(text=result.get("message", "购买失败"))
            return

        item = result["item"]
        self.player.save_log(
            f"购买商品：{item.get('name', item_id)}",
            f"金币-{item.get('price', 0)}"
        )

        if result.get("effect_type") == "refresh_daily_tasks":
            self.task_manager.redraw_daily_tasks()

        if result.get("effect_type") == "special_task_slot":
            self.special_task_manager.set_slot_count(self.player.special_task_slots)

        self.level_notice_label.config(text=result.get("message", "购买成功"))
        self.update_display()
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
                f"{self.get_achievement_reward_text(achievement)}"
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

    def show_level_notice_if_needed(self, before_exp):
        level_up_info = self.level_system.get_level_up_info(
            before_exp,
            self.player.exp
        )

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

        unlocked_ids = set(self.player.unlocked_achievements)

        for achievement in self.achievement_manager.achievements:
            line = self.get_achievement_display_text(achievement)

            if achievement.get("id") in unlocked_ids:
                unlocked_text.insert(tk.END, line + "\n\n")
            else:
                locked_text.insert(tk.END, line + "\n\n")

        if unlocked_text.get("1.0", tk.END).strip() == "":
            unlocked_text.insert(tk.END, "暂时还没有获取成就。")

        if locked_text.get("1.0", tk.END).strip() == "":
            locked_text.insert(tk.END, "所有成就都已获取。")

        unlocked_text.config(state=tk.DISABLED)
        locked_text.config(state=tk.DISABLED)

    def get_achievement_display_text(self, achievement):
        name = achievement.get("name", achievement.get("id", "未知成就"))
        desc = achievement.get("desc", "")
        condition = self.get_achievement_condition_text(achievement)

        return (
            f"【{name}】\n"
            f"{desc}\n"
            f"条件：{condition}\n"
            f"奖励：{self.get_achievement_reward_text(achievement)}"
        )

    def get_achievement_reward_text(self, achievement):
        rewards = []
        reward_coin = achievement.get("reward_coin", 0)
        reward_exp = achievement.get("reward_exp", 0)

        if reward_coin:
            rewards.append(f"金币 +{reward_coin}")

        if reward_exp:
            rewards.append(f"EXP +{reward_exp}")

        if len(rewards) == 0:
            return "无"

        return " ".join(rewards)

    def get_achievement_condition_text(self, achievement):
        condition_type = achievement.get("condition_type")
        target_value = achievement.get("target_value")

        if condition_type == "energy_reach":
            return f"能量达到 {target_value}"

        if condition_type == "task_done_count":
            return f"完成任务 {target_value} 次"

        if condition_type == "action_count":
            action_name = achievement.get("target_action", "指定行动")
            return f"{action_name} {target_value} 次"

        if condition_type == "total_action_count":
            return f"执行任意行动 {target_value} 次"

        if condition_type == "special_task_done_count":
            return f"完成特殊任务 {target_value} 次"

        if condition_type == "level":
            return f"达到 Lv.{target_value}"

        if condition_type == "task_combo":
            return "完成指定普通任务与特殊任务组合"

        return "未知条件"

    def open_title_window(self):
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

        unlocked_ids = set(self.player.unlocked_titles)

        for index, title in enumerate(self.title_system.titles):
            title_id = title.get("id", "")
            is_unlocked = title_id in unlocked_ids
            is_equipped = title_id == self.player.equipped_title

            row_frame = tk.Frame(content, relief=tk.GROOVE, borderwidth=1)
            row_frame.pack(fill=tk.X, pady=4)

            info_text = self.get_title_display_text(title, is_unlocked)

            tk.Label(
                row_frame,
                text=info_text,
                font=("Microsoft YaHei", 10),
                justify=tk.LEFT,
                anchor="w"
            ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=6)

            if is_equipped:
                button = tk.Button(
                    row_frame,
                    text="已佩戴",
                    state=tk.DISABLED,
                    width=8
                )
            elif is_unlocked:
                button = tk.Button(
                    row_frame,
                    text="佩戴",
                    width=8,
                    command=lambda value=title_id, current_window=window:
                    self.handle_equip_title(value, current_window)
                )
            else:
                button = tk.Button(
                    row_frame,
                    text="未解锁",
                    state=tk.DISABLED,
                    width=8
                )

            button.pack(side=tk.RIGHT, padx=8)

        if len(self.title_system.titles) == 0:
            tk.Label(
                content,
                text="还没有配置称号。",
                font=("Microsoft YaHei", 12)
            ).pack(pady=20)

    def handle_equip_title(self, title_id, window):
        if self.title_system.equip_title(title_id):
            self.update_display()
            window.destroy()
            self.open_title_window()

    def get_title_display_text(self, title, is_unlocked):
        name = title.get("name", title.get("id", "未知称号"))
        desc = title.get("desc", "")
        condition = self.get_title_condition_text(title)
        bonus = self.get_title_bonus_text(title)
        status = "已解锁" if is_unlocked else "未解锁"

        return (
            f"【{name}】 {status}\n"
            f"{desc}\n"
            f"条件：{condition}\n"
            f"效果：{bonus}"
        )

    def get_title_condition_text(self, title):
        condition_type = title.get("condition_type")
        target_value = title.get("target_value")

        if condition_type == "always":
            return "默认解锁"

        if condition_type == "task_completed_count":
            return f"累计完成任务 {target_value} 次"

        if condition_type == "task_done_count":
            return f"完成任务 {target_value} 次"

        if condition_type == "energy_reach":
            return f"能量达到 {target_value}"

        if condition_type == "action_count":
            action_name = title.get("target_action", "指定行动")
            return f"{action_name} {target_value} 次"

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
                f"{self.get_title_bonus_text(title)}"
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
        logs = self.player.load_log()
        self.energy_label.config(
            text=f"宅宅能量：{self.player.energy}/{self.config['max_energy']}"
        )
        self.energy_bar["value"] = self.player.energy
        self.history_text.delete("1.0", tk.END)
        self.exp_label.config(
            text=self.level_system.get_exp_text(self.player.exp)
        )
        self.level_label.config(
            text=self.level_system.get_level_text(self.player.exp)
        )
        self.coin_label.config(
            text=f"金币：{self.player.coin}"
        )
        title = self.title_system.get_title_name()
        bonus_text = self.title_system.get_bonus_text()
        self.title_label.config(
            text=f"称号：{title} {bonus_text}"
        )

        if len(logs) == 0:
            self.history_text.insert(tk.END, "今天还没有行动记录喵")
        else:
            for item in logs:
                self.history_text.insert(tk.END, item + "\n")

        for index, task in enumerate(self.task_manager.tasks):
            if index < len(self.task_status_labels):
                self.task_status_labels[index].config(
                    text=self.get_task_detail_text(task)
                )
            if index < len(self.task_buttons):
                state = tk.DISABLED if task.done else tk.NORMAL
                fg = (
                    self.theme["disabled_text"]
                    if task.done
                    else self.theme["button_text"]
                )
                self.task_buttons[index].config(
                    text=self.get_task_action_text(task),
                    state=state,
                    fg=fg
                )

        self.refresh_special_task_buttons()

    def load_config(self):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)

        config.setdefault("theme", "default")
        return config

    def get_title_bonus_text(self, title):
        bonus_type = title.get("bonus_type")
        bonus_value = title.get("bonus_value", 0)

        if bonus_type == "exp_rate":
            return f"经验 +{int(bonus_value * 100)}%"

        if bonus_type == "energy_change_rate":
            return f"能量变化 +{int(bonus_value * 100)}%"

        return "无加成"

    def get_title_condition_text(self, title):
        return self.title_system.get_title_condition_text(title)

    def get_title_bonus_text(self, title):
        return self.title_system.get_title_bonus_text(title)

    def run(self):
        self.update_display()

        self.window.mainloop()
