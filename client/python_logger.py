"""Логгер, воспроизводимый генератор сессий и импорт локальных событий Unity."""

import argparse
import json
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path
from time import time

import requests

from server.storage import ROOT, SAMPLE_DB, Event, ingest


class TelemetryLogger:
    def __init__(self, player_id: str, output: Path, url: str | None = None):
        self.player_id = player_id
        self.session_id = uuid.uuid4().hex
        self.output = output
        self.url = url
        self.buffer = []

    def log(self, event_type: str, level: str, **fields) -> None:
        event = Event(
            event_id=uuid.uuid4().hex,
            session_id=self.session_id,
            player_id=self.player_id,
            event_type=event_type,
            ts=time(),
            level=level,
            source="simulation",
            **fields,
        ).model_dump()
        self.output.parent.mkdir(parents=True, exist_ok=True)
        # Сначала сохраняем локальную копию: сетевой сбой не должен терять события.
        with self.output.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
        self.buffer.append(event)

    def flush(self) -> None:
        if self.url and self.buffer:
            response = requests.post(self.url, json=self.buffer, timeout=5)
            response.raise_for_status()
            self.buffer.clear()  # Очищаем буфер только после подтверждения сервера.


def generate_events(count: int = 48, seed: int = 42) -> list[Event]:
    if count < 20:
        raise ValueError("Для учебной выборки нужно не менее 20 сессий")
    rng = random.Random(seed)
    players = min(24, count)
    base = datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp()
    events = []
    for index in range(count):
        # Половина игроков возвращается на D1, остальные повторные визиты — на D2/D3.
        if index < players:
            player, day = index, 0
        elif index < players + players // 2:
            player, day = index - players, 1
        else:
            player, day = (index - players) % players, 2 + index % 2
        level = "L1" if index % 2 == 0 else "L2"
        start = base + day * 86400 + player * 1200
        duration = rng.randint(90, 360)
        session_id = f"sample-s{index + 1:03}"

        records = [("session_start", 0, None, None, {})]
        for number in range(1 + index % 3):
            # Смерти сосредоточены в двух открытых участках комнаты, а не внутри препятствий.
            center = (-6, -5) if level == "L1" else (6, 5)
            records.append(
                (
                    "death",
                    duration * (0.12 + 0.12 * number),
                    rng.uniform(center[0] - 1.5, center[0] + 1.5),
                    rng.uniform(center[1] - 1.5, center[1] + 1.5),
                    {"cause": "guard"},
                )
            )
        checkpoint = index % 5 != 0
        if checkpoint:
            records.append(("checkpoint", duration * 0.55, -6, 5, {}))
        if checkpoint and index % 3 != 0:
            records.append(("level_complete", duration * 0.85, 6, 7, {"time_s": duration * 0.85}))
        reason = "complete" if checkpoint and index % 3 != 0 else "quit"
        records.append(("session_end", duration, None, None, {"reason": reason}))
        for kind, offset, x, y, payload in records:
            events.append(
                Event(
                    event_id=f"{session_id}-e{len(events):04}",
                    session_id=session_id,
                    player_id=f"sample-p{player + 1:03}",
                    event_type=kind,
                    ts=start + offset,
                    level=level,
                    source="simulation",
                    x=x,
                    y=y,
                    payload=payload,
                )
            )
    return events


def read_jsonl(path: Path) -> list[Event]:
    with path.open(encoding="utf-8-sig") as stream:
        return [Event.model_validate_json(line) for line in stream if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulate", type=int)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--import-jsonl", type=Path)
    parser.add_argument("--db", type=Path, default=SAMPLE_DB)
    parser.add_argument("--url", help="Отправить события через HTTP вместо прямой записи в SQLite")
    args = parser.parse_args()
    if args.simulate:
        events = generate_events(args.simulate, args.seed)
        output = ROOT / "data" / "events.jsonl"
        output.parent.mkdir(exist_ok=True)
        output.write_text("".join(e.model_dump_json() + "\n" for e in events), encoding="utf-8")
    elif args.import_jsonl:
        events = read_jsonl(args.import_jsonl)
    else:
        parser.error("Укажите --simulate N или --import-jsonl файл")
    if args.url:
        response = requests.post(args.url, json=[e.model_dump() for e in events], timeout=15)
        response.raise_for_status()
        print(response.json())
    else:
        print(ingest(args.db, events))


if __name__ == "__main__":
    main()
