"""Main script for CLI run."""

import typer

from hbnpreprocess.hbn_data import HBNData
from hbnpreprocess.prompting import Interactive

app = typer.Typer(
    help="CLI for preprocessing HBN diagnostic data.",
)


@app.command()
def main() -> None:
    """Main function for CLI run."""
    args = Interactive.prompt()
    HBNData.process(
        input_path=args["input_path"],
        output_path=args["output_path"],
        by=args["by"],
        certainty_filter=args["certainty_filter"],
        include_details=args["include_details"],
        viz=args["viz"],
    )


if __name__ == "__main__":
    app()
