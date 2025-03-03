"""Module for handling the HBN data."""

from dataclasses import dataclass
from typing import List, Literal, Optional

import pandas as pd

from .processor import Processor
from .utils import write
from .viz import visualize


@dataclass
class DataConfig:
    """Data configuration class."""

    clean_data: bool = False


class HBNData:
    """Class for handling the HBN diagnostic data."""

    @staticmethod
    def process(
        input_path: str,
        output_path: str | None = None,
        by: Literal["diagnoses", "subcategories", "categories", "all"] = "all",
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
        visualize(output, by)
        write(output, output_path=output_path, input_path=input_path)
        return output
