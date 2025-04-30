"""Pivoting for HBN data."""

import itertools
from dataclasses import dataclass
from typing import List, Literal, Optional

import numpy as np
import pandas as pd


@dataclass
class Diag_Info:
    """Dataclass for storing diagnosis-specific information."""

    diagnosis: str
    sub: str
    cat: str
    code: str
    past_doc: str
    qual: str
    time: int


class Pivot:
    """Class for pivoting the data."""

    dx_ns = [f"{n:02d}" for n in range(1, 11)]

    @classmethod
    def _get_cols(
        cls,
        data: pd.DataFrame,
        by: Literal["diagnoses", "subcategories", "categories"],
    ) -> List[str]:
        # TODO: this can be cleaned up and simplified
        """Get the unique values to create columns for the pivot."""
        cat_cols = ["Diagnosis_ClinicianConsensus,DX_" + n + "_Cat" for n in cls.dx_ns]
        sub_cols = ["Diagnosis_ClinicianConsensus,DX_" + n + "_Sub" for n in cls.dx_ns]
        dx_cols = ["Diagnosis_ClinicianConsensus,DX_" + n for n in cls.dx_ns]

        remove = [
            "nan",
            "No Diagnosis Given",
            "No Diagnosis Given: Incomplete Eval",
            "",
            " ",
            np.nan,
        ]
        cats = list(set(data[cat_cols].values.flatten()) - set(remove))
        subs = list(set(data[sub_cols].values.flatten()) - set(remove))
        dxes = list(set(data[dx_cols].values.flatten()) - set(remove))

        if by == "diagnoses":
            cols = dxes
        elif by == "subcategories":
            cols = subs
        elif by == "categories":
            cols = cats
        # remove any non-string values if nulls were not removed before
        cols = [col for col in cols if isinstance(col, str)]
        cols.sort()
        return cols

    @staticmethod
    def _set_qualifier(data: pd.DataFrame, i: int, col: str) -> str:
        """Get the qualifier for a diagnosis."""
        # TODO: Consider using an enum for the certainty levels.
        # TODO: Rather than indexing into df every time, I think this would be clearer
        # if each of the conditions were assigned to variables that can be used in the
        # logic.
        # TODO: Another potential simplification would be to check sum(bool_values) == 1
        # to ensure only one of the conditions is met.

        byhx = all(
            [
                data.at[i, str(col) + "_Confirmed"] != 1,
                data.at[i, str(col) + "_Presum"] != 1,
                data.at[i, str(col) + "_RC"] != 1,
                data.at[i, str(col) + "_RuleOut"] != 1,
                data.at[i, str(col) + "_ByHx"] == 1,
                data.at[i, str(col) + "_Time"] == 1,
            ]
        )
        confirmed = all(
            [
                data.at[i, str(col) + "_Confirmed"] == 1,
                data.at[i, str(col) + "_Presum"] != 1,
                data.at[i, str(col) + "_RC"] != 1,
                data.at[i, str(col) + "_RuleOut"] != 1,
                data.at[i, str(col) + "_ByHx"] != 1,
                data.at[i, str(col) + "_Time"] == 1,
            ]
        )
        presum = all(
            [
                data.at[i, str(col) + "_Confirmed"] != 1,
                data.at[i, str(col) + "_Presum"] == 1,
                data.at[i, str(col) + "_RC"] != 1,
                data.at[i, str(col) + "_RuleOut"] != 1,
                data.at[i, str(col) + "_ByHx"] != 1,
                data.at[i, str(col) + "_Time"] == 1,
            ]
        )
        rc = all(
            [
                data.at[i, str(col) + "_Confirmed"] != 1,
                data.at[i, str(col) + "_Presum"] != 1,
                data.at[i, str(col) + "_RC"] == 1,
                data.at[i, str(col) + "_RuleOut"] != 1,
                data.at[i, str(col) + "_ByHx"] != 1,
                data.at[i, str(col) + "_Time"] == 1,
            ]
        )
        ruleout = all(
            [
                data.at[i, str(col) + "_Confirmed"] != 1,
                data.at[i, str(col) + "_Presum"] != 1,
                data.at[i, str(col) + "_RC"] != 1,
                data.at[i, str(col) + "_RuleOut"] == 1,
                data.at[i, str(col) + "_ByHx"] != 1,
                data.at[i, str(col) + "_Time"] == 1,
            ]
        )
        past = all(
            [
                data.at[i, str(col) + "_Confirmed"] != 1,
                data.at[i, str(col) + "_Presum"] != 1,
                data.at[i, str(col) + "_RC"] != 1,
                data.at[i, str(col) + "_RuleOut"] != 1,
                data.at[i, str(col) + "_ByHx"] != 1,
                data.at[i, str(col) + "_Time"] == 2,
            ]
        )
        if byhx:
            qual = "ByHx"
        elif confirmed:
            qual = "Confirmed"
        elif presum:
            qual = "Presumptive"
        elif rc:
            qual = "RC"
        elif ruleout:
            qual = "RuleOut"
        elif past:
            qual = "Past"
        # if all missing, or conflicting certainties are present, assign 'Unknown'
        else:
            qual = "Unknown"
        return qual

    @classmethod
    def _get_diagnosis_details(cls, data: pd.DataFrame, i: int, n: str) -> Diag_Info:
        col = "Diagnosis_ClinicianConsensus,DX_" + str(n)
        return Diag_Info(
            diagnosis=data.at[i, str(col)],
            sub=data.at[i, str(col) + "_Sub"],
            cat=data.at[i, str(col) + "_Cat"],
            code=data.at[i, str(col) + "_Code"],
            past_doc=data.at[i, str(col) + "_Past_Doc"],
            qual=cls._set_qualifier(data, i, col),
            time=data.at[i, str(col) + "_Time"],
        )

    @classmethod
    def _filter_pass(cls, qual: str, qualifier_filter: Optional[List[str]]) -> bool:
        """Apply the filter."""
        if qualifier_filter is None:
            return True
        else:
            return qualifier_filter is not None and qual in qualifier_filter

    @classmethod
    def diagnoses(
        cls,
        data: pd.DataFrame,
        output: pd.DataFrame,
        qualifier_filter: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Pivot the data by diagnoses."""
        repeated_vars = ["_Cat", "_Sub", "_Spec", "_Code", "_Past_Doc"]
        cols = cls._get_cols(data, "diagnoses")
        print("Diagnoses in dataset:")
        for c in cols:
            print(c)
            c_cleaned = "".join(filter(str.isalnum, c.strip()))
            # TODO: Try concatenating all new values at once for performance
            output[str(c_cleaned) + "_DiagnosisPresent"] = 0
            output[str(c_cleaned) + "_Certainty"] = None
            for var in repeated_vars:
                output[str(c_cleaned) + str(var)] = None
            for i, n in itertools.product(range(0, len(data)), cls.dx_ns):
                details = cls._get_diagnosis_details(data, i, n)
                col = "Diagnosis_ClinicianConsensus,DX_" + str(n)
                # locate presence of specific diagnosis
                if details.diagnosis == c:
                    # apply filter if selected and set presence of diagnosis
                    if cls._filter_pass(details.qual, qualifier_filter):
                        output = output.copy()
                        output.at[i, str(c_cleaned) + "_DiagnosisPresent"] = 1
                        # variables repeated by diagnosis
                        for var in repeated_vars:
                            output = output.copy()
                            output.at[i, str(c_cleaned) + str(var)] = data.at[
                                i, str(col) + str(var)
                            ]
                        # add qualifier
                        output = output.copy()
                        output.at[i, str(c_cleaned) + "_Qualifier"] = details.qual
        return output

    @classmethod
    def subcategories(
        cls,
        data: pd.DataFrame,
        output: pd.DataFrame,
        qualifier_filter: Optional[List[str]] = None,
        include_details: bool = False,
    ) -> pd.DataFrame:
        """Pivot the dataset on diagnostic subcategories."""
        cols = cls._get_cols(data, "subcategories")
        print("Diagnostic subcategories in dataset:")
        for c in cols:
            print(c)
            c_cleaned = "".join(filter(str.isalnum, c.strip()))
            output[str(c_cleaned) + "_SubcategoryPresent"] = 0
            if include_details:
                # column for diagnostic level details
                output[str(c_cleaned) + "_Details"] = ""
            for i in range(0, len(data)):
                cat_details = []
                for n in cls.dx_ns:
                    details = cls._get_diagnosis_details(data, i, n)
                    if details.sub == c:
                        # apply filter if selected
                        if cls._filter_pass(details.qual, qualifier_filter):
                            # set presence of subcategory
                            output = output.copy()
                            output.at[i, str(c_cleaned) + "_SubcategoryPresent"] = 1
                            # create dictionary to store details on a diagnostic level
                            match details.past_doc:
                                case None:
                                    past_doc = ""
                                case _:
                                    past_doc = details.past_doc
                            cat_dict = {
                                "diagnosis": details.diagnosis,
                                "code": details.code,
                                "qualifier": details.qual,
                                "time": details.time,
                                "past_documentation": past_doc,
                            }
                            # add diagnosis level details
                            cat_details.append(cat_dict)
                # add subcategory details to row
                if all([len(cat_details) > 0, include_details]):
                    output = output.copy()
                    output.at[i, str(c_cleaned) + "_Details"] = str(cat_details).strip(
                        "[]"
                    )
        return output

    @classmethod
    def categories(
        cls,
        data: pd.DataFrame,
        output: pd.DataFrame,
        qualifier_filter: Optional[List[str]] = None,
        include_details: bool = False,
    ) -> pd.DataFrame:
        """Pivot the dataset on diagnostic categories."""
        cols = cls._get_cols(data, "categories")
        print("Diagnostic categories in dataset:")
        for c in cols:
            print(c)
            c_cleaned = "".join(filter(str.isalnum, c.strip()))
            # column for the presence of categories
            output[str(c_cleaned) + "_CategoryPresent"] = 0
            if include_details:
                # column for diagnostic level details
                output[str(c_cleaned) + "_Details"] = ""
            for i in range(0, len(data)):
                cat_details = []
                for n in cls.dx_ns:
                    details = cls._get_diagnosis_details(data, i, n)
                    if details.cat == c:
                        # apply filter if selected
                        if cls._filter_pass(details.qual, qualifier_filter):
                            output = output.copy()
                            # set presence of category
                            output.at[i, str(c_cleaned) + "_CategoryPresent"] = 1
                            # create dictionary to store details on a diagnostic level
                            match details.past_doc:
                                case None:
                                    past_doc = ""
                                case _:
                                    past_doc = details.past_doc
                            cat_dict = {
                                "diagnosis": details.diagnosis,
                                "subcategory": details.sub,
                                "code": details.code,
                                "qualifier": details,
                                "time": details.time,
                                "past_documentation": past_doc,
                            }
                            # add diagnosis level details
                            cat_details.append(cat_dict)
                # add category details to row
                if all([len(cat_details) > 0, include_details]):
                    output = output.copy()
                    output.at[i, str(c_cleaned) + "_Details"] = str(cat_details).strip(
                        "[]"
                    )

        return output
