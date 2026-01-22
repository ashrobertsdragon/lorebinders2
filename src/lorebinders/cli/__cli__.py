import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)

from lorebinders import app
from lorebinders.cli.configuration import build_run_configuration
from lorebinders.logging import configure_logging
from lorebinders.models import ProgressUpdate

cli = typer.Typer(no_args_is_help=True)
console = Console()


@cli.command()
def main(
    book_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the ebook file (epub, pdf, etc.)",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    author_name: Annotated[str, typer.Option("--author", help="Author's name")],
    book_title: Annotated[str, typer.Option("--title", help="Book title")],
    narrator_name: Annotated[
        str | None,
        typer.Option(help="Name of the narrator (if using 1st person)"),
    ] = None,
    is_1st_person: Annotated[
        bool, typer.Option(help="Whether the book is written in 1st person")
    ] = False,
    traits: Annotated[
        list[str] | None, typer.Option("--trait", help="Custom trait to track")
    ] = None,
    categories: Annotated[
        list[str] | None,
        typer.Option("--category", help="Custom category to track"),
    ] = None,
    log_file: Annotated[
        Path | None, typer.Option("--log-file", help="Path to save logs")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable verbose logging")
    ] = False,
) -> None:
    """LoreBinders: Create a Story Bible from your book."""
    config = build_run_configuration(
        book_path=book_path,
        author_name=author_name,
        book_title=book_title,
        narrator_name=narrator_name,
        is_1st_person=is_1st_person,
        traits=traits,
        categories=categories,
    )

    if log_file or verbose:
        configure_logging(log_file)
        if verbose:
            logging.getLogger("lorebinders").setLevel(logging.DEBUG)

    console.print("[bold blue]Starting LoreBinders...[/bold blue]")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            extraction_task = progress.add_task(
                "Extracting...", total=None, visible=True
            )
            analysis_task = progress.add_task(
                "Analyzing...", total=None, visible=False
            )

            def handle_progress(update: ProgressUpdate) -> None:
                if update.stage == "extraction":
                    progress.update(
                        extraction_task,
                        completed=update.current,
                        total=update.total,
                        description=update.message,
                    )
                elif update.stage == "analysis":
                    progress.update(
                        analysis_task,
                        visible=True,
                        completed=update.current,
                        total=update.total,
                        description=update.message,
                    )

            output_path = app.run(
                config, progress=handle_progress, log_file=log_file
            )

        console.print(
            f"[bold green]Complete![/bold green] Report saved to: {output_path}"
        )
    except Exception as e:
        console.print(f"[bold red]Build Failed:[/bold red] {e}")
        raise


if __name__ == "__main__":
    cli()
