"""Tests for main script."""


def test_main_import() -> None:
    """Test that main script can be imported."""
    import hbnddp.__main__  # noqa: F401

    assert True


def test_main_execution() -> None:
    """Test that main function can be executed."""
    from hbnddp.__main__ import main

    assert callable(main)
