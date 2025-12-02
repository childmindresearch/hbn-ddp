"""Util functions."""

import io
import logging

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from PIL import Image

logger = logging.getLogger(__name__)


def show(fig: go.Figure) -> None:
    """Display plotly figure in a new window."""
    buf = io.BytesIO()
    pio.write_image(fig, buf)
    img = Image.open(buf)
    img.show()
    buf.close()


def write(
    output: pd.DataFrame,
    input_path: str,
    by: str,
    output_path: str | None,
) -> None:
    """Write the processed data to a CSV file."""
    if output_path is None:
        input_directory = input_path.rsplit("/", 1)[0] if "/" in input_path else "."
        input_file_name = input_path.rsplit("/", 1)[1]
        output_path = (
            f"{input_directory}/"
            f"{input_file_name.rsplit('.', 1)[0]}_processed_{by}.csv"
        )
    output.to_csv(output_path, index=False)
    logger.info("Data saved to %s", output_path)
