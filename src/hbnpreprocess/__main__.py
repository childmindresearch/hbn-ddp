"""Main script for CLI run."""

from hbnpreprocess.hbn_data import HBNData
from hbnpreprocess.prompting import Interactive

# CLI run
args = Interactive.prompt()


HBNData.process(
    input_path=args["input_path"],
    output_path=args["output_path"],
    by=args["by"],
    qualifier_filter=args["qualifier_filter"],
    include_details=args["include_details"],
    viz=args["viz"],
)
