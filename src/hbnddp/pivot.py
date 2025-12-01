"""Pivoting for HBN data."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, Optional

import numpy as np
import pandas as pd

TIME_COURSE_DXES = [
    "Major Depressive Disorder",
    "Persistent Depressive Disorder (Dysthymia)",
]


class CertaintyLevel(Enum):
    """Enum for certainty levels."""

    BY_HX = "ByHx"
    CONFIRMED = "Confirmed"
    PRESUMPTIVE = "Presumptive"
    RC = "RC"
    RULE_OUT = "RuleOut"
    UNKNOWN = "Unknown"


class TimeCode(Enum):
    """Enum for time codes."""

    PRESENT = 1
    PAST = 2


@dataclass
class DxInfo:
    """Dataclass for storing diagnosis-specific information."""

    diagnosis: str
    sub: str
    cat: str
    code: str
    past_doc: str
    certainty: str
    time: str


class Pivot:
    """Class for pivoting the data."""

    DX_NS = [f"{n:02d}" for n in range(1, 11)]
    DX_COLS = [f"Diagnosis_ClinicianConsensus,DX_{n}" for n in DX_NS]
    DX_CAT_COLS = [f"Diagnosis_ClinicianConsensus,DX_{n}_Cat" for n in DX_NS]
    DX_SUB_COLS = [f"Diagnosis_ClinicianConsensus,DX_{n}_Sub" for n in DX_NS]
    INVALID_DX_VALS = {
        "nan",
        "No Diagnosis Given",
        "No Diagnosis Given: Incomplete Eval",
        "",
        " ",
        np.nan,
    }

    @classmethod
    def _clean_dx_value(cls, value: str) -> str:
        """Clean diagnosis value to use as column name."""
        cleaned = re.sub(r"[^\w\s/-]", "", str(value).strip())
        cleaned = cleaned.replace("/", "_").replace("-", "_")
        return cleaned.replace(" ", "_")

    @classmethod
    def _get_values(
        cls,
        data: pd.DataFrame,
        by: Literal["diagnoses", "subcategories", "categories"],
    ) -> list[str]:
        """Get the unique values to create columns for the pivot."""
        match by:
            case "diagnoses":
                columns = cls.DX_COLS
            case "categories":
                columns = cls.DX_CAT_COLS
            case "subcategories":
                columns = cls.DX_SUB_COLS
            case _:
                columns = []
        # Filter for columns that exist in the data
        columns = [col for col in columns if col in data.columns]
        # Get unique values excluding invalid ones
        values = {
            x for x in set(data[columns].values.flatten()) if pd.notna(x)
        } - cls.INVALID_DX_VALS
        return sorted(list(values))

    @staticmethod
    def _set_certainty(data: pd.DataFrame, i: int, col: str) -> str:
        """Get the certainty for a diagnosis."""
        certainty_conds = [
            (CertaintyLevel.BY_HX.value, data.at[i, f"{col}_ByHx"] == 1),
            (CertaintyLevel.CONFIRMED.value, data.at[i, f"{col}_Confirmed"] == 1),
            (CertaintyLevel.PRESUMPTIVE.value, data.at[i, f"{col}_Presum"] == 1),
            (CertaintyLevel.RC.value, data.at[i, f"{col}_RC"] == 1),
            (CertaintyLevel.RULE_OUT.value, data.at[i, f"{col}_RuleOut"] == 1),
        ]

        certainty_matches = [name for name, cond in certainty_conds if cond]
        if len(certainty_matches) == 1:
            certainty = certainty_matches[0]
        elif len(certainty_matches) > 1:
            # multiple certainties
            certainty = CertaintyLevel.UNKNOWN.value
        else:
            # no certainties
            certainty = CertaintyLevel.UNKNOWN.value

        return certainty

    @staticmethod
    def _set_time(data: pd.DataFrame, i: int, col: str) -> str:
        """Get the time for a diagnosis."""
        # set time to specific time course for applicable diagnoses
        if data.at[i, f"{col}"] in TIME_COURSE_DXES:
            time = "Specific Time Course"
        elif data.at[i, f"{col}_Time"] == TimeCode.PAST.value:
            time = "Past"
        elif data.at[i, f"{col}_Time"] == TimeCode.PRESENT.value:
            time = "Present"
        else:
            time = "Unknown"
        return time

    @classmethod
    def _get_diagnosis_details(cls, data: pd.DataFrame, i: int, n: str) -> DxInfo:
        col = f"Diagnosis_ClinicianConsensus,DX_{n}"
        details = DxInfo(
            diagnosis=data.at[i, col],
            sub=data.at[i, f"{col}_Sub"],
            cat=data.at[i, f"{col}_Cat"],
            code=data.at[i, f"{col}_Code"],
            past_doc=data.at[i, f"{col}_Past_Doc"],
            certainty=cls._set_certainty(data, i, col),
            time=cls._set_time(data, i, col),
        )

        return details

    @classmethod
    def _filter_pass(cls, certainty: str, certainty_filter: list[str] | None) -> bool:
        """Apply the filter."""
        return certainty_filter is None or certainty in certainty_filter

    @classmethod
    def diagnoses(
        cls,
        data: pd.DataFrame,
        output: pd.DataFrame,
        certainty_filter: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Pivot the data by diagnoses.

        Args:
            data: Input DataFrame with HBN diagnostic data
            output: Output DataFrame to append pivoted columns to
            certainty_filter: Optional list of certainty levels to include

        Returns:
            Output DataFrame with diagnosis columns added
        """
        repeated_vars = ["_Cat", "_Sub", "_Spec", "_ICD_Code", "_Past_Doc"]
        dx_values = cls._get_values(data, "diagnoses")
        print("Diagnoses in dataset:")

        # Dictionary to collect all new columns
        all_new_cols: dict[str, Any] = {}

        for dx_val in dx_values:
            print(dx_val)
            col_name = cls._clean_dx_value(dx_val)

            # Collect all updates for this diagnosis
            present_data = [0] * len(data)
            certainty_data: list[str | None] = [None] * len(data)
            time_data: list[str | None] = [None] * len(data)
            repeated_data: dict[str, list[str | int | None]] = {
                var: [None] * len(data) for var in repeated_vars
            }

            for i in range(len(data)):
                for n in cls.DX_NS:
                    details = cls._get_diagnosis_details(data, i, n)

                    # Check if this row has the specific diagnosis
                    if details.diagnosis == dx_val:
                        # Apply filter if selected
                        if cls._filter_pass(details.certainty, certainty_filter):
                            present_data[i] = 1
                            certainty_data[i] = details.certainty
                            time_data[i] = details.time

                            # Store repeated variables data
                            for var in repeated_vars:
                                original_var_name = (
                                    "_Code" if var == "_ICD_Code" else var
                                )
                                repeated_data[var][i] = data.at[
                                    i,
                                    f"Diagnosis_ClinicianConsensus,DX_{n}{original_var_name}",
                                ]

                            # If dx is found, do not need to check other dx numbers
                            break

            # Store columns for this diagnosis
            all_new_cols[f"{col_name}_DiagnosisPresent"] = present_data
            all_new_cols[f"{col_name}_Certainty"] = certainty_data
            all_new_cols[f"{col_name}_Time"] = time_data
            for var in repeated_vars:
                all_new_cols[f"{col_name}{var}"] = repeated_data[var]

        # Add all new columns at once to avoid fragmentation
        new_df = pd.DataFrame(all_new_cols, index=output.index)
        output = pd.concat([output, new_df], axis=1)

        return output

    @classmethod
    def subcategories(
        cls,
        data: pd.DataFrame,
        output: pd.DataFrame,
        certainty_filter: Optional[list[str]] = None,
        include_details: bool = False,
    ) -> pd.DataFrame:
        """Pivot the dataset on diagnostic subcategories.

        Args:
            data: Input DataFrame with HBN diagnostic data
            output: Output DataFrame to append pivoted columns to
            certainty_filter: Optional list of certainty levels to include
            include_details: Whether to include diagnosis-level details.
            These will be stored in a single column per subcategory.

        Returns:
            Output DataFrame with subcategory columns added
        """
        dx_values = cls._get_values(data, "subcategories")
        print("Diagnostic subcategories in dataset:")

        # Dictionary to collect all new columns
        all_new_cols: dict[str, Any] = {}

        for dx_val in dx_values:
            print(dx_val)
            col_name = cls._clean_dx_value(dx_val)

            # Collect all updates for this subcategory
            present_data = [0] * len(data)
            details_data: list[str] = [""] * len(data) if include_details else []

            for i in range(len(data)):
                cat_details = []
                for n in cls.DX_NS:
                    details = cls._get_diagnosis_details(data, i, n)
                    if details.sub == dx_val:
                        # Apply filter if selected
                        if cls._filter_pass(details.certainty, certainty_filter):
                            present_data[i] = 1

                            # Create dictionary to store details on a diagnostic level
                            cat_dict = {
                                "diagnosis": details.diagnosis,
                                "ICD_code": details.code,
                                "certainty": details.certainty,
                                "time": details.time,
                                "past_documentation": ""
                                if details.past_doc is None
                                else details.past_doc,
                            }
                            cat_details.append(cat_dict)

                # Store subcategory details
                if include_details and cat_details:
                    details_data[i] = str(cat_details).strip("[]")

            # Store columns for this subcategory
            all_new_cols[f"{col_name}_SubcategoryPresent"] = present_data
            if include_details:
                all_new_cols[f"{col_name}_Details"] = details_data

        # Add all new columns at once to avoid fragmentation
        new_df = pd.DataFrame(all_new_cols, index=output.index)
        output = pd.concat([output, new_df], axis=1)

        return output

    @classmethod
    def categories(
        cls,
        data: pd.DataFrame,
        output: pd.DataFrame,
        certainty_filter: list[str] | None = None,
        include_details: bool = False,
    ) -> pd.DataFrame:
        """Pivot the dataset on diagnostic categories.

        Args:
            data: Input DataFrame with HBN diagnostic data
            output: Output DataFrame to append pivoted columns to
            certainty_filter: Optional list of certainty levels to include
            include_details: Whether to include diagnosis-level details.
            These will be stored in a single column per category.

        Returns:
            Output DataFrame with category columns added
        """
        dx_values = cls._get_values(data, "categories")
        print("Diagnostic categories in dataset:")

        # Dictionary to collect all new columns
        all_new_cols: dict[str, Any] = {}

        for dx_val in dx_values:
            print(dx_val)
            col_name = cls._clean_dx_value(dx_val)

            # Collect all updates for this category
            present_data = [0] * len(data)
            details_data: list[str] = [""] * len(data) if include_details else []

            for i in range(len(data)):
                cat_details = []
                for n in cls.DX_NS:
                    details = cls._get_diagnosis_details(data, i, n)
                    if details.cat == dx_val:
                        # Apply filter if selected
                        if cls._filter_pass(details.certainty, certainty_filter):
                            present_data[i] = 1

                            # Create dictionary to store details on a diagnostic level
                            cat_dict = {
                                "diagnosis": details.diagnosis,
                                "subcategory": details.sub,
                                "ICD_code": details.code,
                                "certainty": details.certainty,
                                "time": details.time,
                                "past_documentation": ""
                                if details.past_doc is None
                                else details.past_doc,
                            }
                            cat_details.append(cat_dict)

                # Store category details
                if include_details and cat_details:
                    details_data[i] = str(cat_details).strip("[]")

            # Store columns for this category
            all_new_cols[f"{col_name}_CategoryPresent"] = present_data
            if include_details:
                all_new_cols[f"{col_name}_Details"] = details_data

        # Add all new columns at once to avoid fragmentation
        new_df = pd.DataFrame(all_new_cols, index=output.index)
        output = pd.concat([output, new_df], axis=1)

        return output
