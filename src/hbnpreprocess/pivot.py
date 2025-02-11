"""Pivoting for HBN data."""

import itertools
from typing import List, Literal, Optional

import numpy as np
import pandas as pd


class Pivot:
    """Class for pivoting the data."""

    dx_ns = [f"{n:02d}" for n in range(1, 11)]

    def __init__(self) -> None:
        """Initialize the class."""

    @classmethod
    def get_cols(
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
    def certainty(data: pd.DataFrame, i: int, col: str) -> str:
        """Get the certainty of the diagnosis."""
        # TODO: Consider using an enum for the certainty levels.
        # TODO: Rather than indexing into df every time, I think this would be clearer
        # if each of the conditions were assigned to variables that can be used in the
        # logic.
        # TODO: Another potential simplification would be to check sum(bool_values) == 1
        # to ensure only one of the conditions is met.
        if all(
            [
                data.at[i, str(col) + "_Confirmed"] != 1,
                data.at[i, str(col) + "_Presum"] != 1,
                data.at[i, str(col) + "_RC"] != 1,
                data.at[i, str(col) + "_RuleOut"] != 1,
                data.at[i, str(col) + "_ByHx"] == 1,
            ]
        ):
            cert = "ByHx"
        elif all(
            [
                data.at[i, str(col) + "_Confirmed"] == 1,
                data.at[i, str(col) + "_Presum"] != 1,
                data.at[i, str(col) + "_RC"] != 1,
                data.at[i, str(col) + "_RuleOut"] != 1,
                data.at[i, str(col) + "_ByHx"] != 1,
            ]
        ):
            cert = "Confirmed"
        elif all(
            [
                data.at[i, str(col) + "_Confirmed"] != 1,
                data.at[i, str(col) + "_Presum"] == 1,
                data.at[i, str(col) + "_RC"] != 1,
                data.at[i, str(col) + "_RuleOut"] != 1,
                data.at[i, str(col) + "_ByHx"] != 1,
            ]
        ):
            cert = "Presumptive"
        elif all(
            [
                data.at[i, str(col) + "_Confirmed"] != 1,
                data.at[i, str(col) + "_Presum"] != 1,
                data.at[i, str(col) + "_RC"] == 1,
                data.at[i, str(col) + "_RuleOut"] != 1,
                data.at[i, str(col) + "_ByHx"] != 1,
            ]
        ):
            cert = "RC"
        elif all(
            [
                data.at[i, str(col) + "_Confirmed"] != 1,
                data.at[i, str(col) + "_Presum"] != 1,
                data.at[i, str(col) + "_RC"] != 1,
                data.at[i, str(col) + "_RuleOut"] == 1,
                data.at[i, str(col) + "_ByHx"] != 1,
            ]
        ):
            cert = "RuleOut"
        # if certainties are 0 and time = 2, assign 'N/A' these are past diagnoses
        # noted in Past_Doc
        elif all(
            [
                data.at[i, str(col) + "_Time"] == 2,
                data.at[i, str(col) + "_Confirmed"] == 0,
                data.at[i, str(col) + "_Presum"] == 0,
                data.at[i, str(col) + "_RC"] == 0,
                data.at[i, str(col) + "_RuleOut"] == 0,
                data.at[i, str(col) + "_ByHx"] != 1,
            ]
        ):
            cert = "N/A"
        # if all missing, or conflicting certainties are present,assign 'Unknown'
        else:
            cert = "Unknown"
        return cert

    @classmethod
    def diagnoses(
        cls,
        data: pd.DataFrame,
        output: pd.DataFrame,
        certainty_filter: Optional[List[str]] = None,
        time_filter: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Pivot the data by diagnoses."""
        repeated_vars = ["_Cat", "_Sub", "_Spec", "_Code", "_Past_Doc"]
        cols = cls.get_cols(data, "diagnoses")
        print("Diagnoses in dataset:")
        for d in cols:
            print(d)
            d_cleaned = "".join(filter(str.isalnum, d.strip()))
            # TODO: Why all the copies?
            output = output.copy()
            output[str(d_cleaned) + "_DiagnosisPresent"] = 0
            output = output.copy()
            output[str(d_cleaned) + "_Certainty"] = ""
            output = output.copy()
            output[str(d_cleaned) + "_Time"] = ""
            for var in repeated_vars:
                output = output.copy()
                output[str(d_cleaned) + str(var)] = ""
            # iterate through each participant and diagnosis
            # TODO: This is a lot of nested logic, would recommend breaking up into
            # smaller functions
            for i, n in itertools.product(range(0, len(data)), cls.dx_ns):
                col = "Diagnosis_ClinicianConsensus,DX_" + str(n)
                # locate presence of specific diagnosis
                if data.at[i, str(col)] == d:
                    # set certainty
                    cert = cls.certainty(data, i, col)
                    # set time
                    if data.at[i, str(col) + "_Time"] == 1:
                        time = "Current"
                    elif data.at[i, str(col) + "_Time"] == 2:
                        time = "Past"
                    # apply certainty filter if selected and set presence of diagnosis
                    if certainty_filter is not None and time_filter is None:
                        if any([cert == x for x in certainty_filter]):
                            output = output.copy()
                            output.at[i, str(d_cleaned) + "_DiagnosisPresent"] = 1
                            # variables repeated by diagnosis
                            for var in repeated_vars:
                                output = output.copy()
                                output.at[i, str(d_cleaned) + str(var)] = data.at[
                                    i, str(col) + str(var)
                                ]
                            # add certainty to DataFrame
                            output = output.copy()
                            output.at[i, str(d_cleaned) + "_Certainty"] = cert
                            # add time to DataFrame
                            output = output.copy()
                            output.at[i, str(d_cleaned) + "_Time"] = time
                    elif time_filter is not None and certainty_filter is None:
                        if any([time == x for x in time_filter]):
                            output = output.copy()
                            output.at[i, str(d_cleaned) + "_DiagnosisPresent"] = 1
                            # variables repeated by diagnosis
                            for var in repeated_vars:
                                output = output.copy()
                                output.at[i, str(d_cleaned) + str(var)] = data.at[
                                    i, str(col) + str(var)
                                ]
                            # add certainty to DataFrame
                            output = output.copy()
                            output.at[i, str(d_cleaned) + "_Certainty"] = cert
                            # add time to DataFrame
                            output = output.copy()
                            output.at[i, str(d_cleaned) + "_Time"] = time
                    elif time_filter is not None and certainty_filter is not None:
                        if all(
                            [
                                any([cert == x for x in certainty_filter]),
                                any([time == x for x in time_filter]),
                            ]
                        ):
                            output = output.copy()
                            output.at[i, str(d_cleaned) + "_DiagnosisPresent"] = 1
                            # variables repeated by diagnosis
                            for var in repeated_vars:
                                output = output.copy()
                                output.at[i, str(d_cleaned) + str(var)] = data.at[
                                    i, str(col) + str(var)
                                ]
                            # add certainty to DataFrame
                            output = output.copy()
                            output.at[i, str(d_cleaned) + "_Certainty"] = cert
                            # add time to DataFrame
                            output = output.copy()
                            output.at[i, str(d_cleaned) + "_Time"] = time
                    # no certainty filter set
                    elif time_filter is None and certainty_filter is None:
                        output = output.copy()
                        output.at[i, str(d_cleaned) + "_DiagnosisPresent"] = 1
                        # variables repeated by diagnosis
                        for var in repeated_vars:
                            output = output.copy()
                            output.at[i, str(d_cleaned) + str(var)] = data.at[
                                i, str(col) + str(var)
                            ]
                        # add certainty to DataFrame
                        output = output.copy()
                        output.at[i, str(d_cleaned) + "_Certainty"] = cert
                        # add time to DataFrame
                        output = output.copy()
                        output.at[i, str(d_cleaned) + "_Time"] = time
        return output

    @classmethod
    def subcategories(
        cls,
        data: pd.DataFrame,
        output: pd.DataFrame,
        certainty_filter: Optional[List[str]] = None,
        time_filter: Optional[List[str]] = None,
        include_details: bool = False,
    ) -> pd.DataFrame:
        """Pivot the dataset on diagnostic subcategories."""
        cols = cls.get_cols(data, "subcategories")
        print("Diagnostic subcategories in dataset:")
        for s in cols:
            print(s)
            s_cleaned = "".join(filter(str.isalnum, s.strip()))
            output[str(s_cleaned) + "_SubcategoryPresent"] = 0
            if include_details:
                # column for higher level category
                output = output.copy()
                output[str(s_cleaned) + "_Category"] = ""
                # column for diagnostic level details
                output = output.copy()
                output[str(s_cleaned) + "_Details"] = ""

            for i in range(0, len(data)):
                sub_details = []
                for n in cls.dx_ns:
                    col = "Diagnosis_ClinicianConsensus,DX_" + str(n)
                    if data.at[i, str(col) + "_Sub"] == s:
                        # set certainty
                        cert = cls.certainty(data, i, col)
                        # set time
                        if data.at[i, str(col) + "_Time"] == 1:
                            time = "Current"
                        elif data.at[i, str(col) + "_Time"] == 2:
                            time = "Past"
                        # set specific diagnosis, code and past documentation
                        d = data.at[i, str(col)]
                        code = data.at[i, str(col) + "_Code"]
                        if pd.isna(data.at[i, str(col) + "_Past_Doc"]):
                            past_doc = ""
                        else:
                            past_doc = str(int(data.at[i, str(col) + "_Past_Doc"]))
                        # create dictionary to store details on a diagnostic level
                        sub_dict = {
                            "diagnosis": d,
                            "code": code,
                            "certainty": cert,
                            "time": time,
                            "past_documentation": past_doc,
                        }
                        if certainty_filter is not None and time_filter is None:
                            if any([cert == x for x in certainty_filter]):
                                output = output.copy()
                                output.at[i, str(s_cleaned) + "_SubcategoryPresent"] = 1
                                # add diagnosis level details
                                sub_details.append(sub_dict)
                                # add higher level category
                                if include_details:
                                    output = output.copy()
                                    output.at[i, str(s_cleaned) + "_Cat"] = data.at[
                                        i,
                                        "Diagnosis_ClinicianConsensus,DX_"
                                        + str(n)
                                        + "_Cat",
                                    ]
                        elif time_filter is not None and certainty_filter is None:
                            if any([time == x for x in time_filter]):
                                output = output.copy()
                                output.at[i, str(s_cleaned) + "_SubcategoryPresent"] = 1
                                # add diagnosis level details
                                sub_details.append(sub_dict)
                                # add higher level category
                                if include_details:
                                    output = output.copy()
                                    output.at[i, str(s_cleaned) + "_Cat"] = data.at[
                                        i,
                                        "Diagnosis_ClinicianConsensus,DX_"
                                        + str(n)
                                        + "_Cat",
                                    ]
                        elif time_filter is not None and certainty_filter is not None:
                            if all(
                                [
                                    any([cert == x for x in certainty_filter]),
                                    any([time == x for x in time_filter]),
                                ]
                            ):
                                output = output.copy()
                                output.at[i, str(s_cleaned) + "_SubcategoryPresent"] = 1
                                # add diagnosis level details
                                sub_details.append(sub_dict)
                                # add higher level category
                                if include_details:
                                    output = output.copy()
                                    output.at[i, str(s_cleaned) + "_Cat"] = data.at[
                                        i,
                                        "Diagnosis_ClinicianConsensus,DX_"
                                        + str(n)
                                        + "_Cat",
                                    ]
                        elif time_filter is None and certainty_filter is None:
                            output = output.copy()
                            output.at[i, str(s_cleaned) + "_SubcategoryPresent"] = 1
                            # add diagnosis level details
                            sub_details.append(sub_dict)
                            # add higher level category
                            if include_details:
                                output = output.copy()
                                output.at[i, str(s_cleaned) + "_Category"] = data.at[
                                    i,
                                    "Diagnosis_ClinicianConsensus,DX_"
                                    + str(n)
                                    + "_Cat",
                                ]
                # add subcategory details to DataFrame
                if all([len(sub_details) > 0, include_details]):
                    output = output.copy()
                    output.at[i, str(s_cleaned) + "_Details"] = str(sub_details).strip(
                        "[]"
                    )
        return output

    @classmethod
    def categories(
        cls,
        data: pd.DataFrame,
        output: pd.DataFrame,
        certainty_filter: Optional[List[str]] = None,
        time_filter: Optional[List[str]] = None,
        include_details: bool = False,
    ) -> pd.DataFrame:
        """Pivot the dataset on diagnostic categories."""
        cols = cls.get_cols(data, "categories")
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
                    col = "Diagnosis_ClinicianConsensus,DX_" + str(n)
                    if data.at[i, str(col) + "_Cat"] == c:
                        # set certainty
                        cert = cls.certainty(data, i, col)
                        # set time
                        if data.at[i, str(col) + "_Time"] == 1:
                            time = "Current"
                        elif data.at[i, str(col) + "_Time"] == 2:
                            time = "Past"
                        # set specific diagnosis, subcategory, code and past doc
                        d = data.at[i, str(col)]
                        code = data.at[i, str(col) + "_Code"]
                        sub = data.at[i, str(col) + "_Sub"]
                        if pd.isna(data.at[i, str(col) + "_Past_Doc"]):
                            past_doc = ""
                        else:
                            past_doc = str(int(data.at[i, str(col) + "_Past_Doc"]))
                        # create dictionary to store details on a diagnostic level
                        cat_dict = {
                            "diagnosis": d,
                            "subcategory": sub,
                            "code": code,
                            "certainty": cert,
                            "time": time,
                            "past_documentation": past_doc,
                        }
                        if certainty_filter is not None and time_filter is None:
                            if any([cert == x for x in certainty_filter]):
                                output = output.copy()
                                output.at[i, str(c_cleaned) + "_CategoryPresent"] = 1
                                # add diagnosis level details
                                cat_details.append(cat_dict)
                        elif time_filter is not None and certainty_filter is None:
                            if any([time == x for x in time_filter]):
                                output = output.copy()
                                output.at[i, str(c_cleaned) + "_CategoryPresent"] = 1
                                # add diagnosis level details
                                cat_details.append(cat_dict)
                        elif time_filter is not None and certainty_filter is not None:
                            if all(
                                [
                                    any([cert == x for x in certainty_filter]),
                                    any([time == x for x in time_filter]),
                                ]
                            ):
                                output = output.copy()
                                output.at[i, str(c_cleaned) + "_CategoryPresent"] = 1
                                # add diagnosis level details
                                cat_details.append(cat_dict)
                        elif time_filter is None and certainty_filter is None:
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
