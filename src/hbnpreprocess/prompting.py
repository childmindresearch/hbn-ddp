"""Prompts user for interactive data filtering."""

import typing

import questionary

certs = ["Confirmed", "Presumptive", "RC", "RuleOut", "ByHx", "Unknown"]
times = ["Current", "Past"]


# TODO: finish this so that it can be used in the main script with process
# args as output
class Prompt:
    """Class for prompting user interactively."""

    def data_filter(**kwargs: bool) -> dict:
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

    def pivot(self) -> str:
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

    def visualize(self) -> bool:
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

    def get_filter_args(self, resp: dict) -> typing.Tuple[bool, bool, list, list]:
        """Returns parameters to use in pivot function."""
        cert_filter_applied = resp["apply_cert"]
        time_filter_applied = resp["apply_time"]
        if cert_filter_applied:
            cert_filter = resp["cert_filter"]
        else:
            cert_filter = certs
        if time_filter_applied:
            time_filter = resp["time_filter"]
        else:
            time_filter = times
        return cert_filter_applied, time_filter_applied, cert_filter, time_filter
