"""Module for generating PDF reports using ReportLab."""

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from lorebinders.models import Binder, EntityEntry
from lorebinders.reporting.styles import get_document_styles


def _process_chapter_traits(
    chapter_num: int,
    traits: dict[str, str | list[str]],
    aggregated_traits: dict[str, dict[int, str | list[str]]],
) -> None:
    """Process traits for a single chapter.

    Args:
        chapter_num: The chapter number.
        traits: The traits dictionary for the chapter.
        aggregated_traits: The mutable aggregation dictionary.
    """
    for trait_name, trait_val in traits.items():
        if trait_name not in aggregated_traits:
            aggregated_traits[trait_name] = {}
        aggregated_traits[trait_name][chapter_num] = trait_val


def _aggregate_traits(
    entity_data: EntityEntry,
) -> dict[str, dict[int, str | list[str]]]:
    """Aggregate traits from chapter-based entity key-values.

    Args:
        entity_data: The raw entity data containing chapter keys and summary.

    Returns:
        Structured trait map: {trait_name: {chapter_num: value}}
    """
    aggregated_traits: dict[str, dict[int, str | list[str]]] = {}

    for key, value in entity_data.items():
        if isinstance(key, int) and isinstance(value, dict):
            _process_chapter_traits(key, value, aggregated_traits)

    return aggregated_traits


def _create_occurrence_item(
    chap_num: int, val: str | list[str], styles: dict
) -> ListItem:
    """Create a list item for a trait occurrence.

    Args:
        chap_num: The chapter number.
        val: The trait value.
        styles: The stylesheet.

    Returns:
        A formatted ListItem.
    """
    val_str = ", ".join(val) if isinstance(val, list) else str(val)
    text = f"Chapter {chap_num}: {val_str}"
    return ListItem(
        Paragraph(text, styles["Normal"]),
        bulletType="bullet",
        value="circle",
    )


def _add_trait_occurrences(
    story: list, occurrences: dict[int, str | list[str]], styles: dict
) -> None:
    """Add individual trait occurrences to the story.

    Args:
        story: The list of flowables.
        occurrences: Map of chapter number to trait value.
        styles: The stylesheet.
    """
    list_items = []
    for chap_num in sorted(occurrences.keys()):
        val = occurrences[chap_num]
        item = _create_occurrence_item(chap_num, val, styles)
        list_items.append(item)

    story.append(ListFlowable(list_items, bulletType="bullet", start="circle"))


def _add_traits_section(
    story: list,
    aggregated_traits: dict[str, dict[int, str | list[str]]],
    styles: dict,
) -> None:
    """Add the traits section to the story.

    Args:
        story: The list of flowables.
        aggregated_traits: The aggregated traits data.
        styles: The stylesheet.
    """
    story.append(Paragraph("<b>Traits:</b>", styles["Normal"]))
    story.append(Spacer(1, 6))

    for trait_name in sorted(aggregated_traits.keys()):
        story.append(Paragraph(f"<b>{trait_name}</b>", styles["Normal"]))
        trait_occurrences = aggregated_traits[trait_name]
        _add_trait_occurrences(story, trait_occurrences, styles)
        story.append(Spacer(1, 6))


def _process_entity(
    story: list,
    entity_name: str,
    entity_data: EntityEntry,
    styles: dict,
) -> None:
    """Process a single entity and add it to the story.

    Args:
        story: The list of flowables.
        entity_name: The name of the entity.
        entity_data: The entity's data.
        styles: The stylesheet.
    """
    story.append(Paragraph(entity_name, styles["Heading2"]))

    summary_text = ""
    if "Summary" in entity_data:
        summary_val = entity_data["Summary"]
        if isinstance(summary_val, str):
            summary_text = summary_val

    if summary_text:
        story.append(Paragraph(summary_text, styles["Normal"]))
        story.append(Spacer(1, 12))

    aggregated_traits = _aggregate_traits(entity_data)

    if aggregated_traits:
        _add_traits_section(story, aggregated_traits, styles)

    story.append(Spacer(1, 12))


def _process_category(
    story: list,
    category: str,
    entities: dict[str, EntityEntry],
    styles: dict,
) -> None:
    """Process a category and add it to the story.

    Args:
        story: The list of flowables.
        category: The category name.
        entities: The dictionary of entities in the category.
        styles: The stylesheet.
    """
    story.append(Paragraph(category, styles["Heading1"]))
    story.append(Spacer(1, 12))

    for entity_name in sorted(entities.keys()):
        _process_entity(story, entity_name, entities[entity_name], styles)


def generate_pdf_report(data: Binder, output_path: Path) -> None:
    """Generate a PDF report from the analysis data.

    Args:
        data: The Binder dictionary containing categorized entity data.
        output_path: Path to save the PDF to.
    """
    doc = SimpleDocTemplate(str(output_path), pagesize=LETTER)
    styles = get_document_styles()
    story = []

    story.append(Paragraph("LoreBinders Story Bible", styles["Title"]))
    story.append(Spacer(1, 12))

    for category in sorted(data.keys()):
        entities = data[category]
        if isinstance(entities, dict):
            _process_category(story, category, entities, styles)

    doc.build(story)
