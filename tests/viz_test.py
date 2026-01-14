"""Unit tests for Visualization functions in hbnpreprocess.viz module."""

from hbnddp.hbn_ddp import HBNData
from hbnddp.viz import _bar, _clean_label


def test_bar() -> None:
    """Test bar plot function."""
    hbn_data = HBNData.create(input_path="tests/test_data.csv")
    test_result = hbn_data.pivot(by="all")
    # Test individual bar plots
    _bar(test_result, col_type="DiagnosisPresent")
    _bar(test_result, col_type="CategoryPresent")
    _bar(test_result, col_type="SubcategoryPresent")
    # Test if file is created
    import os

    assert os.path.exists("./figures/diagnosis_bar_plot.png")
    assert os.path.exists("./figures/category_bar_plot.png")
    assert os.path.exists("./figures/subcategory_bar_plot.png")
    # Delete created files
    os.remove("./figures/diagnosis_bar_plot.png")
    os.remove("./figures/category_bar_plot.png")
    os.remove("./figures/subcategory_bar_plot.png")
    # Delete created directory if empty
    if not os.listdir("./figures"):
        os.rmdir("./figures")
    # Test that invalid col_type raises ValueError
    try:
        _bar(test_result, col_type="InvalidType")  # type: ignore
        assert False
    except ValueError:
        assert True


def test_clean_label() -> None:
    """Test label cleaning function."""
    assert (
        _clean_label(
            "ADHD_Hyperactive_Impulsive_Type_DiagnosisPresent", "DiagnosisPresent"
        )
        == "ADHD Hyperactive Impulsive Type"
    )
    assert (
        _clean_label("Anxiety_Disorders_CategoryPresent", "CategoryPresent")
        == "Anxiety"
    )
    assert (
        _clean_label("Anxiety_Disorders_SubcategoryPresent", "SubcategoryPresent")
        == "Anxiety"
    )
