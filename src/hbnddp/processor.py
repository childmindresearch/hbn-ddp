"""Processing the HBN data."""

from pathlib import Path
from typing import Literal

import pandas as pd

from .pivot import Pivot

VALID_CERTAINTIES = ["Confirmed", "Presumptive", "RC", "RuleOut", "ByHx", "Unknown"]


class Processor:
    """Class for processing the HBN data."""

    def __init__(self) -> None:
        """Initialize the Processor class."""
        self.column_prefix: str | None = None

    def load(self, input_path: str) -> pd.DataFrame:
        """Load the data."""
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"File {path} not found.")
        try:
            data = pd.read_csv(path, low_memory=False)
        except Exception as e:
            raise ValueError(f"Error reading {path} as CSV: {e}")
        if "Diagnosis_ClinicianConsensus,DX_01" in data.columns:
            self.column_prefix = "Diagnosis_ClinicianConsensus,"
        elif "DX_01" in data.columns:
            self.column_prefix = ""
        else:
            raise ValueError("No valid diagnosis columns found in data.")
        # if data.filter(like="Diagnosis_ClinicianConsensus").columns.empty:
        #     raise ValueError(
        #         "No columns found with 'Diagnosis_ClinicianConsensus' in the name."
        #     )
        return self._preprocess_categories(data=data)

    def _preprocess_categories(self, data: pd.DataFrame) -> pd.DataFrame:
        """Preprocess the categories by filling missing subcategories."""
        cat_sub_cols = [
            (
                f"{self.column_prefix}DX_{n:02d}_Cat",
                f"{self.column_prefix}DX_{n:02d}_Sub",
            )
            for n in range(1, 11)
        ]
        for cat, sub in cat_sub_cols:
            data[sub] = data[sub].fillna(data[cat])
        return data

    def _copy_static_columns(self, data: pd.DataFrame) -> pd.DataFrame:
        """Copy the subject data for output."""
        # Diagnosis_ClinicianConsensus columns that are not affected by pivoting
        unchanged_dx_cols = [
            f"{self.column_prefix}NoDX",
            f"{self.column_prefix}Season",
            f"{self.column_prefix}Site",
            f"{self.column_prefix}Year",
        ]
        # Copy ID column, any present unchanged DX columns,
        # and any columns from other intruments.
        unchanged_cols = ["Identifiers"] + [
            col for col in unchanged_dx_cols if col in data.columns
        ]
        # Create DataFrame with copied columns to store output
        output = pd.DataFrame()
        output[unchanged_cols] = data[unchanged_cols].copy()
        # Remove extra text in ID column if present
        output["Identifiers"] = output["Identifiers"].replace(
            ",assessment", "", regex=True
        )
        return output

    def pivot(
        self,
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
        output = self._copy_static_columns(data=data)
        match by:
            case "diagnoses":
                output = Pivot.diagnoses(
                    data,
                    output,
                    certainty_filter,
                    self.column_prefix,
                )
            case "subcategories":
                output = Pivot.subcategories(
                    data, output, certainty_filter, include_details, self.column_prefix
                )
            case "categories":
                output = Pivot.categories(
                    data, output, certainty_filter, include_details, self.column_prefix
                )
            case "all":
                output = Pivot.diagnoses(
                    data,
                    output,
                    certainty_filter,
                    self.column_prefix,
                )
                output = Pivot.subcategories(
                    data, output, certainty_filter, include_details, self.column_prefix
                )
                output = Pivot.categories(
                    data, output, certainty_filter, include_details, self.column_prefix
                )
            case _:
                raise ValueError(f"Invalid value for 'by': {by}")
        return output
