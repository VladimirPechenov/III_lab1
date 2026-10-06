"""Четыре метрики, таблицы CSV и графики для отчёта."""

import argparse
import json
import sqlite3
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from server.storage import ROOT, SAMPLE_DB  # noqa: E402

plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})


def load(path: Path = SAMPLE_DB) -> pd.DataFrame:
    # Read-only соединение не создаёт пустую БД при ошибке в пути.
    with sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True) as connection:
        return pd.read_sql_query("SELECT * FROM events ORDER BY ts, event_id", connection)


def session_lengths(df: pd.DataFrame) -> pd.Series:
    starts = df[df.event_type == "session_start"].groupby("session_id").ts.min()
    ends = df[df.event_type == "session_end"].groupby("session_id").ts.max()
    lengths = (ends - starts).dropna()
    # Незавершённую сессию нельзя выдавать за короткую; отрицательное время также отбрасывается.
    return lengths[lengths >= 0].rename("length_s")


def retention_table(df: pd.DataFrame) -> pd.DataFrame:
    columns = ["cohort", "players", "returned_d1", "retention_d1"]
    starts = df[df.event_type == "session_start"].copy()
    if starts.empty:
        return pd.DataFrame(columns=columns)
    starts["day"] = pd.to_datetime(starts.ts, unit="s", utc=True).dt.floor("D")
    last_day = pd.to_datetime(df.ts.max(), unit="s", utc=True).floor("D")
    rows = []
    for player, visits in starts.groupby("player_id"):
        first = visits.day.min()
        # Последний день наблюдения ещё не даёт узнать, вернулся ли новый игрок завтра.
        if first >= last_day:
            continue
        returned = (visits.day == first + pd.Timedelta(days=1)).any()
        rows.append({"cohort": first.strftime("%Y-%m-%d"), "player": player, "returned": int(returned)})
    if not rows:
        return pd.DataFrame(columns=columns)
    result = pd.DataFrame(rows).groupby("cohort").agg(players=("player", "count"), returned_d1=("returned", "sum"))
    result["retention_d1"] = result.returned_d1 / result.players
    return result.reset_index()


def retention_d1(df: pd.DataFrame) -> float | None:
    cohorts = retention_table(df)
    if cohorts.empty:
        return None
    # Взвешиваем по числу игроков: маленькая когорта не должна иметь вес большой.
    return float(cohorts.returned_d1.sum() / cohorts.players.sum())


def funnel_table(df: pd.DataFrame) -> pd.DataFrame:
    stages = ["session_start", "checkpoint", "level_complete"]
    counts = [0, 0, 0]
    for _, session in df.groupby("session_id"):
        previous = -np.inf
        for index, stage in enumerate(stages):
            candidates = session[(session.event_type == stage) & (session.ts >= previous)]
            if candidates.empty:
                break
            previous = candidates.ts.min()
            counts[index] += 1
    # Одна сессия учитывается один раз на шаге, даже если checkpoint записан повторно.
    total = counts[0]
    return pd.DataFrame(
        {
            "stage": stages,
            "sessions": counts,
            "percent_of_start": [100 * count / total if total else 0 for count in counts],
            "percent_of_previous": [
                100 if total else 0,
                100 * counts[1] / counts[0] if counts[0] else 0,
                100 * counts[2] / counts[1] if counts[1] else 0,
            ],
        }
    )


def duration_figure(df):
    fig, ax = plt.subplots(figsize=(8, 4))
    lengths = session_lengths(df)
    ax.hist(lengths, bins=10, color="#267cba", edgecolor="white")
    if not lengths.empty:
        ax.axvline(lengths.median(), color="#ed9446", label=f"Медиана: {lengths.median():.0f} с")
        ax.legend()
    ax.set(title="Продолжительность завершённых сессий", xlabel="Секунды", ylabel="Число сессий")
    fig.tight_layout()
    return fig


def retention_figure(df):
    fig, ax = plt.subplots(figsize=(8, 4))
    cohorts = retention_table(df)
    ax.bar(cohorts.cohort, cohorts.retention_d1 * 100, color="#3b9a80")
    ax.set(title="Удержание D1 по дате первого визита (UTC)", ylabel="Вернулись на следующий день, %", ylim=(0, 100))
    if cohorts.empty:
        ax.text(0.5, 0.5, "Нет созревших когорт", ha="center", transform=ax.transAxes)
    fig.tight_layout()
    return fig


