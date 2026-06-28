from urllib.parse import quote

import requests


class ApiClientError(RuntimeError):
    pass


class AttrDict(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


def to_attr_dict(value):
    if isinstance(value, dict):
        return AttrDict({key: to_attr_dict(item) for key, item in value.items()})

    if isinstance(value, list):
        return [to_attr_dict(item) for item in value]

    return value


class ApiClient:
    def __init__(self, base_url="http://127.0.0.1:8000", timeout=5, session=None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def get_state(self):
        return self._get("/state")

    def get_action_duration_options(self, action_name):
        action = quote(action_name, safe="")
        return self._get(f"/actions/{action}/duration-options")

    def execute_command(self, command_type, payload=None):
        return self._post(
            "/command",
            {"type": command_type, "payload": payload or {}}
        )

    def _get(self, path):
        return self._request("GET", path)

    def _post(self, path, body):
        return self._request("POST", path, body)

    def _request(self, method, path, body=None):
        url = f"{self.base_url}{path}"
        try:
            if method == "GET":
                response = self.session.get(url, timeout=self.timeout)
            else:
                response = self.session.post(url, json=body, timeout=self.timeout)
            response.raise_for_status()
            return to_attr_dict(response.json())
        except requests.RequestException as exc:
            raise ApiClientError(f"无法连接后端服务，请先启动 FastAPI：{exc}") from exc
        except ValueError as exc:
            raise ApiClientError(f"后端返回的不是有效 JSON：{exc}") from exc
