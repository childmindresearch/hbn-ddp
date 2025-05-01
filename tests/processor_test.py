"""Unit tests for the Processor class in hbnpreprocess.processor module."""

import itertools

import numpy as np
import pandas as pd
import pytest

from hbnpreprocess.processor import Processor


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
            "Identifiers": ["Identifiers_01", "Identifiers_02,Identifiers_03"],
            "Diagnosis_ClinicianConsensus,NoDX": ["NoDX_01", "NoDX_02"],
            "Diagnosis_ClinicianConsensus,Season": ["Season_01", "Season_02"],
            "Diagnosis_ClinicianConsensus,Site": ["Site_01", "Site_02"],
            "Diagnosis_ClinicianConsensus,Year": ["Year_01", "Year_02"],
            "Extra_Column": ["Extra_01", "Extra_02"],
        }
    )
    result = Processor._copy_static_columns(df)
    # Check that the result is as expected
    assert result["Identifiers"].to_list() == [
        "Identifiers_01",
        "Identifiers_02",
    ]
    assert result.columns.tolist() == ["Identifiers"] + static_cols
    assert result[static_cols].equals(df[static_cols])
