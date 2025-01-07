"""Script to fix ClinicianConsensusDiagnosis Data."""

import pandas as pd


def data_clean(hbn_data_path: str) -> None:
    """Fixes error and missing values in the diagnostic data and saves as csv.

    Args:
        hbn_data_path (str): The path to the HBN data file.

    Returns:
        None
    """
    # load data
    df = pd.read_csv(hbn_data_path, low_memory=False)

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
            # if ByHx, Time should be Null
            if df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_ByHx"] == 1:
                df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_Time"] = pd.NA
            # Past Doc should only be noted if ByHx is 1 or Time is 2
            if all(
                [
                    df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_ByHx"] != 1,
                    df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_Time"] != 2,
                ]
            ):
                df.at[i, "Diagnosis_ClinicianConsensus,DX_" + n + "_Past_Doc"] = pd.NA
        # Remove "New" column
        df = df.drop(columns=["Diagnosis_ClinicianConsensus,DX_" + n + "_New"])
        # Remove remission columns (Remission and Partial Remission)
        df = df.drop(columns=["Diagnosis_ClinicianConsensus,DX_" + n + "_Rem"])
        df = df.drop(columns=["Diagnosis_ClinicianConsensus,DX_" + n + "_PRem"])
    save_path = hbn_data_path.replace(".csv", "_cleaned.csv")
    df.to_csv(save_path, index=False)


# run
data_clean("data/HBN_Data_SympCheck2.0.csv")
