"""HTTP-приёмник телеметрии: JSON → проверка полей → транзакция SQLite."""

import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Body, FastAPI, HTTPException

from server.storage import LIVE_DB, Event, ingest, init_db


def create_app(db_path: Path = LIVE_DB) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app):
        init_db(db_path)
        yield

    app = FastAPI(title="Игровая телеметрия", version="1.0", lifespan=lifespan)

    @app.post("/events", status_code=202)
    def receive(events: Annotated[list[Event], Body(min_length=1, max_length=500)]):
        try:
            return ingest(db_path, events)
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.get("/health")
    def health():
        with sqlite3.connect(db_path) as connection:
            count = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        return {"status": "ok", "events": count}

    return app


# Отдельная live.db сохраняет новые игровые события, не изменяя учебную выборку.
app = create_app(Path(os.environ.get("TELEMETRY_DB", LIVE_DB)))
