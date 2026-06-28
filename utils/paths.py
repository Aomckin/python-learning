import os
from pathlib import Path


DATA_ROOT_ENV = "OTAKU_ENERGY_DATA_DIR"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_data_root():
    return Path(os.environ.get(DATA_ROOT_ENV, PROJECT_ROOT)).resolve()


def resolve_data_path(path):
    path = Path(path)
    if path.is_absolute():
        return path

    return get_data_root() / path
