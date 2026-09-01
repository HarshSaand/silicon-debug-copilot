import ast
from pathlib import Path


def test_streamlit_app_parses_and_has_safety_copy():
    path = Path(__file__).parents[1] / "app.py"
    source = path.read_text(encoding="utf-8")
    ast.parse(source)
    assert "No corrective actions are executed" in source
    assert "ABSTAINED" in source
