"""Дашборд должен запускаться и пересчитываться при выборе уровня."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_loads_and_filters_level():
    root = Path(__file__).resolve().parents[1]
    app = AppTest.from_file(str(root / "dashboard" / "app.py"), default_timeout=30).run()
    assert not app.exception
    assert app.metric[0].value == "48"
    app.selectbox[1].set_value("L1").run()
    assert not app.exception
    assert app.metric[0].value == "24"
