"""Module for generating PDF reports using ReportLab."""

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from lorebinders.models import EntityProfile
from lorebinders.reporting.styles import get_document_styles


def generate_pdf_report(data: list[EntityProfile], output_path: Path) -> None:
    """Generate a PDF report from the analysis data.

    Args:
        data: List of entity profiles to report on.
        output_path: Path to save the PDF to.
    """
    doc = SimpleDocTemplate(str(output_path), pagesize=LETTER)
    styles = get_document_styles()
    story = []

    story.append(Paragraph("LoreBinders Story Bible", styles["Title"]))
    story.append(Spacer(1, 12))

    grouped: dict[str, list[EntityProfile]] = {}
    for profile in data:
        if profile.category not in grouped:
            grouped[profile.category] = []
        grouped[profile.category].append(profile)

    sorted_categories = sorted(grouped.keys())

    for category in sorted_categories:
        story.append(Paragraph(category, styles["Heading1"]))
        story.append(Spacer(1, 12))

        profiles = sorted(grouped[category], key=lambda p: p.name)

        for profile in profiles:
            story.append(Paragraph(profile.name, styles["Heading2"]))

            if profile.traits:
                story.append(Paragraph("<b>Traits:</b>", styles["Normal"]))
                for trait_key, trait_value in profile.traits.items():
                    story.append(
                        Paragraph(
                            f"- <b>{trait_key}:</b> {trait_value}",
                            styles["Normal"],
                        )
                    )

            story.append(Spacer(1, 12))

    doc.build(story)
