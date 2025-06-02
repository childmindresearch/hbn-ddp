"""Basic visualization of the HBN data."""

import os
from typing import Literal

import pandas as pd
import plotly.graph_objects as go


def _bar(
    output: pd.DataFrame,
    col_type: Literal["DiagnosisPresent", "CategoryPresent", "SubcategoryPresent"],
) -> None:
    """Plot a bar graph of diagnoses, subcategories, or categories.

    Args:
        col_type: The type of data to visualize.
        output: The HBN data.

    """
    filtered_df = output.filter(like=col_type)
    sums = filtered_df.sum().sort_values()
    labels = list(sums.index)
    sums = list(sums.reset_index(drop=True))
    new_labels = [_clean_label(label, col_type) for label in labels]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=new_labels,
            x=sums,
            orientation="h",
            text=sums,
        )
    )

    match col_type:
        case "DiagnosisPresent":
            title = "Incidence of Diagnoses in HBN Data"
        case "SubcategoryPresent":
            title = "Incidence of Subcategories in HBN Data"
        case "CategoryPresent":
            title = "Incidence of Categories in HBN Data"
        case _:
            raise ValueError(f"Invalid value for 'col_type': {col_type}")

    fig.update_layout(
        width=1200,
        height=1500,
        title=title,
        yaxis_title=col_type.replace("Present", ""),
        xaxis_title="Number of Participants",
    )
    fig.update_yaxes(
        tickangle=20,
        tickfont=dict(size=9),
        showticklabels=True,
    )
    fig.update_traces(
        textposition="outside",
    )

    _save_fig(fig, col_type)


def _clean_label(label: str, col_type: str) -> str:
    return (
        label.replace("_" + str(col_type), "")
        .replace("_", " ")
        .replace(" Disorders", "")
        .replace(" Disorder", "")
    )


def _save_fig(fig: go.Figure, col_type: str) -> None:
    """Save the figure to a file."""
    try:
        os.mkdir("./figures")
    except FileExistsError:
        pass
    col_type = col_type.replace("Present", "").lower()
    fig.write_image(f"figures/{col_type}_bar_plot.png")
    print(f"Figure saved to figures/{col_type}_bar_plot.png.")


def visualize(
    output: pd.DataFrame,
    by: Literal["diagnoses", "subcategories", "categories", "all"] = "all",
) -> None:
    """Visualize the data."""
    match by:
        case "diagnoses":
            _bar(output, "DiagnosisPresent")
        case "subcategories":
            _bar(output, "SubcategoryPresent")
        case "categories":
            _bar(output, "CategoryPresent")
        case "all":
            _bar(output, "DiagnosisPresent")
            _bar(output, "SubcategoryPresent")
            _bar(output, "CategoryPresent")
        case _:
            raise ValueError(f"Invalid value for 'by': {by}")
