"""Сборка шестистраничного отчёта из сохранённых метрик, графиков и игровых событий."""

import json
from collections import Counter

from matplotlib import font_manager
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from server.storage import ROOT


def main():
    summary = json.loads((ROOT / "results/summary.json").read_text(encoding="utf-8"))
    events = [json.loads(line) for line in (ROOT / "data/unity-capture.jsonl").read_text(encoding="utf-8").splitlines()]
    counts = Counter(event["event_type"] for event in events)
    # Шрифты из matplotlib содержат кириллицу и работают также в Linux.
    for name, weight in [("Report", "normal"), ("ReportBold", "bold")]:
        font_path = font_manager.findfont(font_manager.FontProperties(family="DejaVu Sans", weight=weight))
        pdfmetrics.registerFont(TTFont(name, font_path))
    normal = ParagraphStyle("normal", fontName="Report", fontSize=10, leading=14, spaceAfter=9)
    heading = ParagraphStyle("heading", parent=normal, fontName="ReportBold", fontSize=15, leading=20, spaceAfter=13)
    title = ParagraphStyle("title", parent=heading, fontSize=22, leading=29, spaceAfter=20)
    small = ParagraphStyle("small", parent=normal, fontSize=8.5, leading=12)
    code = ParagraphStyle("code", parent=small, fontSize=8, leading=11, backColor=colors.HexColor("#edf2f6"))
    story = []
    markdown = ["# Отчёт по лабораторной работе № 2\n"]

    def h(text, large=False):
        story.append(Paragraph(text, title if large else heading))
        markdown.append(("# " if large else "## ") + text + "\n")

    def p(text):
        story.append(Paragraph(text, normal))
        markdown.append(text + "\n")

    def table(rows, widths=None):
        cells = [[Paragraph(str(cell), small) for cell in row] for row in rows]
        item = Table(cells, colWidths=widths, hAlign="LEFT", repeatRows=1)
        item.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e3edf4")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#d4dce3")),
                ]
            )
        )
        story.extend([item, Spacer(1, 12)])
        markdown.extend(
            [
                "| " + " | ".join(map(str, rows[0])) + " |",
                "| " + " | ".join("---" for _ in rows[0]) + " |",
                *["| " + " | ".join(map(str, row)) + " |" for row in rows[1:]],
                "",
            ]
        )

    def picture(relative, width, caption):
        image = Image(str(ROOT / relative))
        image.drawHeight *= width / image.drawWidth
        image.drawWidth = width
        story.extend([image, Spacer(1, 5), Paragraph(caption, small), Spacer(1, 9)])
        markdown.append(
            f"![{caption}]({('../' if relative.startswith('results/') else '') + relative.removeprefix('docs/')})\n"
        )

    def page():
        story.append(PageBreak())

    h("Лабораторная работа № 2", True)
    h("Сбор и анализ игровой телеметрии")
    p(
        "Дисциплина: Игровой искусственный интеллект. Направление 09.03.01, профиль «Разработка игровых и"
        " XR-приложений»."
    )
    p(
        "Студент: Печенов Владимир Владимирович<br/>Группа: ИВТ-465<br/>"
        "Преподаватель: Колесников Н. С.<br/>Дата: 06.10.2026"
    )
    story.append(Spacer(1, 28))
    h("1. Цель и постановка задачи")
    p(
        "Организовать сбор событий игрового клиента, сохранить их в базе и получить метрики, позволяющие "
        "описать прохождение уровня и возвращение игроков."
    )
    p(
        "Требования: клиентский логгер; база с не менее чем 20 сессиями; расчёт длительности, удержания "
        "D1, тепловой карты смертей и конверсии; дашборд с не менее чем тремя визуализациями. Определения"
        " метрик приведены в README."
    )
    p(
        "Реализация использует Unity 6000.3.9f1, C#, Python 3.14, FastAPI, SQLite, pandas, matplotlib и "
        "Streamlit. Игровая основа - комната со стражником из первой работы."
    )
    p(
        "Материалы находятся в ветке lab02-telemetry существующего репозитория. Сцена Lab01 также "
        "сохранена; новая сцена Lab02 содержит игровой сценарий для сбора телеметрии."
    )

    page()
    h("2. Архитектура и события")
    p(
        "Поток данных: Unity → локальный JSONL и HTTP POST → FastAPI → SQLite → pandas → графики и "
        "Streamlit. Сервер записывает новые игровые данные в live.db; готовая учебная база telemetry.db "
        "хранится отдельно."
    )
    table(
        [
            ["Событие", "Условие записи", "Дополнительные поля"],
            ["session_start", "Запуск или перезапуск уровня", "level, source"],
            ["death", "Три удара стражника", "x, y, cause"],
            ["checkpoint", "Первое достижение зелёного диска", "x, y"],
            ["level_complete", "Выход после контрольной точки", "x, y, time_s"],
            ["session_end", "Завершение, выход или перезапуск", "reason"],
        ],
        [120, 225, 165],
    )
    p(
        "Каждое событие содержит event_id, session_id, player_id, ts, level, source и schema_version. ts "
        "- секунды Unix UTC. Координаты комнаты представлены парой x/y, где y соответствует оси Z Unity. "
        "Идентификатор игрока сохраняется между сессиями."
    )
    p(
        "Таблица sessions хранит принадлежность сессии игроку, уровню и источнику; events содержит "
        "события и внешнюю ссылку на сессию. event_id является первичным ключом. Индексы построены по "
        "сессии/времени и типу/уровню."
    )
    p(
        "Логгер сохраняет событие до сетевого запроса; буфер удаляется только после ответа сервера. При "
        "повторной доставке event_id предотвращает двойной учёт. Конфликт содержания откатывает весь "
        "пакет. При остановке игры локальный файл позволяет восстановить конечное событие."
    )
    fragment = (
        'ts = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0;\n'
        'x = position.x; y = position.z;\n'
        'File.AppendAllText(FilePath, JsonUtility.ToJson(item) + "\\n");\n'
        'pending.Add(item);'
    )
    story.append(Preformatted(fragment, code))
    markdown.append("```csharp\n" + fragment + "\n```\n")

    page()
    h("3. Игровая сцена и проверка сбора")
    picture("docs/img/lab02-scene.png", 470, "Рисунок 1. Комната, игрок, стражник, контрольная точка и выход.")
    p(
        "Игрок управляется WASD. Зелёный диск расположен в (-6; 5), выход в (6; 7). После трёх ударов "
        "записывается смерть и происходит возрождение. Выход доступен после контрольной точки. R начинает"
        " новую сессию, Esc завершает текущую."
    )
    p(
        "Уровни используют одинаковую геометрию: L1 - FSM и скорость 3,5 м/с; L2 - BT и скорость 4,2 м/с."
        " Координаты препятствий совпадают со схемой тепловой карты."
    )
    p(
        f"Проверка в Unity дала {len(events)} событий двух завершённых сессий. "
        "События доставлены по HTTP и сохранены в SQLite; "
        "JSONL-копия находится в data/unity-capture.jsonl."
    )
    table(
        [
            ["Тип", "Количество"],
            *[
                [kind, counts[kind]]
                for kind in ["session_start", "death", "checkpoint", "level_complete", "session_end"]
            ],
        ],
        [255, 255],
    )
    p(
        "Игровые события имеют source=unity. Учебная выборка имеет source=simulation и фиксированный seed"
        " 42; она проверяет расчёты на 48 сессиях 24 игроков за 1-4 октября 2026 года. Эти два источника "
        "не смешиваются при подготовке результатов ниже."
    )

    page()
    h("4. Длительность и удержание")
    p(
        "Длительность = ts(session_end) - ts(session_start). Сессии без границы конца и отрицательные "
        "длительности исключаются. В учебной базе все 48 сессий завершены; медиана составляет 208 с."
    )
    picture("results/session_lengths.png", 410, "Рисунок 2. Распределение длительности завершённых сессий.")
    p(
        "D1 - доля игроков, имеющих сессию в следующий календарный день UTC после первого визита. Новые "
        "игроки последнего дня наблюдения исключаются из знаменателя. Повторный визит в тот же день или "
        "только на D2 не считается D1."
    )
    picture("results/retention_d1.png", 410, "Рисунок 3. Удержание D1 когорты первого дня.")
    p(
        "Из 24 игроков 12 возвращаются на следующий день: D1 = 12/24 = 50%. Все 24 имеют повторные "
        "сессии, поэтому простой подсчёт игроков с двумя входами дал бы неверный результат 100%."
    )

    page()
    h("5. Тепловые карты и дашборд")
    p(
        "Тепловая карта - 2D-гистограмма смертей в диапазоне [-10; 10] по двум осям, 20 × 20 ячеек. "
        "Каждая ячейка соответствует 1 × 1 м. Для L1 и L2 строятся отдельные карты поверх одинаковой "
        "схемы комнаты."
    )
    left = Image(str(ROOT / "results/heatmap_L1.png"), width=250, height=208)
    right = Image(str(ROOT / "results/heatmap_L2.png"), width=250, height=208)
    story.append(Table([[left, right]], colWidths=[255, 255]))
    story.extend([Paragraph("Рисунок 4. Смерти на L1 и L2; тёмные блоки - препятствия.", small), Spacer(1, 10)])
    markdown.extend(["![Карта L1](../results/heatmap_L1.png)\n", "![Карта L2](../results/heatmap_L2.png)\n"])
    p(
        "На каждом уровне записано 48 смертей. Учебная выборка размещает их в открытых участках: L1 около"
        " (-6; -5), L2 около (6; 5). Карты позволяют проверить преобразование координат и разделение "
        "уровней. Для выводов о реальном балансе нужны дополнительные прохождения игроков."
    )
    p(
        "Дашборд содержит гистограмму длительности, воронку, тепловые карты и график D1. Фильтры выбирают"
        " базу, источник и уровень. При изменении фильтра все показатели пересчитываются; события "
        "доступны для просмотра и выгрузки CSV."
    )
    picture("docs/img/lab02-dashboard.png", 350, "Рисунок 5. Дашборд с показателями и графиками.")

    page()
    h("6. Конверсия, проверки и выводы")
    picture("results/funnel.png", 390, "Рисунок 6. Воронка прохождения по сессиям.")
    p(
        "Воронка требует хронологического порядка: начало → checkpoint → завершение. Каждая сессия "
        "считается один раз на шаге. Из 48 сессий контрольной точки достигли 38 (79,2%), выхода - 26 "
        "(54,2%). Между контрольной точкой и выходом потеряно 12 из 38 сессий, или 31,6%."
    )
    p(
        "Проверки Python: 16 тестов пройдены. Проверены границы длительности, календарный D1, порядок "
        "воронки, повторная доставка, откат конфликтующего пакета, неверные поля и фильтрация дашборда. В"
        " Unity подтверждены события всех пяти типов на L1/L2 и доставка в SQLite."
    )
    p(
        "Получена полная цепочка сбора и анализа. Данные и графики воспроизводятся из JSONL; сервер "
        "допускает повторную доставку без искажения метрик. Учебная выборка проверяет расчёты, а игровые "
        "сессии подтверждают работу логгера. Для улучшения уровня следует сравнить потери между этапами и"
        " расположение смертей на расширенной игровой выборке."
    )
    h("7. Источники и материалы")
    p(
        "1. Шаблон ЛР № 2: https://github.com/kolesnikov-vstu-gameai/lab02-telemetry<br/>"
        "2. SQLite: https://www.sqlite.org/lang_transaction.html<br/>"
        "3. pandas: https://pandas.pydata.org/docs/<br/>"
        "4. FastAPI: https://fastapi.tiangolo.com/<br/>"
        "5. Streamlit: https://docs.streamlit.io/"
    )
    p(
        "Репозиторий: https://github.com/VladimirPechenov/III_lab1/tree/lab02-telemetry. "
        "Исходные события: data/events.jsonl; результаты: results/; схема: docs/event_schema.md."
    )

    def footer(canvas, document):
        canvas.setFont("Report", 8)
        canvas.setFillColor(colors.HexColor("#526477"))
        canvas.drawString(42, 22, "ЛР № 2. Сбор и анализ игровой телеметрии")
        canvas.drawRightString(A4[0] - 42, 22, str(document.page))

    output = ROOT / "docs/lab02-report.pdf"
    document = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=42,
        rightMargin=42,
        topMargin=38,
        bottomMargin=38,
        title="Лабораторная работа № 2",
        author="Печенов Владимир Владимирович",
    )
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    (ROOT / "docs/lab02-report.md").write_text("\n".join(markdown).replace("<br/>", "\n\n"), encoding="utf-8")
    print(output)
    print("Сессий в учебной базе:", summary["sessions"])


if __name__ == "__main__":
    main()
