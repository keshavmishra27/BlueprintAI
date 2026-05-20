import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
if "API_KEY" in os.environ:
    del os.environ["API_KEY"]

from backend.app.database import ensure_schema
from backend.app.main import app

ensure_schema()
client = TestClient(app)


def test_public_health_without_key():
    r = client.get("/repo-judge/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_assess_domains_public():
    r = client.get("/assess/domains")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
