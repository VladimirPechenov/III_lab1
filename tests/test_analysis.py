"""Проверки определения метрик на маленьких выборках с известным ответом."""

from datetime import datetime, timezone

import pandas as pd
import pytest

from analysis.analyze import funnel_table, retention_d1, session_lengths


def frame(rows):
    return pd.DataFrame(rows, columns=["session_id", "player_id", "event_type", "ts"])


def day(number):
    return datetime(2026, 10, number, tzinfo=timezone.utc).timestamp()


def test_duration_uses_boundaries_and_excludes_incomplete_session():
    df = frame(
        [
            ("s1", "p1", "session_start", 10),
            ("s1", "p1", "death", 100),
            ("s1", "p1", "session_end", 60),
            ("s2", "p2", "session_start", 20),
        ]
    )
    # Событие вне границ не должно расширять длительность до MAX(ts)-MIN(ts).
    assert session_lengths(df).to_dict() == {"s1": 50}


def test_d1_means_next_calendar_day_not_second_session():
    df = frame(
        [
            ("s1", "p1", "session_start", day(1)),
            ("s2", "p1", "session_start", day(2)),
            ("s3", "p2", "session_start", day(1)),
            ("s4", "p2", "session_start", day(1) + 600),
            ("s5", "p2", "session_start", day(3)),
            ("s6", "p3", "session_start", day(3)),
        ]
    )
    # p1 вернулся на D1, p2 только в тот же день и на D2, p3 ещё не созрел.
    assert retention_d1(df) == 0.5


def test_no_mature_cohort_has_no_retention_value():
    assert retention_d1(frame([("s1", "p1", "session_start", day(1))])) is None


def test_funnel_requires_order_and_does_not_count_duplicate_checkpoints():
    df = frame(
        [
            ("s1", "p1", "session_start", 0),
            ("s1", "p1", "checkpoint", 10),
            ("s1", "p1", "checkpoint", 11),
            ("s1", "p1", "level_complete", 20),
            ("s2", "p2", "session_start", 0),
            ("s2", "p2", "level_complete", 5),
            ("s2", "p2", "checkpoint", 10),
        ]
    )
    result = funnel_table(df)
    assert result.sessions.tolist() == [2, 2, 1]
    assert result.percent_of_start.tolist() == [100, 100, 50]


def test_empty_data_is_handled():
    df = frame([])
    assert session_lengths(df).empty
    assert retention_d1(df) is None
    assert funnel_table(df).sessions.tolist() == [0, 0, 0]


def test_sample_d1_is_reproducible():
    from client.python_logger import generate_events

    events = generate_events()
    df = pd.DataFrame([event.model_dump() for event in events])
    assert df.session_id.nunique() == 48
    assert df.player_id.nunique() == 24
    assert retention_d1(df) == pytest.approx(0.5)
    assert len(session_lengths(df)) == 48
