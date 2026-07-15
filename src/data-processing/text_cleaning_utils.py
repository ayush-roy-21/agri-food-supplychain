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


# --- Chunk-level quality filters (added after reviewing the post-cleaning
# BERTopic run: 5 of 515 units were landing in an artifact cluster for
# reasons unrelated to the provenance-header issue above) ---

# Generic, automatic: catches PDF/OCR text-layer extraction failures where
# the font encoding is broken and pypdf/Tesseract emit control characters /
# non-ASCII glyph codes instead of real text. Calibrated against the live
# corpus: clean chunks (prose AND numeric/tabular content, e.g. trade-stat
# tables) sit at >=0.94; the one confirmed corrupted chunk sits at 0.20.
_MIN_PRINTABLE_ASCII_RATIO = 0.85


def is_corrupted_text(text: str) -> bool:
    text = str(text)
    if not text:
        return False
    ratio = sum(c.isprintable() and c.isascii() for c in text) / len(text)
    return ratio < _MIN_PRINTABLE_ASCII_RATIO


# Manually verified, NOT auto-detected: a stopword/common-word-ratio
# heuristic was tried and rejected because it false-positives on legitimate
# low-prose content (trade-statistics tables, EU frequency-check tables also
# score low). These 4 chunks were individually inspected during the Topic 2
# review and confirmed junk:
#   - A-SPICE-004-C04: OCR output is readable-looking but not real text
#     (likely a non-English source script misread by Tesseract) -- 98%
#     printable ASCII, so the automatic filter above does not catch it.
#   - B-GD-020-C06, B-GD-029-C06, B-GD-088-C04: the FINAL chunk only of
#     each parent article is scraper noise (related-articles widget /
#     comment-policy footer picked up by newspaper3k), not article body
#     text. Earlier chunks of these same parents are genuine and are kept.
VERIFIED_JUNK_CHUNK_IDS = {
    "A-SPICE-004-C04": "manually verified: OCR output not real text (non-English source script misread)",
    "B-GD-020-C06": "manually verified: trailing scraper-noise chunk (related-articles widget), not article text",
    "B-GD-029-C06": "manually verified: trailing scraper-noise chunk (related-articles widget), not article text",
    "B-GD-088-C04": "manually verified: trailing scraper-noise chunk (comment-policy footer), not article text",
}