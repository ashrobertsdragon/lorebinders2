import re

NARRATOR_PATTERN = re.compile(
    r"\b(narrator|the narrator|the protagonist|protagonist|"
    r"the main character|main character|i|me|my|myself)\b",
    re.IGNORECASE,
)

LOCATION_SUFFIX_PATTERN = re.compile(r"\s*[\(\-].*", re.IGNORECASE)
