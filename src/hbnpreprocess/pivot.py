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
    cert: str
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
        cols.sort()
        return cols

    @staticmethod
    def _certainty(data: pd.DataFrame, i: int, col: str) -> str:
        """Get the certainty of the diagnosis."""
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
            cert = "ByHx"
        elif confirmed:
            cert = "Confirmed"
        elif presum:
            cert = "Presumptive"
        elif rc:
            cert = "RC"
        elif ruleout:
            cert = "RuleOut"
        elif past:
            cert = "Past"
        # if all missing, or conflicting certainties are present, assign 'Unknown'
        else:
            cert = "Unknown"
        return cert

    @classmethod
    def _get_diagnosis_details(cls, data: pd.DataFrame, i: int, n: str) -> Diag_Info:
        col = "Diagnosis_ClinicianConsensus,DX_" + str(n)
        return Diag_Info(
            diagnosis=data.at[i, str(col)],
            sub=data.at[i, str(col) + "_Sub"],
            cat=data.at[i, str(col) + "_Cat"],
            code=data.at[i, str(col) + "_Code"],
            past_doc=data.at[i, str(col) + "_Past_Doc"],
            cert=cls._certainty(data, i, col),
            time=data.at[i, str(col) + "_Time"],
        )

    @classmethod
    def _filter_pass(cls, cert: str, certainty_filter: Optional[List[str]]) -> bool:
        """Apply the certainty filter."""
        if certainty_filter is None:
            return True
        else:
            return certainty_filter is not None and cert in certainty_filter

    @classmethod
    def diagnoses(
        cls,
        data: pd.DataFrame,
        output: pd.DataFrame,
        certainty_filter: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Pivot the data by diagnoses."""
        repeated_vars = ["_Cat", "_Sub", "_Spec", "_Code", "_Past_Doc"]
        cols = cls._get_cols(data, "diagnoses")
        print("Diagnoses in dataset:")
        for d in cols:
            print(d)
            d_cleaned = "".join(filter(str.isalnum, d.strip()))
            # TODO: Try concatenating all new values at once for performance
            output[str(d_cleaned) + "_DiagnosisPresent"] = 0
            output[str(d_cleaned) + "_Certainty"] = None
            for var in repeated_vars:
                output[str(d_cleaned) + str(var)] = None
            for i, n in itertools.product(range(0, len(data)), cls.dx_ns):
                details = cls._get_diagnosis_details(data, i, n)
                col = "Diagnosis_ClinicianConsensus,DX_" + str(n)
                # locate presence of specific diagnosis
                if details.diagnosis == d:
                    # apply certainty filter if selected and set presence of diagnosis
                    if cls._filter_pass(details.cert, certainty_filter):
                        output = output.copy()
                        output.at[i, str(d_cleaned) + "_DiagnosisPresent"] = 1
                        # variables repeated by diagnosis
                        for var in repeated_vars:
                            output = output.copy()
                            output.at[i, str(d_cleaned) + str(var)] = data.at[
                                i, str(col) + str(var)
                            ]
                        # add certainty
                        output = output.copy()
                        output.at[i, str(d_cleaned) + "_Certainty"] = details.cert
        return output

    @classmethod
    def subcategories(
        cls,
        data: pd.DataFrame,
        output: pd.DataFrame,
        certainty_filter: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Pivot the dataset on diagnostic subcategories."""
        cols = cls._get_cols(data, "subcategories")
        print("Diagnostic subcategories in dataset:")
        for s in cols:
            print(s)
            s_cleaned = "".join(filter(str.isalnum, s.strip()))
            output[str(s_cleaned) + "_SubcategoryPresent"] = 0
            for i, n in itertools.product(range(0, len(data)), cls.dx_ns):
                details = cls._get_diagnosis_details(data, i, n)
                if details.sub == s:
                    # apply certainty filter if selected and set presence of diagnosis
                    if cls._filter_pass(details.cert, certainty_filter):
                        output = output.copy()
                        output.at[i, str(s_cleaned) + "_SubcategoryPresent"] = 1
        return output

    @classmethod
    def categories(
        cls,
        data: pd.DataFrame,
        output: pd.DataFrame,
        certainty_filter: Optional[List[str]] = None,
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
                        if cls._filter_pass(details.cert, certainty_filter):
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
                                "certainty": details,
                                "time": details.time,
                                "past_documentation": past_doc,
                            }
                            output = output.copy()
                            output.at[i, str(c_cleaned) + "_CategoryPresent"] = 1
                            # add diagnosis level details
                            cat_details.append(cat_dict)
                # add category details to DataFrame
                if all([len(cat_details) > 0, include_details]):
                    output = output.copy()
                    output.at[i, str(c_cleaned) + "_Details"] = str(cat_details).strip(
                        "[]"
                    )

        return output
