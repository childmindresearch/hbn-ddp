"""Tests for main script."""

import pandas as pd

from hbnddp.hbn_ddp import HBNData


def test_main_import() -> None:
    """Test that main script can be imported."""
    import hbnddp.__main__  # noqa: F401

    assert True


def test_main_execution() -> None:
    """Test that main function can be executed."""
    from hbnddp.__main__ import main

    assert callable(main)


def test_process() -> None:
    """Test the main processing function."""
    data = HBNData(input_path="tests/test_data.csv")
    output = data.process(
        by="diagnoses",
        include_details=True,
        output_path=None,
        viz=False,
    )
    assert output is not None
    assert isinstance(output, pd.DataFrame)
    # Check for expected columns
    expected_columns = [
        "Identifiers",
        "Diagnosis_ClinicianConsensus,NoDX",
        "ADHD_Hyperactive_Impulsive_Type_DiagnosisPresent",
        "ADHD_Hyperactive_Impulsive_Type_Certainty",
        "ADHD_Hyperactive_Impulsive_Type_Time",
    ]
    for col in expected_columns:
        assert col in output.columns
