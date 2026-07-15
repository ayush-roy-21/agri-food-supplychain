"""
text_cleaning_utils.py

Shared utility to strip collection-pipeline provenance/DQA headers that were
written directly into raw source .txt files (Doc ID, DQA scores, retrieval
metadata, etc.) by the GDELT / YouTube / Reddit collection scripts, so that
downstream chunking, word-counting, and embedding operate on genuine
discourse/article content only.

Root cause: gdelt_pipeline.py / youtube_scraper.py / reddit collector wrote
this metadata as part of the saved article text rather than only into
master_registry.csv. chunk_documents.py's own header (the "--- CHUNK HEADER
---" block it adds during chunking) is a separate, later-stage wrapper and is
stripped independently by generate_embeddings.py's strip_chunk_header(); this
utility handles the INNER, source-level preamble that predates chunking.

Deliberately conservative: only strips when a known marker is found within a
short leading window AND preceded by the pipeline's "====" separator line, so
Corpus A documents (including structured registry profiles like A-IEC-* that
legitimately start with "Doc ID:") are left completely untouched.
"""

import re
from typing import Optional, Tuple

_SEPARATOR_RE = re.compile(r"=" * 10 + r"+")

# (marker text, human label) -- checked in order; first match wins.
_KNOWN_MARKERS = [
    ("FULL SUBSTANTIVE ARTICLE TEXT:", "gdelt_article_marker"),
    ("DESCRIPTION:", "youtube_description_marker"),
]

_REDDIT_MARKER = "--- DE-IDENTIFIED PUBLIC DISCOURSE SAMPLES ---"

# How far into the file (chars) the separator/marker must appear to be
# treated as a header rather than incidental in-body text.
_MAX_HEADER_WINDOW = 2000


def strip_provenance_preamble(text: str) -> Tuple[str, Optional[str]]:
    """
    Returns (cleaned_text, marker_stripped).
    marker_stripped is None if no known preamble pattern was found (text is
    returned unchanged in that case).
    """
    if not text:
        return text, None

    window = text[:_MAX_HEADER_WINDOW]

    # GDELT / YouTube: marker must follow a "====...====" separator line,
    # both within the leading window, to avoid false positives on body text
    # that happens to contain the word "DESCRIPTION:".
    sep_match = _SEPARATOR_RE.search(window)
    if sep_match:
        after_sep = text[sep_match.end():sep_match.end() + 200]
        for marker, label in _KNOWN_MARKERS:
            idx = after_sep.find(marker)
            if idx != -1:
                abs_idx = sep_match.end() + idx + len(marker)
                remainder = text[abs_idx:].strip()
                return remainder, label

    # Reddit: header ends at the "--- DE-IDENTIFIED PUBLIC DISCOURSE
    # SAMPLES ---" marker with no preceding "====" separator.
    idx = window.find(_REDDIT_MARKER)
    if idx != -1:
        remainder = text[idx + len(_REDDIT_MARKER):].strip()
        return remainder, "reddit_samples_marker"

    return text, None