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

from lorebinders.models import Binder, EntityRecord
from lorebinders.reporting.styles import get_document_styles


def _create_occurrence_item(
    chap_num: int, val: str | list[str], styles: dict
) -> ListItem:
    """Create a list item for a trait occurrence.

    Args:
        chap_num: The chapter number.
        val: The trait value.
        styles: Document styles.

    Returns:
        A ListItem containing the formatted occurrence.
    """
    val_str = ", ".join(val) if isinstance(val, list) else str(val)
    text = f"Chapter {chap_num}: {val_str}"
    return ListItem(
        Paragraph(text, styles["Normal"]),
        bulletType="bullet",
        value="circle",
    )


def _add_trait_section(
    story: list,
    trait_name: str,
    occurrences: dict[int, str | list[str]],
    styles: dict,
) -> None:
    """Add a single trait and its occurrences to the report."""
    story.append(Paragraph(f"<b>{trait_name}</b>", styles["Normal"]))
    list_items = []
    for chap_num in sorted(occurrences.keys()):
        val = occurrences[chap_num]
        item = _create_occurrence_item(chap_num, val, styles)
        list_items.append(item)

    story.append(ListFlowable(list_items, bulletType="bullet", start="circle"))
    story.append(Spacer(1, 6))


def _process_entity(
    story: list,
    entity: EntityRecord,
    styles: dict,
) -> None:
    """Process a single entity and add it to the story."""
    story.append(Paragraph(entity.name, styles["Heading2"]))

    if entity.summary:
        story.append(Paragraph(entity.summary, styles["Normal"]))
        story.append(Spacer(1, 12))

    if entity.appearances:
        story.append(Paragraph("<b>Traits:</b>", styles["Normal"]))
        story.append(Spacer(1, 6))

        trait_map: dict[str, dict[int, str | list[str]]] = {}
        for chap_num, appearance in entity.appearances.items():
            for trait_name, trait_val in appearance.traits.items():
                if trait_name not in trait_map:
                    trait_map[trait_name] = {}
                trait_map[trait_name][chap_num] = trait_val

        for trait_name in sorted(trait_map.keys()):
            _add_trait_section(story, trait_name, trait_map[trait_name], styles)

    story.append(Spacer(1, 12))


def generate_pdf_report(data: Binder, output_path: Path) -> None:
    """Generate a PDF report from the Binder model."""
    doc = SimpleDocTemplate(str(output_path), pagesize=LETTER)
    styles = get_document_styles()
    story = []

    story.append(Paragraph("LoreBinders Story Bible", styles["Title"]))
    story.append(Spacer(1, 12))

    for cat_name in sorted(data.categories.keys()):
        category = data.categories[cat_name]
        story.append(Paragraph(category.name, styles["Heading1"]))
        story.append(Spacer(1, 12))

        for entity_name in sorted(category.entities.keys()):
            _process_entity(story, category.entities[entity_name], styles)

    doc.build(story)
