"""Module for handling the HBN data."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class DataConfig:
    """Data configuration class."""

    clean_data: bool = False


class HbnDiagnosticData:
    """Class for handling the HBN diagnostic data."""

    NULL_DIAGNOSES = [
        "nan",
        "No Diagnosis Given",
        "No Diagnosis Given: Incomplete Eval",
        "",
        " ",
    ]

    @classmethod
    def load(
        path: Path,
        config: DataConfig,
    ) -> pd.DataFrame:
        """Load the data."""
        pass

    @classmethod
    def visualize(cls) -> None:
        """Visualize the data."""
        pass

    @classmethod
    def pivot(cls) -> pd.DataFrame:
        """Pivot the data."""
        pass

    @classmethod
    def explore(cls) -> None:
        """Explore data interactively."""
        pass
