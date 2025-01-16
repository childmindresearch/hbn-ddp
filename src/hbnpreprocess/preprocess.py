"""Pivots the clinician consensus diagnosis data."""

# import modules
import itertools
import typing

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class Diag_Preprocess:
    """Class for HBN data preprocessing."""

    def __init__(
        self: "Diag_Preprocess",
        hbn_data_path: str,
    ) -> None:
        """Initializes a class for HBN data preprocessing.

        Args:
            hbn_data_path (str): Path to the HBN data file.

        """
        self.input_path = hbn_data_path
        df = pd.read_csv(hbn_data_path, low_memory=False)

        dx_ns = ["0" + str(n) for n in range(1, 10)]
        dx_ns.append("10")

        # define columns
        cat_cols = ["Diagnosis_ClinicianConsensus,DX_" + n + "_Cat" for n in dx_ns]
        sub_cols = ["Diagnosis_ClinicianConsensus,DX_" + n + "_Sub" for n in dx_ns]
        dx_cols = ["Diagnosis_ClinicianConsensus,DX_" + n for n in dx_ns]

        self.dx_ns = dx_ns

        # replace blank subcategories with the category
        for sub, cat in zip(sub_cols, cat_cols):
            df[sub] = np.where(df[sub].isnull(), df[cat], df[sub])
        self.df = df
        # values to remove from diagnoses list
        remove = [
            "nan",
            "No Diagnosis Given",
            "No Diagnosis Given: Incomplete Eval",
            "",
            " ",
        ]
        # extract unique categories, subcategories, and diagnoses
        self.cats = [
            x for x in pd.unique(df[cat_cols].values.ravel("K")) if str(x) not in remove
        ]
        self.cats.sort()
        self.subs = [
            x for x in pd.unique(df[sub_cols].values.ravel("K")) if str(x) not in remove
        ]
        self.subs.sort()
        self.dxes = [
            x for x in pd.unique(df[dx_cols].values.ravel("K")) if str(x) not in remove
        ]
        self.dxes.sort()

        # create new DataFrame for results
        self.new_df = pd.DataFrame()
        # IDs and other columns that don't need to be pivoted
        unchanged_cols = [
            "Identifiers",
            "Diagnosis_ClinicianConsensus,NoDX",
            "Diagnosis_ClinicianConsensus,Season",
            "Diagnosis_ClinicianConsensus,Site",
            "Diagnosis_ClinicianConsensus,Year",
        ]
        for x in unchanged_cols:
            self.new_df[x] = df[x].copy()

    def certainty_filter(self: "Diag_Preprocess") -> None:
        """Interactively filters diagnoses by user-selected certainty and time."""
        cert_texts = [
            "confirmed diagnoses",
            "presumptive diagnoses",
            "diagnoses requiring confirmation",
            "rule-out diagnoses",
            "diagnoses by history",
            "diagnoses of unknown certainty",
        ]
        certs = ["Confirmed", "Presumptive", "RC", "RuleOut", "ByHx", "Unknown"]
        time_texts = ["current diagnoses", "past diagnoses"]
        times = ["Current", "Past"]
        self.cert_filter = []
        self.time_filter = []
        print(
            "The HBN dataset includes diagnoses of varying levels of certainty: "
            "confirmed, presumptive, requires confirmation, rule out, and by history)"
            ", as well as differing times of diagnosis or symptoms "
            "(current or past diagnoses)."
        )
        print("Would you like to filter the dataset by certainty level? (yes or no)")
        self.cert_filter_applied = False
        resp = input().lower()
        while resp != "yes" and resp != "no":
            print("Please enter yes or no")
            resp = input().lower()
        if resp == "yes":
            self.cert_filter_applied = True
            print(
                "First, please select which levels of diagnostic certainties should "
                "be included in the dataset."
            )
            included_certainties = []
            for t, c in zip(cert_texts, certs):
                include = ""
                print("Include " + str(t) + "? (yes or no)")
                include = input().lower()
                while include != "yes" and include != "no":
                    print("Please enter yes or no")
                    include = input("yes or no").lower()
                if include == "yes":
                    self.cert_filter.append(c)
                    included_certainties.append(t)
            print(
                "Dataset will include "
                + str(included_certainties)
                .replace("[", "")
                .replace("]", "")
                .replace("'", "")
                + ". Other diagnoses will be excluded."
            )
        else:
            print(
                "No certainty filter applied. "
                "Diagnoses of all certainty levels will be left in the dataset."
            )

        print("Would you like to filter the dataset by time of diagnosis? (yes or no)")
        self.time_filter_applied = False
        resp = input().lower()
        while resp != "yes" and resp != "no":
            print("Please enter yes or no")
            resp = input().lower()
        if resp == "yes":
            self.time_filter_applied = True
            print(
                "First, please select which levels of diagnostic certainties "
                "should be included in the dataset."
            )
            included_times = []
            for t, c in zip(time_texts, times):
                include = ""
                print("Include " + str(t) + "? (yes or no)")
                include = input().lower()
                while include != "yes" and include != "no":
                    print("Please enter yes or no")
                    include = input("yes or no").lower()
                if include == "yes":
                    self.time_filter.append(c)
                    included_times.append(t)
            print(
                "Dataset will include "
                + str(included_times).replace("[", "").replace("]", "").replace("'", "")
                + ". Other diagnoses will be excluded."
            )

    def certainty(self: "Diag_Preprocess", i: int, col: str) -> str:
        """Set the certainty of the diagnosis or category."""
        if all(
            [
                self.df.at[i, str(col) + "_Confirmed"] != 1,
                self.df.at[i, str(col) + "_Presum"] != 1,
                self.df.at[i, str(col) + "_RC"] != 1,
                self.df.at[i, str(col) + "_RuleOut"] != 1,
                self.df.at[i, str(col) + "_ByHx"] == 1,
            ]
        ):
            cert = "ByHx"
        elif all(
            [
                self.df.at[i, str(col) + "_Confirmed"] == 1,
                self.df.at[i, str(col) + "_Presum"] != 1,
                self.df.at[i, str(col) + "_RC"] != 1,
                self.df.at[i, str(col) + "_RuleOut"] != 1,
                self.df.at[i, str(col) + "_ByHx"] != 1,
            ]
        ):
            cert = "Confirmed"
        elif all(
            [
                self.df.at[i, str(col) + "_Confirmed"] != 1,
                self.df.at[i, str(col) + "_Presum"] == 1,
                self.df.at[i, str(col) + "_RC"] != 1,
                self.df.at[i, str(col) + "_RuleOut"] != 1,
                self.df.at[i, str(col) + "_ByHx"] != 1,
            ]
        ):
            cert = "Presumptive"
        elif all(
            [
                self.df.at[i, str(col) + "_Confirmed"] != 1,
                self.df.at[i, str(col) + "_Presum"] != 1,
                self.df.at[i, str(col) + "_RC"] == 1,
                self.df.at[i, str(col) + "_RuleOut"] != 1,
                self.df.at[i, str(col) + "_ByHx"] != 1,
            ]
        ):
            cert = "RC"
        elif all(
            [
                self.df.at[i, str(col) + "_Confirmed"] != 1,
                self.df.at[i, str(col) + "_Presum"] != 1,
                self.df.at[i, str(col) + "_RC"] != 1,
                self.df.at[i, str(col) + "_RuleOut"] == 1,
                self.df.at[i, str(col) + "_ByHx"] != 1,
            ]
        ):
            cert = "RuleOut"
        # if certainties are 0 and time = 2, assign 'N/A' these are past diagnoses
        # noted in Past_Doc
        elif all(
            [
                self.df.at[i, str(col) + "_Time"] == 2,
                self.df.at[i, str(col) + "_Confirmed"] == 0,
                self.df.at[i, str(col) + "_Presum"] == 0,
                self.df.at[i, str(col) + "_RC"] == 0,
                self.df.at[i, str(col) + "_RuleOut"] == 0,
                self.df.at[i, str(col) + "_ByHx"] != 1,
            ]
        ):
            cert = "N/A"
        # if all missing, or conflicting certainties are present,assign 'Unknown'
        else:
            cert = "Unknown"
        return cert

    def diagnoses(self: "Diag_Preprocess") -> None:
        """Pivot the dataset on diagnoses."""
        repeated_vars = ["_Cat", "_Sub", "_Spec", "_Code", "_Past_Doc"]
        print("Diagnoses in dataset:")
        for d in self.dxes:
            print(d)
            d_cleaned = (
                d.strip()
                .replace(" ", "_")
                .replace(":", "")
                .replace("-", "")
                .replace("/", "")
                .replace("(", "")
                .replace(")", "")
                .replace(",", "")
                .replace(" ", "")
                .replace("__", "")
            )
            # create new columns
            self.new_df = self.new_df.copy()
            self.new_df[str(d_cleaned) + "_DiagnosisPresent"] = 0
            self.new_df = self.new_df.copy()
            self.new_df[str(d_cleaned) + "_Certainty"] = ""
            self.new_df = self.new_df.copy()
            self.new_df[str(d_cleaned) + "_Time"] = ""
            for var in repeated_vars:
                self.new_df = self.new_df.copy()
                self.new_df[str(d_cleaned) + str(var)] = ""
            # iterate through each participant and diagnosis
            for i, n in itertools.product(range(0, len(self.df)), self.dx_ns):
                col = "Diagnosis_ClinicianConsensus,DX_" + str(n)
                # locate presence of specific diagnosis
                if self.df.at[i, str(col)] == d:
                    # set certainty
                    cert = self.certainty(i, col)
                    # set time
                    if self.df.at[i, str(col) + "_Time"] == 1:
                        time = "Current"
                    elif self.df.at[i, str(col) + "_Time"] == 2:
                        time = "Past"
                    # apply certainty filter if selected and set presence of diagnosis
                    if self.cert_filter_applied and not self.time_filter_applied:
                        if any([cert == x for x in self.cert_filter]):
                            self.new_df = self.new_df.copy()
                            self.new_df.at[i, str(d_cleaned) + "_DiagnosisPresent"] = 1
                            # variables repeated by diagnosis
                            for var in repeated_vars:
                                self.new_df = self.new_df.copy()
                                self.new_df.at[i, str(d_cleaned) + str(var)] = (
                                    self.df.at[i, str(col) + str(var)]
                                )
                            # add certainty to DataFrame
                            self.new_df = self.new_df.copy()
                            self.new_df.at[i, str(d_cleaned) + "_Certainty"] = cert
                            # add time to DataFrame
                            self.new_df = self.new_df.copy()
                            self.new_df.at[i, str(d_cleaned) + "_Time"] = time
                    elif self.time_filter_applied and not self.cert_filter_applied:
                        if any([time == x for x in self.time_filter]):
                            self.new_df = self.new_df.copy()
                            self.new_df.at[i, str(d_cleaned) + "_DiagnosisPresent"] = 1
                            # variables repeated by diagnosis
                            for var in repeated_vars:
                                self.new_df = self.new_df.copy()
                                self.new_df.at[i, str(d_cleaned) + str(var)] = (
                                    self.df.at[i, str(col) + str(var)]
                                )
                            # add certainty to DataFrame
                            self.new_df = self.new_df.copy()
                            self.new_df.at[i, str(d_cleaned) + "_Certainty"] = cert
                            # add time to DataFrame
                            self.new_df = self.new_df.copy()
                            self.new_df.at[i, str(d_cleaned) + "_Time"] = time
                    elif self.time_filter_applied and self.cert_filter_applied:
                        if all(
                            [
                                any([cert == x for x in self.cert_filter]),
                                any([time == x for x in self.time_filter]),
                            ]
                        ):
                            self.new_df = self.new_df.copy()
                            self.new_df.at[i, str(d_cleaned) + "_DiagnosisPresent"] = 1
                            # variables repeated by diagnosis
                            for var in repeated_vars:
                                self.new_df = self.new_df.copy()
                                self.new_df.at[i, str(d_cleaned) + str(var)] = (
                                    self.df.at[i, str(col) + str(var)]
                                )
                            # add certainty to DataFrame
                            self.new_df = self.new_df.copy()
                            self.new_df.at[i, str(d_cleaned) + "_Certainty"] = cert
                            # add time to DataFrame
                            self.new_df = self.new_df.copy()
                            self.new_df.at[i, str(d_cleaned) + "_Time"] = time
                    # no certainty filter set
                    else:
                        self.new_df = self.new_df.copy()
                        self.new_df.at[i, str(d_cleaned) + "_DiagnosisPresent"] = 1
                        # variables repeated by diagnosis
                        for var in repeated_vars:
                            self.new_df = self.new_df.copy()
                            self.new_df.at[i, str(d_cleaned) + str(var)] = self.df.at[
                                i, str(col) + str(var)
                            ]
                        # add certainty to DataFrame
                        self.new_df = self.new_df.copy()
                        self.new_df.at[i, str(d_cleaned) + "_Certainty"] = cert
                        # add time to DataFrame
                        self.new_df = self.new_df.copy()
                        self.new_df.at[i, str(d_cleaned) + "_Time"] = time

    def subcategories(self: "Diag_Preprocess", include_details: bool = True) -> None:
        """Pivot the dataset on diagnostic subcategories."""
        print("Diagnostic subcategories in dataset:")
        for s in self.subs:
            print(s)
            s_cleaned = (
                s.strip()
                .replace(" ", "")
                .replace(":", "")
                .replace("-", "")
                .replace("/", "")
                .replace("(", "")
                .replace(")", "")
                .replace(",", "")
                .replace(" ", "")
                .replace("__", "")
            )
            # column for the presence of subcategories
            self.new_df[str(s_cleaned) + "_SubcategoryPresent"] = 0
            if include_details:
                # column for higher level category
                self.new_df = self.new_df.copy()
                self.new_df[str(s_cleaned) + "_Category"] = ""
                # column for diagnostic level details
                self.new_df = self.new_df.copy()
                self.new_df[str(s_cleaned) + "_Details"] = ""

            for i in range(0, len(self.df)):
                sub_details = []
                for n in self.dx_ns:
                    col = "Diagnosis_ClinicianConsensus,DX_" + str(n)
                    if self.df.at[i, str(col) + "_Sub"] == s:
                        # set certainty
                        cert = self.certainty(i, col)
                        # set time
                        if self.df.at[i, str(col) + "_Time"] == 1:
                            time = "Current"
                        elif self.df.at[i, str(col) + "_Time"] == 2:
                            time = "Past"
                        # set specific diagnosis, code and past documentation
                        d = self.df.at[i, str(col)]
                        code = self.df.at[i, str(col) + "_Code"]
                        if pd.isna(self.df.at[i, str(col) + "_Past_Doc"]):
                            past_doc = ""
                        else:
                            past_doc = str(int(self.df.at[i, str(col) + "_Past_Doc"]))
                        # create dictionary to store details on a diagnostic level
                        sub_dict = {
                            "diagnosis": d,
                            "code": code,
                            "certainty": cert,
                            "time": time,
                            "past_documentation": past_doc,
                        }
                        if self.cert_filter_applied and not self.time_filter_applied:
                            if any([cert == x for x in self.cert_filter]):
                                self.new_df = self.new_df.copy()
                                self.new_df.at[
                                    i, str(s_cleaned) + "_SubcategoryPresent"
                                ] = 1
                                # add diagnosis level details
                                sub_details.append(sub_dict)
                                # add higher level category
                                if include_details:
                                    self.new_df = self.new_df.copy()
                                    self.new_df.at[i, str(s_cleaned) + "_Cat"] = (
                                        self.df.at[
                                            i,
                                            "Diagnosis_ClinicianConsensus,DX_"
                                            + str(n)
                                            + "_Cat",
                                        ]
                                    )
                        elif self.time_filter_applied and not self.cert_filter_applied:
                            if any([time == x for x in self.time_filter]):
                                self.new_df = self.new_df.copy()
                                self.new_df.at[
                                    i, str(s_cleaned) + "_SubcategoryPresent"
                                ] = 1
                                # add diagnosis level details
                                sub_details.append(sub_dict)
                                # add higher level category
                                if include_details:
                                    self.new_df = self.new_df.copy()
                                    self.new_df.at[i, str(s_cleaned) + "_Cat"] = (
                                        self.df.at[
                                            i,
                                            "Diagnosis_ClinicianConsensus,DX_"
                                            + str(n)
                                            + "_Cat",
                                        ]
                                    )
                        elif self.time_filter_applied and self.cert_filter_applied:
                            if all(
                                [
                                    any([cert == x for x in self.cert_filter]),
                                    any([time == x for x in self.time_filter]),
                                ]
                            ):
                                self.new_df = self.new_df.copy()
                                self.new_df.at[
                                    i, str(s_cleaned) + "_SubcategoryPresent"
                                ] = 1
                                # add diagnosis level details
                                sub_details.append(sub_dict)
                                # add higher level category
                                if include_details:
                                    self.new_df = self.new_df.copy()
                                    self.new_df.at[i, str(s_cleaned) + "_Cat"] = (
                                        self.df.at[
                                            i,
                                            "Diagnosis_ClinicianConsensus,DX_"
                                            + str(n)
                                            + "_Cat",
                                        ]
                                    )
                        else:
                            self.new_df = self.new_df.copy()
                            self.new_df.at[
                                i, str(s_cleaned) + "_SubcategoryPresent"
                            ] = 1
                            # add diagnosis level details
                            sub_details.append(sub_dict)
                            # add higher level category
                            if include_details:
                                self.new_df = self.new_df.copy()
                                self.new_df.at[i, str(s_cleaned) + "_Category"] = (
                                    self.df.at[
                                        i,
                                        "Diagnosis_ClinicianConsensus,DX_"
                                        + str(n)
                                        + "_Cat",
                                    ]
                                )
                # add subcategory details to DataFrame
                if all([len(sub_details) > 0, include_details]):
                    self.new_df = self.new_df.copy()
                    self.new_df.at[i, str(s_cleaned) + "_Details"] = str(
                        sub_details
                    ).strip("[]")

    def categories(self: "Diag_Preprocess", include_details: bool = True) -> None:
        """Pivot the data on diagnostic categories."""
        print("Diagnostic subcategories in dataset:")
        for c in self.cats:
            print(c)
            c_cleaned = (
                c.strip()
                .replace(" ", "")
                .replace(":", "")
                .replace("-", "")
                .replace("/", "")
                .replace("(", "")
                .replace(")", "")
                .replace(",", "")
                .replace(" ", "")
                .replace("__", "")
            )
            # column for the presence of categories
            self.new_df[str(c_cleaned) + "_CategoryPresent"] = 0
            if include_details:
                # column for diagnostic level details
                self.new_df[str(c_cleaned) + "_Details"] = ""
            for i in range(0, len(self.df)):
                cat_details = []
                for n in self.dx_ns:
                    col = "Diagnosis_ClinicianConsensus,DX_" + str(n)
                    if self.df.at[i, str(col) + "_Cat"] == c:
                        # set certainty
                        cert = self.certainty(i, col)
                        # set time
                        if self.df.at[i, str(col) + "_Time"] == 1:
                            time = "Current"
                        elif self.df.at[i, str(col) + "_Time"] == 2:
                            time = "Past"
                        # set specific diagnosis, subcategory, code and past doc
                        d = self.df.at[i, str(col)]
                        code = self.df.at[i, str(col) + "_Code"]
                        sub = self.df.at[i, str(col) + "_Sub"]
                        if pd.isna(self.df.at[i, str(col) + "_Past_Doc"]):
                            past_doc = ""
                        else:
                            past_doc = str(int(self.df.at[i, str(col) + "_Past_Doc"]))
                        # create dictionary to store details on a diagnostic level
                        cat_dict = {
                            "diagnosis": d,
                            "subcategory": sub,
                            "code": code,
                            "certainty": cert,
                            "time": time,
                            "past_documentation": past_doc,
                        }
                        if self.cert_filter_applied and not self.time_filter_applied:
                            if any([cert == x for x in self.cert_filter]):
                                self.new_df = self.new_df.copy()
                                self.new_df.at[
                                    i, str(c_cleaned) + "_CategoryPresent"
                                ] = 1
                                # add diagnosis level details
                                cat_details.append(cat_dict)
                        elif self.time_filter_applied and not self.cert_filter_applied:
                            if any([time == x for x in self.time_filter]):
                                self.new_df = self.new_df.copy()
                                self.new_df.at[
                                    i, str(c_cleaned) + "_CategoryPresent"
                                ] = 1
                                # add diagnosis level details
                                cat_details.append(cat_dict)
                        elif self.time_filter_applied and self.cert_filter_applied:
                            if all(
                                [
                                    any([cert == x for x in self.cert_filter]),
                                    any([time == x for x in self.time_filter]),
                                ]
                            ):
                                self.new_df = self.new_df.copy()
                                self.new_df.at[
                                    i, str(c_cleaned) + "_CategoryPresent"
                                ] = 1
                                # add diagnosis level details
                                cat_details.append(cat_dict)
                        else:
                            self.new_df = self.new_df.copy()
                            self.new_df.at[i, str(c_cleaned) + "_CategoryPresent"] = 1
                            # add diagnosis level details
                            cat_details.append(cat_dict)
                # add category details to DataFrame
                if all([len(cat_details) > 0, include_details]):
                    self.new_df = self.new_df.copy()
                    self.new_df.at[i, str(c_cleaned) + "_Details"] = str(
                        cat_details
                    ).strip("[]")

    def visualize(self: "Diag_Preprocess", by: str) -> None:
        """Visualizes the data by diagnoses, subcategories, or categories.

        Args:
            by (str): The type of data to visualize.

        """
        # diagnosis plot
        if by == "all" or by == "diagnoses":
            # filter columns
            filtered_columns = [
                col for col in self.new_df.columns if "DiagnosisPresent" in col
            ]
            filtered_df = self.new_df[filtered_columns]
            sums = filtered_df.sum().sort_values(ascending=False)
            new_labels = [
                label.replace("_DiagnosisPresent", "") for label in sums.index
            ]
            # plot
            sums.plot(kind="bar", color="blue")
            plt.xlabel("Diagnosis Present")
            plt.ylabel("# Participants")
            plt.xticks(
                ticks=range(len(new_labels)),
                labels=new_labels,
                rotation=45,
                ha="right",
                fontsize=8,
            )
            plt.subplots_adjust(bottom=0.25)  # Adjust bottom padding as needed
            plt.show()
        # category plot
        if by == "all" or by == "categories":
            # filter columns
            filtered_columns = [
                col for col in self.new_df.columns if "CategoryPresent" in col
            ]
            filtered_df = self.new_df[filtered_columns]
            sums = filtered_df.sum().sort_values(ascending=False)
            new_labels = [label.replace("_CategoryPresent", "") for label in sums.index]
            # plot
            sums.plot(kind="bar", color="blue")
            plt.xlabel("Category Present")
            plt.ylabel("# Participants")
            plt.xticks(
                ticks=range(len(new_labels)),
                labels=new_labels,
                rotation=45,
                ha="right",
                fontsize=8,
            )
            plt.subplots_adjust(bottom=0.25)  # Adjust bottom padding as needed
            plt.show()
        # subcategory plot
        if by == "all" or by == "subcategories":
            # filter columns
            filtered_columns = [
                col for col in self.new_df.columns if "SubcategoryPresent" in col
            ]
            filtered_df = self.new_df[filtered_columns]
            sums = filtered_df.sum().sort_values(ascending=False)
            new_labels = [
                label.replace("_SubcategoryPresent", "") for label in sums.index
            ]
            # plot
            sums.plot(kind="bar", color="blue")
            plt.xlabel("Subcategory Present")
            plt.ylabel("# Participants")
            plt.xticks(
                ticks=range(len(new_labels)),
                labels=new_labels,
                rotation=45,
                ha="right",
                fontsize=8,
            )
            plt.subplots_adjust(bottom=0.25)  # Adjust bottom padding as needed
            plt.show()

    def pivot(
        self: "Diag_Preprocess",
        output_path: str,
        interactive: bool = True,
        pivot_by: str = "all",
        cert_filter: typing.Optional[list] = None,
        time_filter: typing.Optional[list] = None,
        include_details: bool = True,
        viz: bool = True,
    ) -> pd.DataFrame:
        """Runs the preprocessing of clinician consensus diagnostic data.

        Args:
            interactive (bool): Whether to interactively filter the data rather than
            setting parameters. Default is True.
            output_path (str): The path to save the data.
            pivot_by (str): The level of data to pivot on. Options are "diagnoses",
            "subcategories", "categories", or "all". Default is "all".
            cert_filter (list): If interactive filtering is not used, a list of
            diagnostic certainties to include in the data. Options are "Confirmed",
            "Presumptive", "RC", "RuleOut", "ByHx", and "Unknown". Default is None,
            which will not apply a filter.
            time_filter (list): If interactive filtering is not used, a list of
            diagnostic times to include in the data. Options are "Current" and "Past".
            Default is None, which will not apply a filter.
            include_details (bool): Whether to include details of each specific
            diagnosis when pivoting on higher level subcategories or categories. Default
            is True.
            viz (bool): Whether to visualize the data by plotting counts of each
            diagnosis or category. Default is True.

        Returns:
            DataFrame: The preprocessed data.
        """
        if interactive:
            print(
                "Would you like to pivot the data by diagnoses, subcategories,",
                "categories, or all?",
            )
            pivot_by = input().lower()
            while pivot_by not in ["diagnoses", "subcategories", "categories", "all"]:
                print("Please enter diagnoses, subcategories, categories, or all.")
                pivot_by = input().lower()
            print("Pivoting the data by " + pivot_by + ".")
            self.certainty_filter()
        else:
            if cert_filter is None:
                self.cert_filter_applied = False
            else:
                self.cert_filter_applied = True
                self.cert_filter = cert_filter
            if time_filter is None:
                self.time_filter_applied = False
            else:
                self.time_filter_applied = True
                self.time_filter = time_filter

            # set cert and time filters to values passed
        # pivot data
        print("Pivoting data...")
        if pivot_by == "diagnoses":
            self.diagnoses()
        if pivot_by == "subcategories":
            self.subcategories(include_details=include_details)
        if pivot_by == "categories":
            self.categories(include_details=include_details)
        if pivot_by == "all":
            self.diagnoses()
            print("Diagnoses complete. Moving to subcategories...")
            self.subcategories(include_details=False)
            print("Subcategories complete. Moving to categories...")
            self.categories(include_details=False)
        print("Preprocessing complete.")

        # save data
        self.new_df.to_csv(output_path, index=False)
        print("Data saved to " + output_path)

        # plot data if specified
        if interactive:
            print("Would you like to visualize the data? (yes or no)")
            viz_input = input().lower()
            while viz_input != "yes" and viz_input != "no":
                print("Please enter yes or no")
                viz_input = input().lower()
            if viz_input == "no":
                viz = False
        if viz:
            self.visualize(by=pivot_by)

        return self.new_df
