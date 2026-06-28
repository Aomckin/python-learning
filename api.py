from pathlib import Path

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from core import GameCore
from core_command import COMPLETE_TIMED_ACTION, GameCommand
from core_types import ActionDurationOption

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
core = GameCore()


def _coerce_payload(command_type, payload):
    payload = payload or {}

    if command_type == COMPLETE_TIMED_ACTION and isinstance(
            payload.get("option"),
            dict
    ):
        payload = dict(payload)
        option = payload["option"]
        payload["option"] = ActionDurationOption(
            option.get("minutes", 0),
            option.get("multiplier", 1),
            option.get("exp", 0)
        )

    return payload


def _run_command(command_type, payload=None):
    result = core.execute(
        GameCommand(command_type, _coerce_payload(command_type, payload))
    )
    return jsonable_encoder(result)


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/state")
def get_state():
    return jsonable_encoder(core.get_state())


@app.get("/actions/{action_name}/duration-options")
def get_duration_options(action_name: str):
    return jsonable_encoder(core.get_action_duration_options(action_name))


@app.post("/command")
def command(request: dict):
    return _run_command(request.get("type"), request.get("payload"))
