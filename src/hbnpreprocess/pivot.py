"""Pivoting for HBN data."""

import itertools
from dataclasses import dataclass
from typing import Literal, Optional
from warnings import simplefilter

import numpy as np
import pandas as pd

# Ignore performance warnings from pandas
# TODO: concatenate all new values at once for performance
simplefilter(action="ignore", category=pd.errors.PerformanceWarning)


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
    DX_COLS = ["Diagnosis_ClinicianConsensus,DX_" + n for n in DX_NS]
    DX_CAT_COLS = ["Diagnosis_ClinicianConsensus,DX_" + n + "_Cat" for n in DX_NS]
    DX_SUB_COLS = ["Diagnosis_ClinicianConsensus,DX_" + n + "_Sub" for n in DX_NS]
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
        return "".join(filter(str.isalnum, str(value).strip()))

    @classmethod
    def _get_values(
        cls,
        data: pd.DataFrame,
        by: Literal["diagnoses", "subcategories", "categories"],
    ) -> list[str]:
        # TODO: this can be cleaned up and simplified
        """Get the unique values to create columns for the pivot."""
        columns = (
            cls.DX_COLS
            if by == "diagnoses"
            else cls.DX_CAT_COLS
            if by == "categories"
            else cls.DX_SUB_COLS
            if by == "subcategories"
            else []
        )
        return sorted(
            (
                set(map(cls._clean_dx_value, data[columns].values.flatten()))
                - cls.INVALID_DX_VALS
            )
        )

    @staticmethod
    def _set_certainty(data: pd.DataFrame, i: int, col: str) -> str:
        """Get the certainty for a diagnosis."""
        # TODO: Consider using an enum for the certainty levels.
        # TODO: Rather than indexing into df every time, I think this would be clearer
        # if each of the conditions were assigned to variables that can be used in the
        # logic.

        byhx = all(
            [
                data.at[i, col + "_Confirmed"] != 1,
                data.at[i, col + "_Presum"] != 1,
                data.at[i, col + "_RC"] != 1,
                data.at[i, col + "_RuleOut"] != 1,
                data.at[i, col + "_ByHx"] == 1,
            ]
        )
        confirmed = all(
            [
                data.at[i, col + "_Confirmed"] == 1,
                data.at[i, col + "_Presum"] != 1,
                data.at[i, col + "_RC"] != 1,
                data.at[i, col + "_RuleOut"] != 1,
                data.at[i, col + "_ByHx"] != 1,
            ]
        )
        presum = all(
            [
                data.at[i, col + "_Confirmed"] != 1,
                data.at[i, col + "_Presum"] == 1,
                data.at[i, col + "_RC"] != 1,
                data.at[i, col + "_RuleOut"] != 1,
                data.at[i, col + "_ByHx"] != 1,
            ]
        )
        rc = all(
            [
                data.at[i, col + "_Confirmed"] != 1,
                data.at[i, col + "_Presum"] != 1,
                data.at[i, col + "_RC"] == 1,
                data.at[i, col + "_RuleOut"] != 1,
                data.at[i, col + "_ByHx"] != 1,
            ]
        )
        ruleout = all(
            [
                data.at[i, col + "_Confirmed"] != 1,
                data.at[i, col + "_Presum"] != 1,
                data.at[i, col + "_RC"] != 1,
                data.at[i, col + "_RuleOut"] == 1,
                data.at[i, col + "_ByHx"] != 1,
            ]
        )
        if byhx:
            certainty = "ByHx"
        elif confirmed:
            certainty = "Confirmed"
        elif presum:
            certainty = "Presumptive"
        elif rc:
            certainty = "RC"
        elif ruleout:
            certainty = "RuleOut"
        else:
            certainty = "Unknown"
        return certainty
    
    @staticmethod
    def _set_time(data: pd.DataFrame, i: int, col: str) -> str:
        """Get the time for a diagnosis."""
        past = data.at[i, col + "_Time"] == 2
        present = data.at[i, col + "_Time"] == 1
        if past:
            time = "Past"
        elif present:
            time = "Present"
        else:
            time = "Unknown"
        return time

    @classmethod
    def _get_diagnosis_details(cls, data: pd.DataFrame, i: int, n: str) -> DxInfo:
        col = f"Diagnosis_ClinicianConsensus,DX_{n}"
        return DxInfo(
            diagnosis=data.at[i, col],
            sub=data.at[i, col + "_Sub"],
            cat=data.at[i, col + "_Cat"],
            code=data.at[i, col + "_Code"],
            past_doc=data.at[i, col + "_Past_Doc"],
            certainty=cls._set_certainty(data, i, col),
            time=cls._set_time(data, i, col),
        )

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
        """Pivot the data by diagnoses."""
        repeated_vars = ["_Cat", "_Sub", "_Spec", "_Code", "_Past_Doc"]
        dx_values = cls._get_values(data, "diagnoses")
        print("Diagnoses in dataset:")
        for dx_val in dx_values:
            print(dx_val)
            output[dx_val + "_DiagnosisPresent"] = 0
            output[dx_val + "_Certainty"] = None
            dx_cols = [dx_val + var for var in repeated_vars]
            output[dx_cols] = None
            for i, n in itertools.product(range(0, len(data)), cls.DX_NS):
                details = cls._get_diagnosis_details(data, i, n)
                col = f"Diagnosis_ClinicianConsensus,DX_{n}"
                # locate presence of specific diagnosis
                if cls._clean_dx_value(details.diagnosis) == dx_val:
                    # apply filter if selected and set presence of diagnosis
                    if cls._filter_pass(details.certainty, certainty_filter):
                        output.at[i, f"{dx_val}_DiagnosisPresent"] = 1
                        # variables repeated by diagnosis
                        for var in repeated_vars:
                            output.at[i, dx_val + var] = data.at[i, col + var]
                        # add certainty
                        output.at[i, f"{dx_val}_Certainty"] = details.certainty
        return output

    @classmethod
    def subcategories(
        cls,
        data: pd.DataFrame,
        output: pd.DataFrame,
        certainty_filter: Optional[list[str]] = None,
        include_details: bool = False,
    ) -> pd.DataFrame:
        """Pivot the dataset on diagnostic subcategories."""
        dx_values = cls._get_values(data, "subcategories")
        print("Diagnostic subcategories in dataset:")
        for dx_val in dx_values:
            print(dx_val)
            output[dx_val + "_SubcategoryPresent"] = 0
            if include_details:
                # column for diagnostic level details
                output[dx_val + "_Certainty"] = ""
            for i in range(0, len(data)):
                cat_details = []
                for n in cls.DX_NS:
                    details = cls._get_diagnosis_details(data, i, n)
                    if cls._clean_dx_value(details.sub) == dx_val:
                        # apply filter if selected
                        if cls._filter_pass(details.certainty, certainty_filter):
                            # set presence of subcategory
                            output.at[i, dx_val + "_SubcategoryPresent"] = 1
                            # create dictionary to store details on a diagnostic level
                            cat_dict = {
                                "diagnosis": details.diagnosis,
                                "code": details.code,
                                "certainty": details.certainty,
                                "time": details.time,
                                "past_documentation": ""
                                if details.past_doc is None
                                else details.past_doc,
                            }
                            # add diagnosis level details
                            cat_details.append(cat_dict)
                # add subcategory details to row
                if include_details and len(cat_details) > 0:
                    output.at[i, dx_val + "_Details"] = str(cat_details).strip("[]")
        return output

    @classmethod
    def categories(
        cls,
        data: pd.DataFrame,
        output: pd.DataFrame,
        certainty_filter: list[str] | None = None,
        include_details: bool = False,
    ) -> pd.DataFrame:
        """Pivot the dataset on diagnostic categories."""
        dx_values = cls._get_values(data, "categories")
        print("Diagnostic categories in dataset:")
        for dx_val in dx_values:
            print(dx_val)
            # column for the presence of categories
            output[dx_val + "_CategoryPresent"] = 0
            if include_details:
                # column for diagnostic level details
                output[dx_val + "_Certainty"] = ""
            for i in range(0, len(data)):
                cat_details = []
                for n in cls.DX_NS:
                    details = cls._get_diagnosis_details(data, i, n)
                    if cls._clean_dx_value(details.cat) == dx_val:
                        # apply filter if selected
                        if cls._filter_pass(details.certainty, certainty_filter):
                            # set presence of category
                            output.at[i, dx_val + "_CategoryPresent"] = 1
                            # create dictionary to store details on a diagnostic level
                            cat_dict = {
                                "diagnosis": details.diagnosis,
                                "subcategory": details.sub,
                                "code": details.code,
                                "certainty": details,
                                "time": details.time,
                                "past_documentation": ""
                                if details.past_doc is None
                                else details.past_doc,
                            }
                            # add diagnosis level details
                            cat_details.append(cat_dict)
                # add category details to row
                if include_details and len(cat_details) > 0:
                    output.at[i, dx_val + "_Details"] = str(cat_details).strip("[]")

        return output
