"""Module for handling the HBN data."""

from typing import Literal

import pandas as pd

from .processor import Processor
from .utils import write
from .viz import visualize


class HBNData:
    """Class for handling the HBN diagnostic data."""

    def __init__(self, input_path: str) -> None:
        """Initialize the HBNData class."""
        self.input_path = input_path
        self.processor = Processor()
        self.data = self.processor.load(input_path)

    def process(
        self,
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
        output = self.processor.pivot(self.data, by, certainty_filter, include_details)
        if viz:
            visualize(output, by)
        write(output, input_path=self.input_path, by=by, output_path=output_path)
        self.processed_data = output
        return output
