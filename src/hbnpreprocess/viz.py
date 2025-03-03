"""Basic visualization of the HBN data."""

from typing import Literal

import pandas as pd
import plotly.graph_objects as go

from .utils import show


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
    sums = list(sums.reset_index(drop=True))
    new_labels = [_clean_label(label, col_type) for label in filtered_df.columns]

    fig = go.Figure()
    name = col_type.replace("Present", "")
    fig.add_trace(
        go.Bar(
            y=new_labels,
            x=sums,
            name=name,
            orientation="h",
            text=sums,
        )
    )

    fig.update_layout(
        width=1200,
        height=1500,
        title="Incidence of " + str(name) + " in HBN Data",
        yaxis_title="Disorder",
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

    show(fig)


def _clean_label(label: str, col_type: str) -> str:
    return (
        label.replace("_" + str(col_type), "")
        .replace("_", " ")
        .replace(" Disorders", "")
        .replace(" Disorder", "")
    )


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
