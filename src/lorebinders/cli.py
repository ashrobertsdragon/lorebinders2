from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from lorebinders.builder import LoreBinderBuilder
from lorebinders.cli_adapters import AnalysisAdapter, ExtractionAdapter
from lorebinders.core.models import NarratorConfig, RunConfiguration
from lorebinders.ingestion.ingester import EbookIngester
from lorebinders.ingestion.workspace import WorkspaceManager
from lorebinders.reporting.pdf import ReportLabPDFReporter

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
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
    """LoreBinders: Create a Series Bible from your book.

    Raises:
        typer.Exit: If ingestion fails.
    """
    narrator_config = NarratorConfig(
        is_3rd_person=is_3rd_person,
        name=narrator_name,
    )

    config = RunConfiguration(
        book_path=book_path,
        author_name=author_name,
        book_title=book_title,
        narrator_config=narrator_config,
        custom_traits=traits or [],
        custom_categories=categories or [],
    )

    console.print("[green]Configuration Validated![/green]")
    console.print(config)

    console.print("[bold blue]Starting Ingestion...[/bold blue]")

    workspace_mgr = WorkspaceManager()
    workspace_path = workspace_mgr.ensure_workspace(
        author=config.author_name,
        title=config.book_title,
    )
    console.print(f"Workspace ready: {workspace_path}")

    console.print(f"Workspace ready: {workspace_path}")

    ingester = EbookIngester()
    extractor = ExtractionAdapter(config)
    analyzer = AnalysisAdapter(config)
    reporter = ReportLabPDFReporter()

    builder = LoreBinderBuilder(
        ingestion=ingester,
        extraction=extractor,
        analysis=analyzer,
        reporting=reporter,
    )

    try:
        console.print("[bold blue]Running Build Pipeline...[/bold blue]")
        builder.run(config)
        console.print(
            "[bold green]Build Complete![/bold green] PDF Report generated."
        )

    except Exception as e:
        console.print(f"[bold red]Build Failed:[/bold red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
