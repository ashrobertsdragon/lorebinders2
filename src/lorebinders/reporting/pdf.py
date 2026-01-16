"""Module for generating PDF reports using ReportLab."""

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from lorebinders.core.models import CharacterProfile
from lorebinders.reporting.styles import get_document_styles


def generate_pdf_report(
    data: list[CharacterProfile], output_path: Path
) -> None:
    """Generate a PDF report from the analysis data.

    Args:
        data: List of character profiles to report on.
        output_path: Path to save the PDF to.
    """
    doc = SimpleDocTemplate(str(output_path), pagesize=LETTER)
    styles = get_document_styles()
    story = []

    story.append(Paragraph("LoreBinders Series Bible", styles["Title"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Characters", styles["Heading1"]))
    story.append(Spacer(1, 12))

    for profile in data:
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
