"""Util functions."""

import io

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from PIL import Image


def show(fig: go.Figure) -> None:
    """Display plotly figure in a new window."""
    buf = io.BytesIO()
    pio.write_image(fig, buf)
    img = Image.open(buf)
    img.show()


def write(output: pd.DataFrame, input_path: str, output_path: str | None) -> None:
    """Write the processed data to a CSV file."""
    if output_path is None:
        output_path = input_path.replace(".csv", "_processed.csv")
    output.to_csv(output_path, index=False)
    print(f"Data saved to {output_path}")
