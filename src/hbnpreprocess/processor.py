"""Processing the HBN data."""

from pathlib import Path
from typing import Literal

import pandas as pd

from .pivot import Pivot


class Processor:
    """Class for processing the HBN data."""

    @staticmethod
    def load(input_path: str) -> pd.DataFrame:
        """Load the data."""
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"File {path} not found.")
        data = pd.read_csv(path, low_memory=False)
        if data.filter(like="Diagnosis_ClinicianConsensus").columns.empty:
            raise ValueError(
                "No columns found with 'Diagnosis_ClinicianConsensus' in the name."
            )
        return Processor._preprocess_categories(data)

    @staticmethod
    def _preprocess_categories(data: pd.DataFrame) -> pd.DataFrame:
        """Preprocess the categories."""
        cat_sub_cols = [
            (
                f"Diagnosis_ClinicianConsensus,DX_{n:02d}_Cat",
                f"Diagnosis_ClinicianConsensus,DX_{n:02d}_Sub",
            )
            for n in range(1, 11)
        ]
        for cat, sub in cat_sub_cols:
            data[sub] = data[sub].fillna(data[cat])
        return data

    @staticmethod
    def _copy_static_columns(data: pd.DataFrame) -> pd.DataFrame:
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
        by: Literal[
            "diagnoses",
            "subcategories",
            "categories",
            "all",
        ] = "all",
        qualifier_filter: list[str] | None = None,
        include_details: bool = False,
    ) -> pd.DataFrame:
        """Pivot and filter the data."""
        output = Processor._copy_static_columns(data)
        match by:
            case "diagnoses":
                output = Pivot.diagnoses(data, output, qualifier_filter)
            case "subcategories":
                output = Pivot.subcategories(
                    data, output, qualifier_filter, include_details
                )
            case "categories":
                output = Pivot.categories(
                    data, output, qualifier_filter, include_details
                )
            case "all":
                output = Pivot.diagnoses(data, output, qualifier_filter)
                output = Pivot.subcategories(
                    data, output, qualifier_filter, include_details
                )
                output = Pivot.categories(
                    data, output, qualifier_filter, include_details
                )
            case _:
                raise ValueError(f"Invalid value for 'by': {by}")
        return output
