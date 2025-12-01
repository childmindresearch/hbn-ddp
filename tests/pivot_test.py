"""Tests for pivot functions."""

import pandas as pd

from hbnddp.pivot import Pivot
from hbnddp.processor import Processor

test_data = Processor.load("tests/test_data.csv")
test_output = Processor._copy_static_columns(test_data)

# Expected unique diagnoses in test data
expected_diagnoses = pd.unique(
    test_data[
        [
            f"Diagnosis_ClinicianConsensus,DX_{n}"
            for n in [f"{n:02d}" for n in range(1, 11)]
        ]
    ].values.ravel()
)
# Filter out invalid diagnosis values
expected_diagnoses = [
    d
    for d in expected_diagnoses
    if pd.notna(d)
    and d not in {"No Diagnosis Given", "No Diagnosis Given: Incomplete Eval", "", " "}
]

def test_clean_dx_value() -> None:
    """Test cleaning diagnosis value."""
    assert (
        Pivot._clean_dx_value("Posttraumatic Stress Disorder ")
        == "Posttraumatic_Stress_Disorder"
    )
    assert (
        Pivot._clean_dx_value("ADHD-Hyperactive/Impulsive Type")
        == "ADHD_Hyperactive_Impulsive_Type"
    )
    assert (
        Pivot._clean_dx_value(" Excoriation (Skin-Picking) Disorder")
        == "Excoriation_Skin_Picking_Disorder"
    )


def test_get_values() -> None:
    """Test getting unique diagnosis values."""
    dx_values = Pivot._get_values(test_data, "diagnoses")
    assert dx_values is not None
    assert callable(dx_values) is False, "dx_values should not be a function"
    assert all(isinstance(val, str) for val in dx_values)
    assert set(expected_diagnoses) == set(dx_values)
    dx_values = Pivot._get_values(test_data, "categories")
    assert dx_values is not None
    assert all(isinstance(val, str) for val in dx_values)

    dx_values = Pivot._get_values(test_data, "subcategories")
    assert dx_values is not None
    assert all(isinstance(val, str) for val in dx_values)


def test_set_certainty() -> None:
    """Test setting certainty levels."""
    # Test that single certainty is handled correctly
    single_cert = pd.DataFrame(
        {
            "Diagnosis_ClinicianConsensus,DX_01": ["ADHD_Hyperactive_Impulsive_Type"],
            "Diagnosis_ClinicianConsensus,DX_01_Confirmed": [1],
            "Diagnosis_ClinicianConsensus,DX_01_Presum": [0],
            "Diagnosis_ClinicianConsensus,DX_01_RC": [0],
            "Diagnosis_ClinicianConsensus,DX_01_RuleOut": [0],
            "Diagnosis_ClinicianConsensus,DX_01_ByHx": [0],
        }
    )
    assert (
        Pivot._set_certainty(single_cert, i=0, col="Diagnosis_ClinicianConsensus,DX_01")
        == "Confirmed"
    )

    # Test that multiple certainties are handled correctly
    mult_cert = pd.DataFrame(
        {
            "Diagnosis_ClinicianConsensus,DX_01": ["ADHD_Hyperactive_Impulsive_Type"],
            "Diagnosis_ClinicianConsensus,DX_01_Confirmed": [1],
            "Diagnosis_ClinicianConsensus,DX_01_Presum": [1],
            "Diagnosis_ClinicianConsensus,DX_01_RC": [0],
            "Diagnosis_ClinicianConsensus,DX_01_RuleOut": [0],
            "Diagnosis_ClinicianConsensus,DX_01_ByHx": [0],
        }
    )
    assert (
        Pivot._set_certainty(mult_cert, i=0, col="Diagnosis_ClinicianConsensus,DX_01")
        == "Unknown"
    )

    # Test that missing certainties are handled correctly
    missing_cert = pd.DataFrame(
        {
            "Diagnosis_ClinicianConsensus,DX_01": ["ADHD_Hyperactive_Impulsive_Type"],
            "Diagnosis_ClinicianConsensus,DX_01_Confirmed": [0],
            "Diagnosis_ClinicianConsensus,DX_01_Presum": [0],
            "Diagnosis_ClinicianConsensus,DX_01_RC": [0],
            "Diagnosis_ClinicianConsensus,DX_01_RuleOut": [0],
            "Diagnosis_ClinicianConsensus,DX_01_ByHx": [0],
        }
    )
    assert (
        Pivot._set_certainty(
            missing_cert, i=0, col="Diagnosis_ClinicianConsensus,DX_01"
        )
        == "Unknown"
    )


