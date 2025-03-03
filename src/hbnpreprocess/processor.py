"""Processing the HBN data."""

from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from .pivot import Pivot


class Processor:
    """Class for processing the HBN data."""

    ns = [f"{n:02d}" for n in range(1, 11)]

    def __init__(self) -> None:
        """Initialize the class."""
        pass

    @classmethod
    def load(cls, input_path: str) -> pd.DataFrame:
        """Load the data."""
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"File {path} not found.")
        data = pd.read_csv(path, low_memory=False)
        cat_cols = ["Diagnosis_ClinicianConsensus,DX_" + n + "_Cat" for n in cls.ns]
        sub_cols = ["Diagnosis_ClinicianConsensus,DX_" + n + "_Sub" for n in cls.ns]
        # TODO: move this to cleaning script?
        # replace blank subcategories with the category
        for sub, cat in zip(sub_cols, cat_cols):
            data[sub] = np.where(data[sub].isnull(), data[cat], data[sub])
        return data

    @staticmethod
    def copy(data: pd.DataFrame) -> pd.DataFrame:
        """Copy the subject data for output."""
        unchanged_cols = [
            "Identifiers",
            "Diagnosis_ClinicianConsensus,NoDX",
            "Diagnosis_ClinicianConsensus,Season",
            "Diagnosis_ClinicianConsensus,Site",
            "Diagnosis_ClinicianConsensus,Year",
        ]

        output = pd.DataFrame()
        output[unchanged_cols] = data[unchanged_cols].copy()
        # remove extra text in ID column
        output["Identifiers"] = output["Identifiers"].str.split(",").str[0]
        return output

    @staticmethod
    def pivot(
        data: pd.DataFrame,
        output: pd.DataFrame,
        by: Literal[
            "diagnoses",
            "subcategories",
            "categories",
            "all",
        ] = "all",
        certainty_filter: list[str] | None = None,
        time_filter: list[str] | None = None,
        include_details: bool = False,
    ) -> pd.DataFrame:
        """Pivot and filter the data."""
        match by:
            case "diagnoses":
                output = Pivot.diagnoses(data, output, certainty_filter, time_filter)
            case "subcategories":
                output = Pivot.subcategories(
                    data, output, certainty_filter, time_filter, include_details
                )
            case "categories":
                output = Pivot.categories(
                    data, output, certainty_filter, time_filter, include_details
                )
            case "all":
                output = Pivot.diagnoses(data, output, certainty_filter, time_filter)
                output = Pivot.subcategories(
                    data, output, certainty_filter, time_filter, include_details
                )
                output = Pivot.categories(
                    data, output, certainty_filter, time_filter, include_details
                )
            case _:
                raise ValueError(f"Invalid value for 'by': {by}")
        return output
