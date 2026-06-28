import json

from utils.paths import resolve_data_path


def file_exists(path):
    return resolve_data_path(path).exists()


def load_json(path):
    with open(resolve_data_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(resolve_data_path(path), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

