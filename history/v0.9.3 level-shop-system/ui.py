import tkinter as tk
from tkinter import ttk
import json

from achievement import Achievement
from level import Level
from player import Otaku
from shop import ShopManager
from task import SpecialTaskManager, TaskManager
from title import Title


class GameUI:
    def __init__(self):
        self.config = self.load_config()
        self.player = Otaku(self.config)
        self.actions = self.load_actions()
        self.task_manager = TaskManager()
        self.special_task_manager = SpecialTaskManager(self.player.special_task_slots)
        self.shop_manager = ShopManager(self.player)
        self.window = tk.Tk()
        self.window.title(self.config["window_title"])
        self.window.geometry(self.config["window_size"])
        self.task_buttons = []
        self.special_task_buttons = []
        self.level_system = Level()
        self.title_system = Title(self.player)
        self.achievement_manager = Achievement(self.player)
        self.achievement_clear_job = None
        self.level_notice_clear_job = None
        self.shop_window = None

        self.window_title_label = tk.Label(
            self.window,
            text=self.config["window_title"],
            font=("Microsoft YaHei", 18)
        )

        self.window_title_label.pack(pady=15)

        self.energy_frame = tk.Frame(self.window)
        self.energy_frame.pack()

        self.energy_label = tk.Label(
            self.energy_frame,
            text=f"宅宅能量：{self.player.energy}/{self.config['max_energy']}",
            font=("Microsoft YaHei", 14)
        )
        self.energy_label.pack(side=tk.LEFT, padx=5)

        self.energy_bar = ttk.Progressbar(
            self.energy_frame,
            length=250,
            maximum=self.config["max_energy"],
            value=self.player.energy
        )
        self.energy_bar.pack(side=tk.LEFT, padx=5)

        self.level_label = tk.Label(
            self.window,
            text=self.level_system.get_level_text(self.player.exp),
            font=("Microsoft YaHei", 14)
        )
        self.level_label.pack()

        self.exp_label = tk.Label(
            self.window,
            text=self.level_system.get_exp_text(self.player.exp),
            font=("Microsoft YaHei", 14)
        )
        self.exp_label.pack()

        self.coin_label = tk.Label(
            self.window,
            text=f"金币：{self.player.coin}",
            font=("Microsoft YaHei", 14)
        )
        self.coin_label.pack()

        self.title_label = tk.Label(
            self.window,
            text="称号：无",
            font=("Microsoft YaHei", 14)
        )
        self.title_label.pack()

        self.title_button = tk.Button(
            self.window,
            text="查看称号",
            command=self.open_title_window
        )
        self.title_button.pack(pady=3)

        self.achievement_button = tk.Button(
            self.window,
            text="查看成就",
            command=self.open_achievement_window
        )
        self.achievement_button.pack(pady=3)

        self.shop_button = tk.Button(
            self.window,
            text="商店",
            command=self.open_shop_window
        )
        self.shop_button.pack(pady=3)

        self.achievement_label = tk.Label(
            self.window,
            text="",
            font=("Microsoft YaHei", 12),
            fg="gold",
            justify="center"
        )

        self.achievement_label.pack(pady=5)

        self.level_notice_label = tk.Label(
            self.window,
            text="",
            font=("Microsoft YaHei", 10),
            fg="gray",
            justify="center"
        )
        self.level_notice_label.pack()

        unlocked_titles = self.title_system.check_titles(self.task_manager.all_tasks)
        if unlocked_titles:
            self.show_title_unlock(unlocked_titles)

        self.action_frame = tk.Frame(self.window)
        self.action_frame.pack(pady=5)

        action_columns = 3

        for index, (action_name, action_info) in enumerate(self.actions.items()):
            change = action_info["energy_change"]
            row = index // action_columns
            column = index % action_columns

            button = tk.Button(
                self.action_frame,
                text=f"{action_name} {change:+}",
                width=10,
                command=lambda name=action_name: self.handle_action(name)
            )
            button.grid(row=row, column=column, padx=5, pady=3)

        self.task_area = tk.Frame(self.window)
        self.task_area.pack(pady=10)

        self.daily_task_frame = tk.Frame(self.task_area)
        self.daily_task_frame.pack(side=tk.LEFT, padx=10)

        self.special_task_frame = tk.Frame(self.task_area)
        self.special_task_frame.pack(side=tk.LEFT, padx=10, anchor="n")

        self.task_label = tk.Label(
            self.daily_task_frame,
            text="每日任务",
            font=("Microsoft YaHei", 12)
        )
        self.task_label.pack()

        for index, task in enumerate(self.task_manager.tasks):
            button_text = self.get_task_button_text(task)

            button = tk.Button(
                self.daily_task_frame,
                text=button_text,
                command=lambda i=index: self.handle_task(i)
            )
            button.pack()

            self.task_buttons.append(button)

        self.special_task_label = tk.Label(
            self.special_task_frame,
            text="特殊任务",
            font=("Microsoft YaHei", 12)
        )
        self.special_task_label.pack()

        self.refresh_special_task_buttons()

        self.history_label = tk.Label(
            self.window,
            text="行动记录",
            font=("Microsoft YaHei", 12)
        )
        self.history_label.pack()

        self.history_text = tk.Text(
            self.window,
            height=10,
            width=70
        )
        self.history_text.pack()

    def load_actions(self):
        with open("actions.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def handle_action(self, action_name):
        before_exp = self.player.exp

        self.player.do_action(
            action_name,
            self.actions,
            self.title_system.get_energy_bonus_rate()
        )

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

    def apply_task_exp_bonus(self, exp):
        final_exp = self.title_system.apply_exp_bonus(exp)
        final_exp *= self.shop_manager.get_task_exp_multiplier()

        return final_exp

    def handle_task(self, index):
        task = self.task_manager.tasks[index]
        reward, exp = self.task_manager.finish_task(index)
        before_exp = self.player.exp

        if reward > 0 or exp > 0:
            final_reward = self.title_system.apply_energy_bonus(reward)
            final_exp = self.apply_task_exp_bonus(exp)
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

    def refresh_special_task_buttons(self):
        for button in self.special_task_buttons:
            button.destroy()

        self.special_task_buttons = []

        if len(self.special_task_manager.tasks) == 0:
            button = tk.Button(
                self.special_task_frame,
                text="暂无特殊任务",
                state=tk.DISABLED
            )
            button.pack()
            self.special_task_buttons.append(button)
            return

        for index, task in enumerate(self.special_task_manager.tasks):
            button = tk.Button(
                self.special_task_frame,
                text=self.get_special_task_button_text(task),
                command=lambda i=index: self.handle_special_task(i)
            )
            button.pack()
            self.special_task_buttons.append(button)

    def handle_special_task(self, index):
        if index < 0 or index >= len(self.special_task_manager.tasks):
            return

        task = self.special_task_manager.tasks[index]
        coin, exp = self.special_task_manager.finish_task(index)
        before_exp = self.player.exp

        if coin > 0 or exp > 0:
            final_exp = self.apply_task_exp_bonus(exp)
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
                f"EXP +{achievement.get('reward_exp', 0)}"
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
        reward_exp = achievement.get("reward_exp", 0)

        return (
            f"【{name}】\n"
            f"{desc}\n"
            f"条件：{condition}\n"
            f"奖励：EXP +{reward_exp}"
        )

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

        return "未知条件"

    def open_title_window(self):
        window = tk.Toplevel(self.window)
        window.title("称号列表")
        window.geometry("680x480")

        content = tk.Frame(window)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

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
            self.task_buttons[index].config(
                text=self.get_task_button_text(task)
            )

        self.refresh_special_task_buttons()

    def load_config(self):
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def get_title_bonus_text(self, title):
        bonus_type = title.get("bonus_type")
        bonus_value = title.get("bonus_value", 0)

        if bonus_type == "exp_rate":
            return f"经验 +{int(bonus_value * 100)}%"

        if bonus_type == "energy_change_rate":
            return f"能量变化 +{int(bonus_value * 100)}%"

        return "无加成"

    def run(self):
        self.update_display()

        self.window.mainloop()
