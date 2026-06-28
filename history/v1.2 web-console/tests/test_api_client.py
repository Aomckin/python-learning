import json
import unittest

import requests

from clients.api_client import ApiClient, ApiClientError, AttrDict


class FakeResponse:
    def __init__(self, status_code=200, body=None, text=None):
        self.status_code = status_code
        self._body = body
        self.text = text if text is not None else json.dumps(body or {})

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        if isinstance(self._body, Exception):
            raise self._body

        return self._body


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, timeout):
        self.calls.append(("GET", url, None, timeout))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response

        return response

    def post(self, url, json, timeout):
        self.calls.append(("POST", url, json, timeout))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response

        return response


class ApiClientTest(unittest.TestCase):
    def test_get_state_returns_attr_dict_recursively(self):
        session = FakeSession([
            FakeResponse(body={
                "energy_text": "energy",
                "events": [{"type": "OK", "payload": {"value": 1}}],
            })
        ])
        client = ApiClient(base_url="http://server", session=session)

        state = client.get_state()

        self.assertIsInstance(state, AttrDict)
        self.assertEqual(state.energy_text, "energy")
        self.assertEqual(state["events"][0].type, "OK")
        self.assertEqual(state.events[0].payload.value, 1)
        self.assertEqual(session.calls[0], ("GET", "http://server/state", None, 5))

    def test_execute_command_posts_command_payload(self):
        session = FakeSession([
            FakeResponse(body={"success": True, "state": {"coin_text": "1"}})
        ])
        client = ApiClient(base_url="http://server/", timeout=2, session=session)

        result = client.execute_command("BUY", {"item_id": "x"})

        self.assertTrue(result.success)
        self.assertEqual(result.state.coin_text, "1")
        self.assertEqual(
            session.calls[0],
            (
                "POST",
                "http://server/command",
                {"type": "BUY", "payload": {"item_id": "x"}},
                2,
            ),
        )

    def test_duration_options_escapes_action_name(self):
        session = FakeSession([FakeResponse(body={"success": True, "events": []})])
        client = ApiClient(base_url="http://server", session=session)

        client.get_action_duration_options("推gal")

        self.assertEqual(
            session.calls[0],
            (
                "GET",
                "http://server/actions/%E6%8E%A8gal/duration-options",
                None,
                5,
            ),
        )

    def test_request_errors_are_wrapped(self):
        session = FakeSession([requests.Timeout("slow")])
        client = ApiClient(base_url="http://server", session=session)

        with self.assertRaises(ApiClientError):
            client.get_state()

    def test_bad_json_is_wrapped(self):
        session = FakeSession([
            FakeResponse(body=ValueError("bad json"), text="not json")
        ])
        client = ApiClient(base_url="http://server", session=session)

        with self.assertRaises(ApiClientError):
            client.get_state()


if __name__ == "__main__":
    unittest.main()