def heatmap_figure(df, level):
    deaths = df[(df.event_type == "death") & (df.level == level)].dropna(subset=["x", "y"])
    fig, ax = plt.subplots(figsize=(6, 5))
    counts, x_edges, y_edges = np.histogram2d(deaths.x, deaths.y, bins=20, range=[[-10, 10], [-10, 10]])
    mesh = ax.pcolormesh(x_edges, y_edges, np.ma.masked_where(counts.T == 0, counts.T), cmap="YlOrRd", vmin=0)
    fig.colorbar(mesh, ax=ax, label="Число смертей")
    ax.set_facecolor("#eaf0f3")
    # Геометрия совпадает с комнатой Unity; вертикальная ось графика — Unity Z.
    for x, y in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
        ax.add_patch(Rectangle((x - 1, y - 1), 2, 2, facecolor="#4e5966", edgecolor="white"))
    ax.scatter([-6, 6], [5, 7], marker="*", s=100, color="#218765")
    ax.annotate("КТ", (-6, 5), xytext=(-8, 7))
    ax.annotate("Выход", (6, 7), xytext=(4, 8.5))
    ax.set(title=f"Смерти на {level}: {len(deaths)}", xlabel="X, м", ylabel="Z, м", xlim=(-10, 10), ylim=(-10, 10))
    ax.set_aspect("equal")
    fig.tight_layout()
    return fig


def funnel_figure(df):
    funnel = funnel_table(df)
    fig, ax = plt.subplots(figsize=(8, 4))
    labels = ["Начало", "Контрольная точка", "Завершение"]
    bars = ax.barh(labels, funnel.sessions, color=["#267cba", "#3b9a80", "#ed9446"])
    for bar, row in zip(bars, funnel.itertuples(), strict=True):
        ax.text(
            bar.get_width() + 0.2,
            bar.get_y() + bar.get_height() / 2,
            f"{row.sessions} ({row.percent_of_start:.1f}%)",
            va="center",
        )
    ax.set(
        title="Воронка прохождения по сессиям", xlabel="Число сессий", xlim=(0, max(1, funnel.sessions.max()) * 1.35)
    )
    ax.invert_yaxis()
    fig.tight_layout()
    return fig


def summarize(df) -> dict:
    lengths = session_lengths(df)
    funnel = funnel_table(df)
    return {
        "events": len(df),
        "sessions": int(df.session_id.nunique()),
        "players": int(df.player_id.nunique()),
        "completed_sessions": len(lengths),
        "incomplete_sessions": int(df.session_id.nunique()) - len(lengths),
        "median_length_s": None if lengths.empty else float(lengths.median()),
        "retention_d1": retention_d1(df),
        "deaths": int((df.event_type == "death").sum()),
        "checkpoint_percent": float(funnel.iloc[1].percent_of_start),
        "completion_percent": float(funnel.iloc[2].percent_of_start),
    }


def export(df, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    session_lengths(df).to_csv(output / "session_lengths.csv", encoding="utf-8")
    retention_table(df).to_csv(output / "retention.csv", index=False)
    funnel_table(df).to_csv(output / "funnel.csv", index=False)
    summary = summarize(df)
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    figures = {
        "session_lengths": duration_figure(df),
        "retention_d1": retention_figure(df),
        "funnel": funnel_figure(df),
    }
    for level in sorted(df.level.unique()):
        figures[f"heatmap_{level}"] = heatmap_figure(df, level)
        deaths = df[(df.event_type == "death") & (df.level == level)]
        counts, _, _ = np.histogram2d(deaths.x, deaths.y, bins=20, range=[[-10, 10], [-10, 10]])
        np.savetxt(output / f"heatmap_{level}.csv", counts.T, fmt="%d", delimiter=",")
    for name, figure in figures.items():
        figure.savefig(output / f"{name}.png", dpi=160)
        plt.close(figure)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=SAMPLE_DB)
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--source", choices=["unity", "simulation"])
    args = parser.parse_args()
    df = load(args.db)
    if args.source:
        df = df[df.source == args.source]
    print(json.dumps(export(df, args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
