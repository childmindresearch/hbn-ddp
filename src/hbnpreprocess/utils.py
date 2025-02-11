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


def write(output: pd.DataFrame, output_dir: str) -> None:
    """Write the processed data to a CSV file."""
    output.to_csv(output_dir, index=False)
    print(f"Data saved in {output_dir}")
    return None
