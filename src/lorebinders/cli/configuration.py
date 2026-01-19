from pathlib import Path

from lorebinders.models import NarratorConfig, RunConfiguration


def build_run_configuration(
    book_path: Path,
    author_name: str,
    book_title: str,
    narrator_name: str | None,
    is_1st_person: bool,
    traits: list[str] | None,
    categories: list[str] | None,
) -> RunConfiguration:
    """Build a valid RunConfiguration from raw CLI arguments.

    Parses trait strings that may be in "Category:Trait" format.

    Args:
        book_path: Path to the book file.
        author_name: Name of the author.
        book_title: Title of the book.
        narrator_name: Name of the narrator (if any).
        is_1st_person: Whether the book is 3rd person.
        traits: List of trait strings (e.g. ["Appearance",
                "Location:Atmosphere"]).
        categories: List of custom category names.

    Returns:
        Structured RunConfiguration.
    """
    narrator_config = NarratorConfig(
        is_1st_person=is_1st_person,
        name=narrator_name,
    )

    custom_categories = categories or []
    custom_traits: dict[str, list[str]] = {}

    if traits:
        for t in traits:
            if ":" in t:
                category, trait = t.split(":", 1)
                category = category.strip()
                trait = trait.strip()
            else:
                category = "Characters"
                trait = t.strip()

            if category not in custom_traits:
                custom_traits[category] = []
            custom_traits[category].append(trait)

    return RunConfiguration(
        book_path=book_path,
        author_name=author_name,
        book_title=book_title,
        narrator_config=narrator_config,
        custom_traits=custom_traits,
        custom_categories=custom_categories,
    )
