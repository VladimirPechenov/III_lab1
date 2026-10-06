"""Схема события и запись в SQLite; используются сервером и импортом JSONL."""

import json
import sqlite3
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DB = ROOT / "data" / "telemetry.db"
LIVE_DB = ROOT / "data" / "live.db"


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    schema_version: Literal[1] = 1
    event_id: str = Field(min_length=1, max_length=64)
    session_id: str = Field(min_length=1, max_length=64)
    player_id: str = Field(min_length=1, max_length=64)
    event_type: Literal["session_start", "death", "checkpoint", "level_complete", "session_end"]
    ts: float = Field(ge=0)
    level: Literal["L1", "L2"]
    source: Literal["unity", "simulation"]
    x: float | None = Field(default=None, ge=-10, le=10)
    y: float | None = Field(default=None, ge=-10, le=10)
    payload: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_position(self):
        # Без координат смерть нельзя поместить на тепловую карту.
        if self.event_type in {"death", "checkpoint", "level_complete"} and (self.x is None or self.y is None):
            raise ValueError("Для пространственного события нужны x и y")
        return self


def init_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                player_id TEXT NOT NULL,
                level TEXT NOT NULL,
                source TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES sessions(session_id),
                player_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                ts REAL NOT NULL,
                level TEXT NOT NULL,
                source TEXT NOT NULL,
                x REAL, y REAL,
                payload TEXT NOT NULL,
                schema_version INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS events_session_time ON events(session_id, ts);
            CREATE INDEX IF NOT EXISTS events_type_level ON events(event_type, level);
        """)


def ingest(path: Path, events: list[Event]) -> dict:
    init_db(path)
    accepted = 0
    # Одна транзакция на пакет: конфликт не должен оставлять половину событий в БД.
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        for event in events:
            session = (event.session_id, event.player_id, event.level, event.source)
            stored_session = connection.execute(
                "SELECT session_id, player_id, level, source FROM sessions WHERE session_id = ?",
                (event.session_id,),
            ).fetchone()
            if stored_session is not None and stored_session != session:
                raise ValueError("session_id уже принадлежит другому игроку, уровню или источнику")
            connection.execute("INSERT OR IGNORE INTO sessions VALUES (?, ?, ?, ?)", session)
            values = (
                event.event_id,
                event.session_id,
                event.player_id,
                event.event_type,
                event.ts,
                event.level,
                event.source,
                event.x,
                event.y,
                json.dumps(event.payload, ensure_ascii=False, sort_keys=True),
                event.schema_version,
            )
            stored = connection.execute("SELECT * FROM events WHERE event_id = ?", (event.event_id,)).fetchone()
            if stored is not None:
                if stored != values:
                    raise ValueError("event_id повторён с другим содержимым")
                continue  # Повторная отправка того же события не меняет метрики.
            connection.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", values)
            accepted += 1
    return {"accepted": accepted, "duplicates": len(events) - accepted}
