"""Module for handling the HBN data."""

from dataclasses import dataclass
from typing import Literal

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
        by: Literal[
            "diagnoses",
            "subcategories",
            "categories",
            "all",
        ] = "all",
        certainty_filter: list[str] | None = None,
        include_details: bool = False,
        viz: bool = True,
    ) -> pd.DataFrame:
        """Process the HBN clinician consensus diagnosis data by pivoting.

        Args:
            input_path: The path to the raw data.
            output_path: The path to save the processed data.
            by: The level of detail to pivot the data Options are "diagnosis",
            "subcategory", "category", and "all". Default is "all".
            certainty_filter: The list of certainties to include. Accepted values
            are "Confirmed", "Presumptive", "RC", "RuleOut", "ByHx", and
            "Unknown".
            Default is None, which will include all.
            include_details: When pivoting by category or subcategory, whether to
            include diagnosis level details in a separate column as a dictionary.
            viz: Whether to visualize the data. Displays and saves a bar plot showing
            the incidence of diagnoses or categories.

        Returns:
            The processed data.
        """
        data = Processor.load(input_path)
        output = Processor.pivot(data, by, certainty_filter, include_details)
        if viz:
            visualize(output, by)
        write(output, input_path=input_path, by=by, output_path=output_path)
        return output
