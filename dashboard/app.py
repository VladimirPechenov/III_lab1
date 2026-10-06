"""Дашборд использует те же функции метрик, что и скрипт анализа."""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analysis.analyze import (  # noqa: E402
    duration_figure,
    funnel_figure,
    funnel_table,
    heatmap_figure,
    load,
    retention_figure,
    retention_table,
    summarize,
)
from server.storage import LIVE_DB, SAMPLE_DB  # noqa: E402

st.set_page_config(page_title="Игровая телеметрия", page_icon="📊", layout="wide")
st.title("Игровая телеметрия")
st.caption("Лабораторная работа № 2 · сессии, удержание и прохождение комнаты со стражником")

with st.sidebar:
    st.header("Выбор данных")
    dataset = st.radio("База", ["Учебная выборка", "Новые игровые сессии"])
    path = SAMPLE_DB if dataset == "Учебная выборка" else LIVE_DB
    st.button("Обновить")  # При нажатии Streamlit заново читает БД, без устаревшего кэша.

if not path.exists():
    st.info("В выбранной базе пока нет событий. Запустите сервер и пройдите сцену в Unity.")
    st.stop()
df = load(path)
if df.empty:
    st.info("В базе пока нет событий.")
    st.stop()
with st.sidebar:
    source = st.selectbox("Источник", ["Все", *sorted(df.source.unique())])
    if source != "Все":
        df = df[df.source == source]
    level = st.selectbox("Уровень", ["Все", *sorted(df.level.unique())])
    if level != "Все":
        df = df[df.level == level]
    st.caption("simulation — воспроизводимая учебная выборка; unity — события из игры.")

metrics = summarize(df)
columns = st.columns(4)
columns[0].metric("Сессий", metrics["sessions"])
columns[1].metric(
    "Медиана длительности", "—" if metrics["median_length_s"] is None else f"{metrics['median_length_s']:.0f} с"
)
columns[2].metric("Удержание D1", "—" if metrics["retention_d1"] is None else f"{metrics['retention_d1']:.1%}")
columns[3].metric("Завершили уровень", f"{metrics['completion_percent']:.1f}%")
st.caption(
    f"Игроков: {metrics['players']} · смертей: {metrics['deaths']} · "
    f"незавершённых сессий: {metrics['incomplete_sessions']}"
)

left, right = st.columns(2)
with left:
    st.subheader("Сколько времени проводят в игре")
    figure = duration_figure(df)
    st.pyplot(figure)
    plt.close(figure)
    st.caption("Длительность: конец минус начало. Сессии без конца не входят в гистограмму.")
with right:
    st.subheader("Где теряются прохождения")
    figure = funnel_figure(df)
    st.pyplot(figure)
    plt.close(figure)
    table = funnel_table(df).rename(
        columns={
            "stage": "Этап",
            "sessions": "Сессий",
            "percent_of_start": "% от начала",
            "percent_of_previous": "% от предыдущего",
        }
    )
    table["Этап"] = ["Начало", "Контрольная точка", "Завершение"]
    st.dataframe(table[["Этап", "Сессий", "% от начала"]].round(1), hide_index=True, width="stretch")

st.subheader("Опасные участки комнаты")
levels = sorted(df.level.unique())
columns = st.columns(len(levels))
for column, selected in zip(columns, levels, strict=True):
    with column:
        figure = heatmap_figure(df, selected)
        st.pyplot(figure)
        plt.close(figure)
st.caption("Серые блоки — препятствия; звёзды — контрольная точка и выход. Ось Z соответствует y в событиях.")

st.subheader("Возвращаются ли игроки на следующий день")
figure = retention_figure(df)
st.pyplot(figure)
plt.close(figure)
st.caption("D1 считается по календарным дням UTC. Игроки первого визита в последний день наблюдения исключены.")
with st.expander("Когорты и исходные события"):
    st.dataframe(retention_table(df), hide_index=True, width="stretch")
    st.dataframe(df, hide_index=True, width="stretch")
    st.download_button("Скачать отфильтрованные события CSV", df.to_csv(index=False), "events.csv", "text/csv")
