"""Main script for CLI run."""

from hbn_data import HBNData
from prompting import Interactive

if __name__ == "__main__":
    HBNData.process(Interactive.prompt())
