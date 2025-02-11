"""Basic visualization of the HBN data."""

from typing import Literal

import pandas as pd
import plotly.graph_objects as go

from .utils import show


class Viz:
    """Class for visualizing the HBN data."""

    def __init__(self) -> None:
        """Initialize the class."""

    @staticmethod
    def bar(
        output: pd.DataFrame,
        col_type: Literal["DiagnosisPresent", "CategoryPresent", "SubcategoryPresent"],
    ) -> None:
        """Plot a bar graph of diagnoses, subcategories, or categories.

        Args:
            col_type: The type of data to visualize.
            output: The HBN data.

        """
        filtered_columns = [col for col in output.columns if col_type in col]
        filtered_df = output[filtered_columns]
        sums = filtered_df.sum().sort_values()
        # TODO: simplify with regex
        new_labels = [
            label.replace("_" + str(col_type), "")
            .replace("_", " ")
            .replace(" Disorders", "")
            .replace(" Disorder", "")
            for label in sums.index
        ]
        sums = list(sums.reset_index(drop=True))

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

    @classmethod
    def visualize(
        cls,
        output: pd.DataFrame,
        by: Literal["diagnoses", "subcategories", "categories", "all"],
    ) -> None:
        """Visualize the data."""
        if by == "diagnoses":
            cls.bar(output, "DiagnosisPresent")
        elif by == "subcategories":
            cls.bar(output, "SubcategoryPresent")
        elif by == "categories":
            cls.bar(output, "CategoryPresent")
        elif by == "all":
            cls.bar(output, "DiagnosisPresent")
            cls.bar(output, "SubcategoryPresent")
            cls.bar(output, "CategoryPresent")
