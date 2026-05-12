# Shared compiled regex patterns used across all extractors.
# Single home for these patterns — import from here, never redefine in extractor files.
import re

_INJECTION_RE = re.compile(
    r"ignore (previous|all) instructions|system:|you are now|forget your instructions",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"\b(\+\d{1,3}[\s-])?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b")
