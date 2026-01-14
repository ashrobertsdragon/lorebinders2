"""Module for defining PDF report styles."""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, StyleSheet1


def get_document_styles() -> StyleSheet1:
    """Create and return the stylesheet for the PDF report.

    Returns:
        StyleSheet1: A collection of paragraph styles (Title, Headings, Normal).
    """
    stylesheet = StyleSheet1()

    stylesheet.add(
        ParagraphStyle(
            name="Title",
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=30,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.darkblue,
        )
    )

    stylesheet.add(
        ParagraphStyle(
            name="Heading1",
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            alignment=TA_LEFT,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.black,
        )
    )

    stylesheet.add(
        ParagraphStyle(
            name="Heading2",
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            alignment=TA_LEFT,
            spaceBefore=10,
            spaceAfter=4,
            textColor=colors.darkslategray,
        )
    )

    stylesheet.add(
        ParagraphStyle(
            name="Normal",
            fontName="Helvetica",
            fontSize=11,
            leading=14,
            alignment=TA_LEFT,
            spaceBefore=0,
            spaceAfter=0,
            textColor=colors.black,
        )
    )

    stylesheet.add(
        ParagraphStyle(
            name="BodyText",
            parent=stylesheet["Normal"],
            spaceBefore=0,
            spaceAfter=0,
        )
    )

    return stylesheet
