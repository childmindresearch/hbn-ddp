"""Unit tests for the Processor class in hbnpreprocess.processor module."""

import itertools
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from hbnddp.processor import Processor


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


def test_load() -> None:
    """Test load function."""
    data = Processor.load("tests/test_data.csv")
    assert data is not None


def test_category_preprocessor(categories_df: pd.DataFrame) -> None:
    """Test the category processor."""
    categories_df.iloc[1, 1] = None
    categories_df.iloc[2, 3] = np.nan
    assert categories_df.isnull().sum().sum() == 2
    result = Processor._preprocess_categories(categories_df)
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
    result = Processor._copy_static_columns(df)
    # Check that IDs are copied correctly
    assert result["Identifiers"].to_list() == ["NDAR1", "NDAR2"]
    # Check that all expected columns are present
    expected_cols = {"Identifiers"} | set(static_cols)
    assert set(result.columns) == expected_cols
    # Check that static columns have correct values
    assert result[static_cols].equals(df[static_cols])


def test_pivot() -> None:
    """Test pivot function."""
    data = Processor.load("tests/test_data.csv")
    output = Processor.pivot(data)
    assert output is not None
    assert output is not data
    assert len(output) == len(data)
