"""Script to fix ClinicianConsensusDiagnosis Data."""

import pandas as pd


def data_clean(hbn_data_path: str) -> None:
    """Fixes error and missing values in the diagnostic data and saves as csv.

    This function fixes known inconsistencies or errors in the HBN Clinician Consensus
    Diagnosis Data. First, repeated diagnoses are removed. The rest of the fixes are
    related to diagnosis certainty. As the data entry template for this dataset has
    changed over time, participants may be missing values for columns that were not
    present at the time of data entry. The changes to the certainty columns include:
        - When one of confirmed, presumptive, or requires confirmation are 1, if by
        history is missing, it should be set to 0.
        - When confirmed and presumptive are missing, if requires confirmation, rule
        out, and by history are all 0, confirmed should be 1 and presumptive 0. These
        are confirmed diagnoses from an old template version with no explicit
        "confirmed" option.
        - When confirmed and presumptive are missing, if one of requires confirmation,
        rule out, or by history are 1, confirmed and presumptive should both be 0.
        - If a diagnoses is by history, the time variable should be blank.
        - Past Documentation should only be noted for diagnoses by history or past
        diagnoses. Otherwise, this variable should be blank.
        - The "New", "PRem", and "Rem" columns are from an outdated template version and
        should be removed. This information is available elsewhere.



    Args:
        hbn_data_path (str): The path to the HBN data file.

    Returns:
        None
    """
    # load data
    df = pd.read_csv(hbn_data_path, low_memory=False)

    #
    df["Identifiers"] = df["Identifiers"].str.split(",").str[0]

    # remove known duplicate diagnoses/ whitespace
    df = df.replace(
        "Specific Learning Disorder with Impairment in Mathematics ",
        "Specific Learning Disorder with Impairment in Mathematics",
    )
    df = df.replace(
        "Specific Learning Disorder with Impairment in Reading ",
        "Specific Learning Disorder with Impairment in Reading",
    )
    df = df.replace("Obsessive-Compulsive Disorder ", "Obsessive-Compulsive Disorder")
    df = df.replace(
        "Neurobehavioral Disorder Associated with Prenatal Alcohol Exposure"
        " (ND-PAE) ",
        "Neurobehavioral Disorder Associated with "
        "Prenatal Alcohol Exposure (ND-PAE)",
    )

    remove = [
        "nan",
        "No Diagnosis Given",
        "No Diagnosis Given: Incomplete Eval",
        "",
        " ",
    ]

    dx_ns = ["0" + str(n) for n in range(1, 10)]
    dx_ns.append("10")
    dx_cols = ["Diagnosis_ClinicianConsensus,DX_" + n for n in dx_ns]
    dxes = [x for x in pd.unique(df[dx_cols].values.ravel("K")) if str(x) not in remove]
    dxes.sort()

    # types of corrections for summary
    missing_ByHx = 0
    missing_confirmed = 0
    missing_confirmed_sb_confirmed = 0
    missing_confirmed_not_confirmed = 0
    remove_time = 0
    remove_past_doc = 0

    # correct errors in certainty data
    for n in dx_ns:
        for i in range(0, len(df)):
            # if any of confirmed, presum, or RC are 1, if ByHx is NULL,
            # by history should be 0
            if any(
                [
                    df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_Confirmed"]
                    == 1,
                    df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_Presum"] == 1,
                    df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_RC"] == 1,
                    df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_RuleOut"] == 1,
                ]
            ):
                if pd.isna(df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_ByHx"]):
                    df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_ByHx"] = 0
                    missing_ByHx += 1
            # if confirmed and presum are NULL, and RC, Rule-Out and ByHx are 0,
            # confirmed should be 1
            if all(
                [
                    pd.isna(
                        df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_Confirmed"]
                    ),
                    pd.isna(
                        df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_Presum"]
                    ),
                    df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_RC"] == 0,
                    df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_RuleOut"] == 0,
                    df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_ByHx"] == 0,
                ]
            ):
                df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_Confirmed"] = 1
                df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_Presum"] = 0
                missing_confirmed += 1
                missing_confirmed_sb_confirmed += 1
            # if confirmed and presum are NULL, and one of RC, RuleOut or ByHx are 1,
            # confirmed and presum should be 0
            if pd.isna(
                df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_Confirmed"]
            ) and pd.isna(df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_Presum"]):
                if any(
                    [
                        df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_RC"] == 1,
                        df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_RuleOut"]
                        == 1,
                        df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_ByHx"] == 1,
                    ]
                ):
                    df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_Confirmed"] = 0
                    df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_Presum"] = 0
                    missing_confirmed += 1
                    missing_confirmed_not_confirmed += 1
            # if ByHx, Time should be Null
            if df.at[
                i, "Diagnosis_ClinicianConsensus,DX_" + n + "_ByHx"
            ] == 1 and not pd.isna(
                df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_Time"]
            ):
                df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_Time"] = pd.NA
                remove_time += 1
            # Past Doc should only be noted if ByHx is 1 or Time is 2
            if all(
                [
                    df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_ByHx"] != 1,
                    df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_Time"] != 2,
                ]
            ) and not pd.isna(
                df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_Past_Doc"]
            ):
                df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_Past_Doc"] = pd.NA
                remove_past_doc += 1
        # Remove "New" column
        df = df.drop(columns=["Diagnosis_ClinicianConsensus,DX_" + n + "_New"])
        # Remove remission columns (Remission and Partial Remission)
        df = df.drop(columns=["Diagnosis_ClinicianConsensus,DX_" + n + "_Rem"])
        df = df.drop(columns=["Diagnosis_ClinicianConsensus,DX_" + n + "_PRem"])
    print(
        "Filled missing ByHx with False for " + str(missing_ByHx) + " current diagnoses"
    )
    print(
        "There were "
        + str(missing_confirmed)
        + " diagnoses missing confirmed and presumptive values."
    )
    print(
        "Of these, "
        + str(missing_confirmed_sb_confirmed)
        + " were confirmed and "
        + str(missing_confirmed_not_confirmed)
        + " were not confirmed."
    )
    print(
        "Removed unnecessary time value for "
        + str(remove_time)
        + " diagnoses by history."
    )
    print(
        "Removed unnecessary past documentation for "
        + str(remove_past_doc)
        + " current diagnoses."
    )
    print("Data corrections completed.")
    save_path = hbn_data_path.replace(".csv", "_cleaned.csv")
    df.to_csv(save_path, index=False)
    print(f"Corrected data was saved to {save_path}")


# run - replace with raw data path
data_clean("data/HBN_data.csv")
