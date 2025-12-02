"""Test util functions."""

import pandas as pd
import plotly.graph_objects as go

from hbnddp.utils import show, write

test_data = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})


def test_show() -> None:
    """Test show function."""
    fig = go.Figure(data=go.Scatter(x=test_data["x"], y=test_data["y"], mode="markers"))
    try:
        show(fig)
    except Exception:
        assert False
    assert True


def test_write() -> None:
    """Test write function."""
    write(test_data, input_path="tests/test_data.csv", by="diagnoses", output_path=None)
    # Check that file was created
    import os

    assert os.path.exists("tests/test_data_processed_diagnoses.csv")
    # Delete created file
    os.remove("tests/test_data_processed_diagnoses.csv")