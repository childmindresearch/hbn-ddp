"""Tests for main script."""

import itertools
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from hbnddp.hbn_ddp import HBNData


def test_main_import() -> None:
    """Test that main script can be imported."""
    import hbnddp.__main__  # noqa: F401

    assert True


def test_main_execution() -> None:
    """Test that main function can be executed."""
    from hbnddp.__main__ import main

    assert callable(main)


def _gen_col(prefix: str, i: int) -> list[str | None]:
    """Generate a row of data."""
    return [f"{prefix}_{i:02d}_{j:02d}" for j in range(1, 4)]


@pytest.fixture
def categories_df() -> pd.DataFrame:
    """Fixture for categories DataFrame."""
    cols = {
        f"Diagnosis_ClinicianConsensus,DX_{dx_idx:02d}_{dx_type}": _gen_col(
            dx_type, dx_idx
        )
        for dx_idx, dx_type in itertools.product(range(1, 11), ["Cat", "Sub"])
    }
    return pd.DataFrame(cols)


@pytest.fixture
def test_data_path() -> Path:
    """Fixture for test data path."""
    path = Path("tests/test_data.csv")
    if not path.exists():
        pytest.skip(f"Test data not found: {path}")
    return path


def test_create() -> None:
    """Test load function."""
    data = HBNData.create(input_path="tests/test_data.csv")
    assert data is not None
    assert isinstance(data, HBNData)


def test_preprocess_categories(categories_df: pd.DataFrame) -> None:
    """Test that blank subcategories are filled with category values."""
    categories_df.iloc[1, 1] = None
    categories_df.iloc[2, 3] = np.nan
    assert categories_df.isnull().sum().sum() == 2
    hbn_data = HBNData(
        data=categories_df, column_prefix="Diagnosis_ClinicianConsensus,"
    )
    result = hbn_data._preprocess_categories(
        data=hbn_data.data, column_prefix=hbn_data.column_prefix
    )
    # Check that the result is as expected
    assert result.isnull().sum().sum() == 0
    assert result.iloc[1, 1] == categories_df.iloc[1, 0]
    assert result.iloc[1, 1] == "Cat_01_02"
    assert result.iloc[2, 3] == categories_df.iloc[2, 2]
    assert result.iloc[2, 3] == "Cat_02_03"


def test_copy_static_columns() -> None:
    """Test the copy static columns function."""
    static_cols = [
        "Diagnosis_ClinicianConsensus,NoDX",
        "Diagnosis_ClinicianConsensus,Season",
        "Diagnosis_ClinicianConsensus,Site",
        "Diagnosis_ClinicianConsensus,Year",
    ]
    df = pd.DataFrame(
        {
            "Identifiers": ["NDAR1", "NDAR2,assessment"],
            "Diagnosis_ClinicianConsensus,NoDX": [1, 0],
            "Diagnosis_ClinicianConsensus,Season": ["Season_01", "Season_02"],
            "Diagnosis_ClinicianConsensus,Site": ["Site_01", "Site_02"],
            "Diagnosis_ClinicianConsensus,Year": ["Year_01", "Year_02"],
        }
    )
    hbn_data = HBNData(data=df, column_prefix="Diagnosis_ClinicianConsensus,")
    result = hbn_data._copy_static_columns(data=df)
    # Check that IDs are copied correctly
    assert result["Identifiers"].to_list() == ["NDAR1", "NDAR2"]
    # Check that all expected columns are present
    expected_cols = {"Identifiers"} | set(static_cols)
    assert set(result.columns) == expected_cols
    # Check that static columns have correct values
    assert result[static_cols].equals(df[static_cols])


def test_pivot() -> None:
    """Test pivot function."""
    hbn_data = HBNData.create(input_path="tests/test_data.csv")
    # Test that invalid certainty filter raises error
    with pytest.raises(ValueError):
        hbn_data.pivot(certainty_filter=["InvalidCertainty"])
    # Test that valid certainty filter works
    output_filtered = hbn_data.pivot(certainty_filter=["Confirmed", "Presumptive"])
    assert output_filtered is not None
    assert len(output_filtered) == len(hbn_data.data)
    # Test "by" options
    output_dx = hbn_data.pivot(by="diagnoses")
    assert output_dx is not None
    assert len(output_dx) == len(hbn_data.data)
    output_cat = hbn_data.pivot(by="categories")
    assert output_cat is not None
    assert len(output_cat) == len(hbn_data.data)
    output_sub = hbn_data.pivot(by="subcategories")
    assert output_sub is not None
    assert len(output_sub) == len(hbn_data.data)
    output_all = hbn_data.pivot(by="all")
    assert output_all is not None
    assert len(output_all) == len(hbn_data.data)

    # Test that invalid "by" option raises error
    with pytest.raises(ValueError):
        hbn_data.pivot(by="invalid_option")  # type: ignore


def test_process() -> None:
    """Test the main processing function."""
    hbn_data = HBNData.create("tests/test_data.csv")
    output = hbn_data.process(
        by="diagnoses",
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
    print(output.columns)
    for col in expected_columns:
        assert col in output.columns
