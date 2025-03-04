"""Prompts user for interactive data filtering."""

import typing

import questionary

certs = ["Confirmed", "Presumptive", "RC", "RuleOut", "ByHx", "Unknown"]
times = ["Current", "Past"]


class Interactive:
    """Class for prompting user interactively."""

    @staticmethod
    def _get_paths() -> tuple[str, str]:
        """Prompts user for input path."""
        input_path = questionary.path(
            message="Please enter the path to the HBN data file.",
            default="./data/Diagnosis_ClinicianConsensus.csv",
        ).ask()
        output_path = questionary.path(
            message="Please enter the output path to save the processed data.",
            default=input_path.replace(".csv", "_processed.csv"),
        ).ask()
        return input_path, output_path

    @staticmethod
    def _pivot() -> str:
        """Prompts user for how to pivot the data."""
        questions = [
            {
                "type": "select",
                "name": "pivot_by",
                "message": "How would you like to pivot the data?",
                "choices": [
                    "diagnoses",
                    "subcategories",
                    "categories",
                    "all",
                ],
            }
        ]
        return questionary.prompt(questions)["pivot_by"]

    @staticmethod
    def _data_filter(**kwargs: bool) -> dict:
        """Prompts user for filtering."""
        print("The HBN dataset includes diagnoses of varying levels of certainty:")
        print(
            "confirmed, presumptive, requires confirmation (RC), rule out, and by "
            "history (ByHx)."
        )
        print(
            "It also includes differing times of diagnosis or symptoms: current or "
            "past."
        )
        questions = [
            {
                "type": "confirm",
                "name": "apply_cert",
                "message": "Filter the data by diagnostic certainty?",
                "default": True,
            },
            {
                "type": "checkbox",
                "name": "cert_filter",
                "message": "Please select which levels of diagnostic certainties should"
                " be included in the dataset.",
                "choices": certs,
                "when": lambda x: x["apply_cert"],
                "validate": lambda a: (
                    True if len(a) > 0 else "You must select at least one certainty"
                ),
            },
            {
                "type": "confirm",
                "name": "apply_time",
                "message": "Filter the data by time of diagnosis?",
                "default": True,
            },
            {
                "type": "checkbox",
                "name": "time_filter",
                "message": "Please select which times of diagnosis should be included",
                "choices": times,
                "when": lambda x: x["apply_time"],
                "validate": lambda a: (
                    True if len(a) > 0 else "You must select at least one time"
                ),
            },
        ]
        return questionary.prompt(questions, **kwargs)

    @staticmethod
    def _include_details() -> bool:
        """Prompts user for whether to include details."""
        questions = [
            {
                "type": "confirm",
                "name": "include_details",
                "message": "You have selected to pivot the data by higher level "
                "categories rather than specific diagnoses. Would you like to include "
                "diagnosis level details in the output?",
                "default": False,
            }
        ]
        return questionary.prompt(questions)["include_details"]

    @staticmethod
    def _visualize() -> bool:
        """Prompts user for how to visualize the data."""
        questions = [
            {
                "type": "confirm",
                "name": "visualize",
                "message": "Would you like to visualize the data?",
                "default": True,
            }
        ]
        return questionary.prompt(questions)["visualize"]

    @staticmethod
    def _get_filter_args(resp: dict) -> typing.Tuple[list | None, list | None]:
        """Returns parameters to use in pivot function."""
        if resp["apply_cert"]:
            certainty_filter = resp["cert_filter"]
        else:
            certainty_filter = None
        if resp["apply_time"]:
            time_filter = resp["time_filter"]
        else:
            time_filter = None
        return certainty_filter, time_filter

    @staticmethod
    def prompt() -> dict:
        """Runs the interactive prompts."""
        input_path, output_path = Interactive._get_paths()
        by = Interactive._pivot()
        if by == "subcategories" or by == "categories":
            include_details = Interactive._include_details()
        else:
            include_details = False
        certainty_filter, time_filter = Interactive._get_filter_args(
            Interactive._data_filter()
        )
        viz = Interactive._visualize()
        return {
            "input_path": input_path,
            "output_path": output_path,
            "by": by,
            "certainty_filter": certainty_filter,
            "time_filter": time_filter,
            "include_details": include_details,
            "viz": viz,
        }
