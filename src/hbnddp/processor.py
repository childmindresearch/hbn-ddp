"""Processing the HBN data."""

from pathlib import Path
from typing import Literal

import pandas as pd

from .pivot import Pivot

VALID_CERTAINTIES = ["Confirmed", "Presumptive", "RC", "RuleOut", "ByHx", "Unknown"]


class Processor:
    """Class for processing the HBN data."""

    @staticmethod
    def load(input_path: str) -> pd.DataFrame:
        """Load the data."""
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"File {path} not found.")
        try: 
            data = pd.read_csv(path, low_memory=False)
        except Exception as e:
            raise ValueError(f"Error reading {path} as CSV: {e}")
        if data.filter(like="Diagnosis_ClinicianConsensus").columns.empty:
            raise ValueError(
                "No columns found with 'Diagnosis_ClinicianConsensus' in the name."
            )
        return Processor._preprocess_categories(data)

    @staticmethod
    def _preprocess_categories(data: pd.DataFrame) -> pd.DataFrame:
        """Preprocess the categories by filling missing subcategories."""
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
        # Diagnosis_ClinicianConsensus columns that are not affected by pivoting
        unchanged_dx_cols = [
            "Diagnosis_ClinicianConsensus,NoDX",
            "Diagnosis_ClinicianConsensus,Season",
            "Diagnosis_ClinicianConsensus,Site",
            "Diagnosis_ClinicianConsensus,Year",
        ]
        # Copy ID column, any present unchanged DX columns, 
        # and any columns from other intruments.
        unchanged_cols = list(set(
            ["Identifiers"] + \
            [col for col in unchanged_dx_cols if col in data.columns] + \
            [col for col in data.columns if "Diagnosis_ClinicianConsensus" not in col]
        ))
        # Create DataFrame with copied columns to store output
        output = pd.DataFrame()
        output[unchanged_cols] = data[unchanged_cols].copy()
        # Remove extra text in ID column if present
        output["Identifiers"] = (
            output["Identifiers"].replace(",assessment", "", regex=True)
        )
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
        certainty_filter: list[str] | None = None,
        include_details: bool = False,
    ) -> pd.DataFrame:
        """Pivot and filter the data."""
        if certainty_filter is not None:
            invalid_certs = set(certainty_filter) - set(VALID_CERTAINTIES)
            if invalid_certs:
                raise ValueError(
                    f"Invalid certainty values: {invalid_certs}. "
                    f"Valid values are: {VALID_CERTAINTIES}"
                )
        output = Processor._copy_static_columns(data)
        match by:
            case "diagnoses":
                output = Pivot.diagnoses(data, output, certainty_filter)
            case "subcategories":
                output = Pivot.subcategories(
                    data, output, certainty_filter, include_details
                )
            case "categories":
                output = Pivot.categories(
                    data, output, certainty_filter, include_details
                )
            case "all":
                output = Pivot.diagnoses(data, output, certainty_filter)
                output = Pivot.subcategories(
                    data, output, certainty_filter, include_details
                )
                output = Pivot.categories(
                    data, output, certainty_filter, include_details
                )
            case _:
                raise ValueError(f"Invalid value for 'by': {by}")
        return output