def test_set_time() -> None:
    """Test setting diagnosis time."""
    # Test current dx
    current_time = pd.DataFrame(
        {
            "Diagnosis_ClinicianConsensus,DX_01": ["ADHD_Hyperactive_Impulsive_Type"],
            "Diagnosis_ClinicianConsensus,DX_01_Time": [1],
        }
    )
    assert (
        Pivot._set_time(
            current_time,
            i=0,
            col="Diagnosis_ClinicianConsensus,DX_01",
        )
        == "Present"
    )

    # Test past dx
    past_time = pd.DataFrame(
        {
            "Diagnosis_ClinicianConsensus,DX_01": ["ADHD_Hyperactive_Impulsive_Type"],
            "Diagnosis_ClinicianConsensus,DX_01_Time": [2],
        }
    )
    assert (
        Pivot._set_time(past_time, i=0, col="Diagnosis_ClinicianConsensus,DX_01")
        == "Past"
    )

    # Test specific time course
    specific_time_course = pd.DataFrame(
        {
            "Diagnosis_ClinicianConsensus,DX_01": ["Major Depressive Disorder"],
            "Diagnosis_ClinicianConsensus,DX_01_Time": [1],
        }
    )
    assert (
        Pivot._set_time(
            specific_time_course, i=0, col="Diagnosis_ClinicianConsensus,DX_01"
        )
        == "Specific Time Course"
    )

    # Test missing time data
    missing_time = pd.DataFrame(
        {
            "Diagnosis_ClinicianConsensus,DX_01": ["ADHD_Hyperactive_Impulsive_Type"],
            "Diagnosis_ClinicianConsensus,DX_01_Time": [0],
        }
    )
    assert (
        Pivot._set_time(missing_time, i=0, col="Diagnosis_ClinicianConsensus,DX_01")
        == "Unknown"
    )


def test_filter_certainty() -> None:
    """Test filtering by certainty."""
    # Test that filter passes with no filter set
    assert Pivot._filter_pass("Confirmed", None) is True
    # Test that filter passes with filter that includes certainty
    assert Pivot._filter_pass("Confirmed", ["Confirmed", "Presumptive"]) is True
    # Test that filter fails with filter that excludes certainty
    assert Pivot._filter_pass("Confirmed", ["ByHx"]) is False


def test_diagnoses() -> None:
    """Test diagnoses pivot."""
    output = Pivot.diagnoses(test_data, test_output)
    assert output is not None
    assert output is not test_output
    assert len(output) == len(test_data)
    # Check that all expected diagnoses are in the output columns
    for dx in expected_diagnoses:
        clean_dx = Pivot._clean_dx_value(dx)
        col_name = f"{clean_dx}_DiagnosisPresent"
        assert col_name in output.columns

    single_dx_test_data = pd.DataFrame(
        {
            "Identifiers": ["Test1"],
            "Diagnosis_ClinicianConsensus,DX_01": ["ADHD-Hyperactive/Impulsive Type"],
            "Diagnosis_ClinicianConsensus,DX_01_Cat": ["Neurodevelopmental Disorders"],
            "Diagnosis_ClinicianConsensus,DX_01_Sub": [
                "Attention-Deficit/Hyperactivity Disorder"
            ],
            "Diagnosis_ClinicianConsensus,DX_01_Code": ["2"],
            "Diagnosis_ClinicianConsensus,DX_01_Confirmed": [1],
            "Diagnosis_ClinicianConsensus,DX_01_Presum": [0],
            "Diagnosis_ClinicianConsensus,DX_01_RC": [0],
            "Diagnosis_ClinicianConsensus,DX_01_RuleOut": [0],
            "Diagnosis_ClinicianConsensus,DX_01_ByHx": [0],
            "Diagnosis_ClinicianConsensus,DX_01_Time": [1],
            "Diagnosis_ClinicianConsensus,DX_01_Past_Doc": [pd.NA],
            "Diagnosis_ClinicianConsensus,DX_01_Spec": ["Specifier"],
        }
    )

    single_dx_test_output = Processor._copy_static_columns(single_dx_test_data)
    output = Pivot.diagnoses(single_dx_test_data, single_dx_test_output)
    assert len(output.columns) == len(single_dx_test_output.columns) + 8
    assert output.at[0, "ADHD_Hyperactive_Impulsive_Type_DiagnosisPresent"] == 1
    assert (
        output.at[0, "ADHD_Hyperactive_Impulsive_Type_Cat"]
        == "Neurodevelopmental Disorders"
    )
    assert (
        output.at[0, "ADHD_Hyperactive_Impulsive_Type_Sub"]
        == "Attention-Deficit/Hyperactivity Disorder"
    )
    assert output.at[0, "ADHD_Hyperactive_Impulsive_Type_ICD_Code"] == "2"
    assert output.at[0, "ADHD_Hyperactive_Impulsive_Type_Certainty"] == "Confirmed"
    assert output.at[0, "ADHD_Hyperactive_Impulsive_Type_Time"] == "Present"
    assert output.at[0, "ADHD_Hyperactive_Impulsive_Type_Past_Doc"] is pd.NA
    assert output.at[0, "ADHD_Hyperactive_Impulsive_Type_Spec"] == "Specifier"
