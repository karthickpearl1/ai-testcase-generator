"""Shared fixtures for the generated API tests.

The client uses only the standard library so the suite runs anywhere pytest is installed.
Point it at an environment with API_BASE_URL and API_TOKEN.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

import pytest

BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
TOKEN = os.environ.get("API_TOKEN", "demo-token")


@dataclass
class Response:
    status_code: int
    text: str

    def json(self):
        return json.loads(self.text) if self.text else None


class ApiClient:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url
        self.token = token

    def request(self, method, path, *, path_params=None, query=None, body=None, auth="none"):
        for name, value in (path_params or {}).items():
            path = path.replace("{" + name + "}", urllib.parse.quote(str(value)))
        url = self.base_url + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        headers = {"Accept": "application/json"}
        if auth == "valid":
            headers["Authorization"] = f"Bearer {self.token}"
        elif auth == "invalid":
            headers["Authorization"] = "Bearer not-a-valid-token"
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return Response(resp.status, resp.read().decode())
        except urllib.error.HTTPError as err:
            return Response(err.code, err.read().decode())


@pytest.fixture(scope="session")
def api():
    return ApiClient(BASE_URL, TOKEN)
