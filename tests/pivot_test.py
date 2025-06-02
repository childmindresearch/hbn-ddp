"""Tests for pivot functions."""

from hbnddp.processor import Processor


def test_load() -> None:
    """Test load function."""
    data = Processor.load("tests/test_data.csv")
    assert data is not None


def test_pivot() -> None:
    """Test pivot function."""
    data = Processor.load("tests/test_data.csv")
    output = Processor.pivot(data)
    assert output is not None
    assert output is not data
    assert len(output) == len(data)


def test_diagnoses() -> None:
    """Test diagnoses pivot."""
    pass
