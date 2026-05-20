import os

import requests

API = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "")


def api_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    return headers


def api_get(path: str, timeout=30):
    return requests.get(f"{API}{path}", headers=api_headers(), timeout=timeout)


def api_post(path: str, json: dict, timeout=120):
    return requests.post(f"{API}{path}", json=json, headers=api_headers(), timeout=timeout)
