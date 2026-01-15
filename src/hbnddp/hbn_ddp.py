"""Module for handling the HBN data."""

from pathlib import Path
from typing import Literal

import pandas as pd

from hbnddp.pivot import Pivot

from .utils import write
from .viz import visualize

VALID_CERTAINTIES = ["Confirmed", "Presumptive", "RC", "RuleOut", "ByHx", "Unknown"]


class HBNData:
    """Class for handling the HBN diagnostic data."""

    def __init__(
        self,
        data: pd.DataFrame,
        column_prefix: str,
        input_path: str | None = None,
    ) -> None:
        """Initialize the HBNData class."""
        self.input_path = input_path
        self.data = data
        self.column_prefix = column_prefix

    @classmethod
    def create(cls, input_path: str) -> "HBNData":
        """Load the data and create an HBNData instance."""
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"File {path} not found.")
        try:
            data = pd.read_csv(path, low_memory=False)
        except Exception as e:
            raise ValueError(f"Error reading {path} as CSV: {e}")
        if "Diagnosis_ClinicianConsensus,DX_01" in data.columns:
            column_prefix = "Diagnosis_ClinicianConsensus,"
        elif "DX_01" in data.columns:
            column_prefix = ""
        else:
            raise ValueError("No valid diagnosis columns found in data.")

        return cls(input_path=input_path, data=data, column_prefix=column_prefix)

    @property
    def _preprocessed_data(self) -> pd.DataFrame:
        """Preprocess the categories by filling missing subcategories."""
        cat_sub_cols = [
            (
                f"{self.column_prefix}DX_{n:02d}_Cat",
                f"{self.column_prefix}DX_{n:02d}_Sub",
            )
            for n in range(1, 11)
        ]
        processed_data = self.data.copy()
        for cat, sub in cat_sub_cols:
            processed_data[sub] = processed_data[sub].fillna(processed_data[cat])
        return processed_data

    @staticmethod
    def _copy_static_columns(data: pd.DataFrame, column_prefix: str) -> pd.DataFrame:
        """Copy the subject data for output."""
        # Diagnosis_ClinicianConsensus columns that are not affected by pivoting
        unchanged_dx_cols = [
            f"{column_prefix}NoDX",
            f"{column_prefix}Season",
            f"{column_prefix}Site",
            f"{column_prefix}Year",
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
        # fill missing subcategories before pivoting
        data = self._preprocessed_data
        column_prefix = self.column_prefix
        if certainty_filter is not None:
            invalid_certs = set(certainty_filter) - set(VALID_CERTAINTIES)
            if invalid_certs:
                raise ValueError(
                    f"Invalid certainty values: {invalid_certs}. "
                    f"Valid values are: {VALID_CERTAINTIES}"
                )
        output = self._copy_static_columns(data=data, column_prefix=column_prefix)
        match by:
            case "diagnoses":
                output = Pivot.diagnoses(
                    data=data,
                    output=output,
                    column_prefix=self.column_prefix,
                    certainty_filter=certainty_filter,
                )
            case "subcategories":
                output = Pivot.subcategories(
                    data=data,
                    output=output,
                    column_prefix=self.column_prefix,
                    certainty_filter=certainty_filter,
                    include_details=include_details,
                )
            case "categories":
                output = Pivot.categories(
                    data=data,
                    output=output,
                    column_prefix=self.column_prefix,
                    certainty_filter=certainty_filter,
                    include_details=include_details,
                )
            case "all":
                output = Pivot.diagnoses(
                    data=data,
                    output=output,
                    column_prefix=self.column_prefix,
                    certainty_filter=certainty_filter,
                )
                output = Pivot.subcategories(
                    data=data,
                    output=output,
                    column_prefix=self.column_prefix,
                    certainty_filter=certainty_filter,
                    include_details=include_details,
                )
                output = Pivot.categories(
                    data=data,
                    output=output,
                    column_prefix=self.column_prefix,
                    certainty_filter=certainty_filter,
                    include_details=include_details,
                )
            case _:
                raise ValueError(f"Invalid value for 'by': {by}")
        return output

    def process(
        self,
        output_path: str | None = None,
        by: Literal[
            "diagnoses",
            "subcategories",
            "categories",
            "all",
        ] = "all",
        certainty_filter: list[str] | None = None,
        include_details: bool = False,
        viz: bool = False,
    ) -> pd.DataFrame:
        """Process the HBN clinician consensus diagnosis data by pivoting.

        Args:
            output_path: The path to save the processed data.
            by: The level of detail to pivot the data Options are "diagnosis",
            "subcategory", "category", and "all". Default is "all".
            certainty_filter: The list of certainties to include. Accepted values
            are "Confirmed", "Presumptive", "RC", "RuleOut", "ByHx", and
            "Unknown".
            Default is None, which will include all.
            include_details: When pivoting by category or subcategory, whether to
            include diagnosis level details in a separate column as a dictionary.
            viz: Whether to visualize the data. Displays and saves a bar plot showing
            the incidence of diagnoses or categories. Default is False.

        Returns:
            The processed data.
        """
        output = self.pivot(by, certainty_filter, include_details)
        if viz:
            visualize(output, by)
        if self.input_path is not None:
            write(output, input_path=self.input_path, by=by, output_path=output_path)
        self.processed_data = output
        return output
