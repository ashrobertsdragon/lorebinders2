from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from lorebinders import app
from lorebinders.cli.adapters import build_run_configuration

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
    is_3rd_person: Annotated[
        bool, typer.Option(help="Whether the book is written in 3rd person")
    ] = True,
    traits: Annotated[
        list[str] | None, typer.Option("--trait", help="Custom trait to track")
    ] = None,
    categories: Annotated[
        list[str] | None,
        typer.Option("--category", help="Custom category to track"),
    ] = None,
) -> None:
    """LoreBinders: Create a Story Bible from your book."""
    config = build_run_configuration(
        book_path=book_path,
        author_name=author_name,
        book_title=book_title,
        narrator_name=narrator_name,
        is_3rd_person=is_3rd_person,
        traits=traits,
        categories=categories,
    )

    console.print("[bold blue]Starting LoreBinders...[/bold blue]")

    try:
        output_path = app.run(config)
        console.print(
            f"[bold green]Complete![/bold green] Report saved to: {output_path}"
        )
    except Exception as e:
        console.print(f"[bold red]Build Failed:[/bold red] {e}")
        raise


if __name__ == "__main__":
    cli()
