"""Module for handling the HBN data."""

from dataclasses import dataclass
from typing import List, Literal, Optional

import pandas as pd

from .processor import Processor
from .utils import write
from .viz import Viz


@dataclass
class DataConfig:
    """Data configuration class."""

    clean_data: bool = False


class HBNData:
    """Class for handling the HBN diagnostic data."""

    NULL_DIAGNOSES = [
        "nan",
        "No Diagnosis Given",
        "No Diagnosis Given: Incomplete Eval",
        "",
        " ",
    ]

    @classmethod
    def process(
        cls,
        input_path: str,
        output_path: str,
        by: Literal["diagnoses", "subcategories", "categories", "all"],
        certainty_filter: Optional[List[str]] = None,
        time_filter: Optional[List[str]] = None,
        include_details: bool = False,
    ) -> pd.DataFrame:
        """Process the data."""
        data = Processor.load(input_path)
        output = Processor.copy(data)
        output = Processor.pivot(
            data, output, by, certainty_filter, time_filter, include_details
        )
        Viz.visualize(output, by)
        write(output, output_path)
        return output
