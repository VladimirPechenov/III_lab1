"""Приём событий, повторная доставка и отклонение неверных пакетов."""

import pytest
from fastapi.testclient import TestClient

from server.app import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "test.db")) as connection:
        yield connection


def event(**changes):
    item = {
        "event_id": "e1",
        "session_id": "s1",
        "player_id": "p1",
        "event_type": "session_start",
        "ts": 10,
        "level": "L1",
        "source": "unity",
    }
    return item | changes


def test_event_can_be_delivered_twice(client):
    assert client.post("/events", json=[event()]).json() == {"accepted": 1, "duplicates": 0}
    assert client.post("/events", json=[event()]).json() == {"accepted": 0, "duplicates": 1}
    assert client.get("/health").json()["events"] == 1


def test_conflicting_id_rolls_back_whole_batch(client):
    client.post("/events", json=[event()])
    response = client.post("/events", json=[event(event_id="e2"), event(ts=20)])
    assert response.status_code == 409
    assert client.get("/health").json()["events"] == 1


def test_session_cannot_change_player(client):
    client.post("/events", json=[event()])
    assert client.post("/events", json=[event(event_id="e2", player_id="p2")]).status_code == 409


@pytest.mark.parametrize(
    "changes",
    [
        {"event_type": "unknown"},
        {"event_type": "death"},
        {"ts": -1},
        {"event_type": "death", "x": 11, "y": 0},
        {"player_id": ""},
    ],
)
def test_invalid_event_is_rejected(client, changes):
    assert client.post("/events", json=[event(**changes)]).status_code == 422
    assert client.get("/health").json()["events"] == 0


def test_empty_batch_is_rejected(client):
    assert client.post("/events", json=[]).status_code == 422
