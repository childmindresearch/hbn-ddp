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

        values = {
            x for x in set(data[columns].values.flatten()) if pd.notna(x)
        } - cls.INVALID_DX_VALS
        return list(values)

    @staticmethod
    def _set_certainty(data: pd.DataFrame, i: int, col: str) -> str:
        """Get the certainty for a diagnosis."""
        # TODO: Consider using an enum for the certainty levels.

        is_confirmed = data.at[i, col + "_Confirmed"] == 1
        is_presum = data.at[i, col + "_Presum"] == 1
        is_rc = data.at[i, col + "_RC"] == 1
        is_ruleout = data.at[i, col + "_RuleOut"] == 1
        is_byhx = data.at[i, col + "_ByHx"] == 1

        confirmed = is_confirmed and not any([is_presum, is_rc, is_ruleout, is_byhx])
        presum = is_presum and not any([is_confirmed, is_rc, is_ruleout, is_byhx])
        rc = is_rc and not any([is_confirmed, is_presum, is_ruleout, is_byhx])
        ruleout = is_ruleout and not any([is_confirmed, is_presum, is_rc, is_byhx])
        byhx = is_byhx and not any([is_confirmed, is_presum, is_rc, is_ruleout])

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
            col_name = cls._clean_dx_value(dx_val)
            output[col_name + "_DiagnosisPresent"] = 0
            output[col_name + "_Certainty"] = None
            dx_cols = [col_name + var for var in repeated_vars]
            output[dx_cols] = None
            for i, n in itertools.product(range(0, len(data)), cls.DX_NS):
                details = cls._get_diagnosis_details(data, i, n)
                dx_n_col = f"Diagnosis_ClinicianConsensus,DX_{n}"
                # locate presence of specific diagnosis
                if details.diagnosis == dx_val:
                    # apply filter if selected and set presence of diagnosis
                    if cls._filter_pass(details.certainty, certainty_filter):
                        output.at[i, f"{col_name}_DiagnosisPresent"] = 1
                        # variables repeated by diagnosis
                        for var in repeated_vars:
                            output.at[i, col_name + var] = data.at[i, dx_n_col + var]
                        # add certainty
                        output.at[i, f"{col_name}_Certainty"] = details.certainty
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
            col_name = cls._clean_dx_value(dx_val)
            output[col_name + "_SubcategoryPresent"] = 0
            if include_details:
                # column for diagnostic level details
                output[col_name + "_Certainty"] = ""
            for i in range(0, len(data)):
                cat_details = []
                for n in cls.DX_NS:
                    details = cls._get_diagnosis_details(data, i, n)
                    if details.sub == dx_val:
                        # apply filter if selected
                        if cls._filter_pass(details.certainty, certainty_filter):
                            # set presence of subcategory
                            output.at[i, col_name + "_SubcategoryPresent"] = 1
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
                    output.at[i, col_name + "_Details"] = str(cat_details).strip("[]")
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
            col_name = cls._clean_dx_value(dx_val)
            # column for the presence of diagnostic categories
            output[col_name + "_CategoryPresent"] = 0
            if include_details:
                # column for diagnostic level details
                output[col_name + "_Certainty"] = ""
            for i in range(0, len(data)):
                cat_details = []
                for n in cls.DX_NS:
                    details = cls._get_diagnosis_details(data, i, n)
                    if details.cat == dx_val:
                        # apply filter if selected
                        if cls._filter_pass(details.certainty, certainty_filter):
                            # set presence of category
                            output.at[i, col_name + "_CategoryPresent"] = 1
                            # create dictionary to store details on a diagnostic level
                            cat_dict = {
                                "diagnosis": details.diagnosis,
                                "subcategory": details.sub,
                                "code": details.code,
                                "certainty": details.certainty,
                                "time": details.time,
                                "past_documentation": ""
                                if details.past_doc is None
                                else details.past_doc,
                            }
                            # add diagnosis level details
                            cat_details.append(cat_dict)
                # add category details to row
                if include_details and len(cat_details) > 0:
                    output.at[i, col_name + "_Details"] = str(cat_details).strip("[]")

        return output
