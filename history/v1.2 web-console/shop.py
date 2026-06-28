from repositories.player_repository import save_player_state
from services.player_service import (
    apply_shop_effect,
    record_shop_purchase,
    spend_coin,
)
from utils.json_store import load_json
from utils.time_utils import get_today_str


class ShopManager:
    def __init__(self, player, shop_file="shop.json", today_func=None):
        self.player = player
        self.shop_file = shop_file
        self.today_func = today_func or self.get_today
        self.shop_data = self.load_shop()
        self.categories = self.shop_data.get(
            "categories",
            ["任务", "成长", "称号", "娱乐", "收藏"]
        )
        self.items = self.shop_data.get("items", [])

    def get_today(self):
        return get_today_str()

    def load_shop(self):
        return load_json(self.shop_file)

    def get_item(self, item_id):
        for item in self.items:
            if item.get("id") == item_id:
                return item

        return None

    def get_items_by_category(self, category):
        return [
            item for item in self.items
            if item.get("category") == category
        ]

    def is_unlocked(self, item):
        return True

    def get_daily_purchase_count(self, item_id):
        today = self.today_func()
        daily_purchases = self.player.shop_daily_purchases.get(today, {})

        return daily_purchases.get(item_id, 0)

    def get_total_purchase_count(self, item_id):
        return self.player.shop_total_purchases.get(item_id, 0)

    def is_sold_out(self, item):
        stock_type = item.get("stock_type", "infinite")
        item_id = item.get("id")

        if stock_type == "daily":
            return self.get_daily_purchase_count(item_id) >= 1

        if stock_type == "permanent":
            return self.get_total_purchase_count(item_id) >= 1

        return False

    def can_buy(self, item_id):
        item = self.get_item(item_id)

        if item is None:
            return False

        if not self.is_unlocked(item):
            return False

        if self.is_sold_out(item):
            return False

        return self.player.coin >= item.get("price", 0)

    def get_stock_text(self, item):
        stock_type = item.get("stock_type", "infinite")

        if stock_type == "daily":
            return "每日限购"

        if stock_type == "permanent":
            return "永久限购"

        return "无限供应"

    def get_button_state_text(self, item):
        if not self.is_unlocked(item):
            return "未解禁"

        if self.is_sold_out(item):
            if item.get("stock_type") == "daily":
                return "今日已购"

            if item.get("stock_type") == "permanent":
                return "已购买"

            return "售罄"

        if self.player.coin < item.get("price", 0):
            return "金币不足"

        return "购买"

    def buy_item(self, item_id):
        item = self.get_item(item_id)

        if item is None:
            return {
                "success": False,
                "message": "商品不存在"
            }

        if not self.is_unlocked(item):
            return {
                "success": False,
                "message": "商品未解禁"
            }

        if self.is_sold_out(item):
            return {
                "success": False,
                "message": "商品已达购买上限"
            }

        price = item.get("price", 0)

        if not spend_coin(self.player, price):
            return {
                "success": False,
                "message": "金币不足"
            }

        self.record_purchase(item)
        self.apply_effect(item)
        save_player_state(self.player)

        return {
            "success": True,
            "message": "购买成功",
            "item": item,
            "effect_type": item.get("effect_type"),
            "effect_value": item.get("effect_value", 0)
        }

    def record_purchase(self, item):
        record_shop_purchase(self.player, item, self.today_func())

    def apply_effect(self, item):
        apply_shop_effect(self.player, item, self.today_func())

    def get_task_exp_multiplier(self):
        if self.player.daily_double_exp_date == self.today_func():
            return 2

        return 1
