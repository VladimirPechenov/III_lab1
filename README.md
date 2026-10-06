# Лабораторная работа № 2 — сбор и анализ игровой телеметрии

Дисциплина «Игровой искусственный интеллект». Ветка `lab02-telemetry` продолжает Unity-проект первой работы
и выполняет требования [шаблона ЛР № 2](https://github.com/kolesnikov-vstu-gameai/lab02-telemetry).

**Студент:** Печенов Владимир Владимирович, ИВТ-465. **Преподаватель:** Колесников Н. С.

**Стек:** Unity 6000.3.9f1, C#, Python 3.14, FastAPI, SQLite, pandas, matplotlib, Streamlit.

Готовы: логгер Unity и Python, база с 48 сессиями, четыре расчёта, дашборд с четырьмя видами графиков,
схема событий, тесты и [отчёт PDF](docs/lab02-report.pdf) / [Markdown](docs/lab02-report.md).

## Быстрый запуск в Windows

В корне репозитория:

```powershell
git switch lab02-telemetry
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m analysis.analyze
.\tools\start_lab02.ps1
```

Готовая база уже включена в Git. Дашборд: **http://127.0.0.1:8501**; описание API: **http://127.0.0.1:8000/docs**.
Скрипт запуска выводит PID процессов и сохраняет журналы в `.venv/logs`. Для остановки используйте
`Stop-Process -Id <PID>`. Порты, занятые ранее, скрипт не переиспользует.

Альтернатива — два терминала:

```powershell
# Терминал 1: приём игровых событий
.\.venv\Scripts\python.exe -m uvicorn server.app:app --host 127.0.0.1 --port 8000
# Терминал 2: дашборд
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py --server.address 127.0.0.1 --server.port 8501
```

## Unity и игровые события

1. Откройте `unity/UnityProject` в Unity 6000.3.9f1 и сцену `Assets/_Project/Scenes/Lab02.unity`.
2. Запустите сервер, затем нажмите Play. WASD — движение, R — новая сессия, 1/2 — уровень, Esc — конец сессии.
3. Дойдите до зелёной контрольной точки, затем до жёлтого выхода. Три удара стражника вызывают смерть и возрождение.
4. L1 использует FSM и скорость 3,5 м/с; L2 — BT и скорость 4,2 м/с. Геометрия комнаты одинакова.
5. На объекте `Telemetry` в `TelemetryLogger` задаются адрес сервера и постоянный псевдоним игрока `playerId`.
6. В дашборде выберите «Новые игровые сессии» и нажмите «Обновить». Фильтры уровня и источника пересчитывают графики.

Сцена сохранена в репозитории; меню **Lab 02 → Create telemetry scene** позволяет пересоздать её.
При открытом Unity доступен Unity MCP для работы со сценой. Логгер работает также без MCP.

## Определения метрик

| Метрика | Расчёт |
|---|---|
| Длительность | `ts(session_end) − ts(session_start)`; медиана и гистограмма. Без конечного события сессия исключается |
| Retention D1 | Доля игроков, вернувшихся в следующий календарный день UTC после первого визита. Когорта последнего дня наблюдения исключается |
| Heatmap смертей | 2D-гистограмма x/y событий death, отдельно для L1/L2; 20 × 20 ячеек по 1 м, с геометрией комнаты |
| Конверсия | Воронка по сессиям `session_start → checkpoint → level_complete` с соблюдением порядка событий; процент от начала и от предыдущего шага |

В учебной выборке: **48 сессий, 24 игрока, 256 событий, медиана 208 с, D1 50%, 96 смертей**.
Контрольная точка достигнута в 38 сессиях (79,2%), уровень завершён в 26 (54,2%).
Между контрольной точкой и выходом потеряно 12 из 38 сессий (31,6%). Карты разделяют участки смертей двух уровней.

## Данные и воспроизведение

`data/telemetry.db` и `data/events.jsonl` содержат учебную синтетическую выборку с seed 42.
Игровой лог `data/unity-capture.jsonl` содержит 15 событий двух проверочных сессий из Unity.
Источники обозначены как `simulation` и `unity`; учебные и новые игровые данные хранятся в разных базах.

```powershell
# Повторный запуск не дублирует события: их идентификаторы стабильны.
.\.venv\Scripts\python.exe -m client.python_logger --simulate 48 --seed 42
.\.venv\Scripts\python.exe -m analysis.analyze
# Импорт сохранённых игровых сессий, в том числе при недоступности сервера в момент игры
.\.venv\Scripts\python.exe -m client.python_logger --import-jsonl data/unity-capture.jsonl --db data/live.db
# Текущий локальный журнал создаётся в data/unity-events.jsonl
.\.venv\Scripts\python.exe -m client.python_logger --import-jsonl data/unity-events.jsonl --db data/live.db
# Вариант отправки учебной выборки по HTTP
.\.venv\Scripts\python.exe -m client.python_logger --simulate 48 --url http://127.0.0.1:8000/events
```

События записываются в JSONL до сетевого запроса. При сбое сети файл можно импортировать позже.
Сервер проверяет схему, запрещает конфликт идентификаторов и записывает пакет одной транзакцией.
Полная [схема событий и ER-диаграмма](docs/event_schema.md), [описание выборки](data/README.md).

## Проверки

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check server client analysis dashboard tests tools
.\.venv\Scripts\python.exe -m tools.build_report
```

Python: **16 тестов пройдены**. Unity: подтверждены все пять типов событий на L1/L2 и HTTP-доставка в SQLite.
Тесты проверяют определения метрик, дубликаты, откат ошибочного пакета и фильтр уровня в дашборде.
GitHub Actions запускает Python-проверки и сохраняет графики. Для запуска Unity-тестов в CI нужен `UNITY_LICENSE`.

## Структура

| Путь | Назначение |
|---|---|
| `unity/UnityProject/Assets/_Project/Scripts/Telemetry` | Логгер Unity и игровой сценарий |
| `unity/UnityProject/Assets/_Project/Editor/CreateTelemetryScene.cs` | Сборка сцены Lab02 |
| `client/python_logger.py` | Python-логгер, генератор сессий, импорт JSONL |
| `server/app.py`, `server/storage.py` | HTTP API, проверка и запись SQLite |
| `analysis/analyze.py` | Общие функции метрик и экспорт результатов |
| `dashboard/app.py` | Streamlit-дашборд |
| `data/`, `results/` | Данные, CSV, JSON и графики |
| `tools/build_report.py` | Сборка отчёта из сохранённых результатов |
| `docs/lab02-defense.md` | Пояснения к коду и расчётам для защиты |

ФИО, группа и преподаватель указаны в отчёте и README. Если кафедра требует собственный
титульный лист, замените первую страницу отчёта. В шаблоне ЛР № 2 обязательная видеозапись не указана.

Материалы первой работы: сцена `Lab01`, [отчёт](docs/report.md), [диаграммы FSM/BT](docs/diagrams.md).
Исходная версия первой работы находится в ветке `Master`.
