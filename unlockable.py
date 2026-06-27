from utils.json_store import file_exists, load_json


class UnlockableSystem:
    def __init__(self, player, data_file):
        self.player = player
        self.data_file = data_file
        self.items = self.load()

    def load(self):
        if not file_exists(self.data_file):
            return []

        return load_json(self.data_file)

    def check(self, context=None):
        unlocked = []

        for item in self.items:
            item_id = item.get("id")

            if not item_id:
                continue

            if self.is_unlocked(item_id):
                continue

            if self.is_done(item, context):
                unlocked.append(item)

        return unlocked

    def unlock(self, item):
        item_id = item.get("id")

        if not item_id:
            return False

        if self.is_unlocked(item_id):
            return False

        return True

    def is_unlocked(self, item_or_id):
        item_id = (
            item_or_id.get("id")
            if isinstance(item_or_id, dict)
            else item_or_id
        )
        return item_id in self.get_unlocked_ids()

    def get_unlocked_ids(self):
        raise NotImplementedError

    def is_done(self, item, context=None):
        raise NotImplementedError
