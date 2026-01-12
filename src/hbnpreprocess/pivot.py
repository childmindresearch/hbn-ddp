"""Pivoting for HBN data."""

import itertools
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd


@dataclass
class DxInfo:
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

    DX_NS = [f"{n:02d}" for n in range(1, 11)]
    DX_COLUMN_SUFFIXES = [
        "ByHx",
        "Cat",
        "Code",
        "Confirmed",
        "Past_Doc",
        "Presum",
        "RC",
        "RuleOut",
        "Spec",
        "Sub",
        "Time",
    ]

    @classmethod
    def _dx_column_names_by_type(cls) -> list[str]:
        """Get the column names for the diagnosis columns."""
        return {
            suffix: [f"Diagnosis_ClinicianConsensus,DX_{n}_{suffix}" for n in cls.DX_NS]
            for suffix in cls.DX_COLUMN_SUFFIXES
        } + {"DX": [f"Diagnosis_ClinicianConsensus,DX_{n}" for n in cls.DX_NS]}

    DX_COLS = ["Diagnosis_ClinicianConsensus,DX_" + n for n in DX_NS]
    DX_SUPPLEMENTAL_COLS = [
        "Diagnosis_ClinicianConsensus,DX_" + n + "_" + suffix
        for suffix in DX_COLUMN_SUFFIXES
        for n in DX_NS
    ]
    # x = {
    #     col_type: [f"Diagnosis_ClinicianConsensus,DX_{n}_{col_type}" for n in DX_NS]
    #     for col_type in DX_COLUMN_SUFFIXES
    # }
    DX_CAT_COLS = [base + "_Cat" for base in DX_COLS]
    DX_SUB_COLS = [base + "_Sub" for base in DX_COLS]
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
    def _qualifier_series(data: pd.DataFrame, col_prefix: str) -> pd.Series:
        """Get the qualifier for a diagnosis."""
        suffixes = ("Confirmed", "Presum", "RC", "RuleOut", "ByHx", "Time")
        confirmed_col, presum_col, rc_col, ruleout_col, byhx_col, time_col = (
            col_prefix + "_" + suffix for suffix in suffixes
        )
        byhx = (
            (data.loc[:, confirmed_col] != 1)
            & (data.loc[:, presum_col] != 1)
            & (data.loc[:, rc_col] != 1)
            & (data.loc[:, ruleout_col] != 1)
            & (data.loc[:, byhx_col] == 1)
            & (data.loc[:, time_col] == 1)
        )
        confirmed = (
            (data.loc[:, confirmed_col] == 1)
            & (data.loc[:, presum_col] != 1)
            & (data.loc[:, rc_col] != 1)
            & (data.loc[:, ruleout_col] != 1)
            & (data.loc[:, byhx_col] != 1)
            & (data.loc[:, time_col] == 1)
        )
        presum = (
            (data.loc[:, confirmed_col] != 1)
            & (data.loc[:, presum_col] == 1)
            & (data.loc[:, rc_col] != 1)
            & (data.loc[:, ruleout_col] != 1)
            & (data.loc[:, byhx_col] != 1)
            & (data.loc[:, time_col] == 1)
        )
        rc = (
            (data.loc[:, confirmed_col] != 1)
            & (data.loc[:, presum_col] != 1)
            & (data.loc[:, rc_col] == 1)
            & (data.loc[:, ruleout_col] != 1)
            & (data.loc[:, byhx_col] != 1)
            & (data.loc[:, time_col] == 1)
        )
        ruleout = (
            (data.loc[:, confirmed_col] != 1)
            & (data.loc[:, presum_col] != 1)
            & (data.loc[:, rc_col] != 1)
            & (data.loc[:, ruleout_col] == 1)
            & (data.loc[:, byhx_col] != 1)
            & (data.loc[:, time_col] == 1)
        )
        past = (
            (data.loc[:, confirmed_col] != 1)
            & (data.loc[:, presum_col] != 1)
            & (data.loc[:, rc_col] != 1)
            & (data.loc[:, ruleout_col] != 1)
            & (data.loc[:, byhx_col] != 1)
            & (data.loc[:, time_col] == 2)
        )

        data.assign(qualifier="ByHx").assign(
            qualifier=data.qualifier.where(byhx, "Confirmed")
            .where(confirmed, "Presumptive")
            .where(presum, "RC")
            .where(rc, "RuleOut")
            .where(ruleout, "Past")
            .where(past, "Unknown")
        )
        return data.qualifier

    @classmethod
    def _get_diagnosis_details(cls, data: pd.DataFrame, i: int, n: str) -> DxInfo:
        col = f"Diagnosis_ClinicianConsensus,DX_{n}"
        return DxInfo(
            diagnosis=data.at[i, col],
            sub=data.at[i, col + "_Sub"],
            cat=data.at[i, col + "_Cat"],
            code=data.at[i, col + "_Code"],
            past_doc=data.at[i, col + "_Past_Doc"],
            qual=cls._set_qualifier(data, i, col),
            time=data.at[i, col + "_Time"],
        )

    @classmethod
    def _filter_pass(cls, qual: str, qualifier_filter: list[str] | None) -> bool:
        """Apply the filter."""
        return qualifier_filter is None or qual in qualifier_filter

    @classmethod
    def diagnoses(
        cls,
        data: pd.DataFrame,
        output: pd.DataFrame,
        qualifier_filter: list[str] | None = None,
    ) -> pd.DataFrame:
        """Pivot the data by diagnoses."""
        repeated_vars = ["_Cat", "_Sub", "_Spec", "_Code", "_Past_Doc"]
        dx_values = cls._get_values(data, "diagnoses")
        print("Diagnoses in dataset:")
        for dx_val in dx_values:
            # TODO: Try concatenating all new values at once for performance
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
                    if cls._filter_pass(details.qual, qualifier_filter):
                        output.at[i, f"{dx_val}_DiagnosisPresent"] = 1
                        # variables repeated by diagnosis
                        for var in repeated_vars:
                            output.at[i, dx_val + var] = data.at[i, col + var]
                        # add qualifier
                        output.at[i, f"{dx_val}_Qualifier"] = details.qual
        return output

    @classmethod
    def subcategories(
        cls,
        data: pd.DataFrame,
        output: pd.DataFrame,
        qualifier_filter: list[str] | None = None,
        include_details: bool = False,
    ) -> pd.DataFrame:
        """Pivot the dataset on diagnostic subcategories."""
        dx_values = cls._get_values(data, "subcategories")
        print("Diagnostic subcategories in dataset:")
        for dx_val in dx_values:
            output[dx_val + "_SubcategoryPresent"] = 0
            if include_details:
                # column for diagnostic level details
                output[dx_val + "_Details"] = ""
            for i in range(0, len(data)):
                cat_details = []
                for n in cls.DX_NS:
                    details = cls._get_diagnosis_details(data, i, n)
                    if cls._clean_dx_value(details.sub) == dx_val:
                        # apply filter if selected
                        if cls._filter_pass(details.qual, qualifier_filter):
                            # set presence of subcategory
                            output.at[i, dx_val + "_SubcategoryPresent"] = 1
                            # create dictionary to store details on a diagnostic level
                            cat_dict = {
                                "diagnosis": details.diagnosis,
                                "code": details.code,
                                "qualifier": details.qual,
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
        qualifier_filter: list[str] | None = None,
        include_details: bool = False,
    ) -> pd.DataFrame:
        """Pivot the dataset on diagnostic categories."""
        # TODO: Gen column of cleaned values for categories
        # Get unique values
        # Set _CatPresent to 0 for all
        # Set _Details to "" for all if include_details
        # Replace loop with matrix op using where or bool mask
        # Set details using column concatenation
        data.loc[:, cls.DX_CAT_COLS] = (
            data.loc[:, cls.DX_CAT_COLS].fillna("").astype(str)
        )
        data.loc[:, cls.DX_CAT_COLS] = data.loc[:, cls.DX_CAT_COLS].apply(
            lambda c: c.str.replace("\W", "", regex=True), axis=1
        )
        dx_values = (
            data.loc[:, cls.DX_CAT_COLS].melt()["value"].drop_duplicates().to_list()
        )
        pd.lreshape(
            data,
            groups={
                "Diagnosis_ClinicianConsensus,DX": cls.DX_COLS,
                "Diagnosis_ClinicianConsensus,DX_Cat": cls.DX_CAT_COLS,
                "Diagnosis_ClinicianConsensus,DX_Sub": cls.DX_SUB_COLS,
            },
        )
        columns = [
            "Diagnosis_ClinicianConsensus,DX_01",
            "Diagnosis_ClinicianConsensus,DX_01_ByHx",
            "Diagnosis_ClinicianConsensus,DX_01_Cat",
            "Diagnosis_ClinicianConsensus,DX_01_Code",
            "Diagnosis_ClinicianConsensus,DX_01_Confirmed",
            "Diagnosis_ClinicianConsensus,DX_01_Past_Doc",
            "Diagnosis_ClinicianConsensus,DX_01_Presum",
            "Diagnosis_ClinicianConsensus,DX_01_RC",
            "Diagnosis_ClinicianConsensus,DX_01_RuleOut",
            "Diagnosis_ClinicianConsensus,DX_01_Spec",
            "Diagnosis_ClinicianConsensus,DX_01_Sub",
            "Diagnosis_ClinicianConsensus,DX_01_Time",
        ]

        # data.loc[:, [f"DX_Qualifier_{n}" for n in cls.DX_NS]] = (
        #     True
        #     if qualifier_filter is None
        #     else data.loc[:, cls.DX_CAT_COLS].apply(
        #         lambda c: cls._qualifier_map, axis=1
        #     )
        # )
        # for col in cls.DX_CAT_COLS:
        #     data.loc[:, f"{col}_Qual"] = cls._qualifier_series(data, col)
        # # TODO integrate qualifier filter
        # for dx_val in dx_values:
        #     data.loc[:, dx_val + "_CategoryPresent"] = (
        #         data.loc[:, cls.DX_CAT_COLS]
        #         .apply(lambda c: c.str.contains(dx_val, na=False, regex=False))
        #         .apply(lambda c: c.any(), axis=1)
        #         .astype(int)
        #     )
        if include_details:
            # column for diagnostic level details
            data.loc[:, [dx + "_Details" for dx in dx_values]] = ""
        dx_values = cls._get_values(data, "categories")
        print("Diagnostic categories in dataset:")
        for dx_val in dx_values:
            # column for the presence of categories
            output[dx_val + "_CategoryPresent"] = 0
            if include_details:
                # column for diagnostic level details
                output[dx_val + "_Details"] = ""
            for i in range(0, len(data)):
                cat_details = []
                for n in cls.DX_NS:
                    details = cls._get_diagnosis_details(data, i, n)
                    if cls._clean_dx_value(details.cat) == dx_val:
                        # apply filter if selected
                        if cls._filter_pass(details.qual, qualifier_filter):
                            # set presence of category
                            output.at[i, dx_val + "_CategoryPresent"] = 1
                            # create dictionary to store details on a diagnostic level
                            cat_dict = {
                                "diagnosis": details.diagnosis,
                                "subcategory": details.sub,
                                "code": details.code,
                                "qualifier": details,
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
