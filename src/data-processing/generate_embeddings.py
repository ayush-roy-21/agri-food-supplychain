"""generate_embeddings.py

Builds the unified modeling-units table (chunked long documents + whole short
documents) from data/master_registry.csv and data/chunk_manifest.csv, then
encodes every unit with intfloat/e5-base-v2 for downstream BERTopic modeling.

Usage:
    python src/data-processing/generate_embeddings.py

Requires (not yet in pyproject.toml — add before running):
    pip install sentence-transformers torch --break-system-packages

NOTE: This script needs internet access to huggingface.co the first time it
runs, to download the e5-base-v2 weights (~440MB). Run it somewhere with that
access (local machine / Colab) — not required to have GitHub access, just HF.
"""

import re
import sys
import numpy as np
import pandas as pd
from pathlib import Path

from text_cleaning_utils import strip_provenance_preamble

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MASTER_REG_PATH = PROJECT_ROOT / "data" / "master_registry.csv"
CHUNK_MANIFEST_PATH = PROJECT_ROOT / "data" / "chunk_manifest.csv"
EMBED_MODEL_NAME = "intfloat/e5-base-v2"
OUT_DIR = PROJECT_ROOT / "data" / "embeddings"

CHUNK_HEADER_SEP = "--------------------\n\n"


def strip_chunk_header(raw_text: str) -> str:
    """Chunk files carry a '--- CHUNK HEADER ---' block; strip it before embedding."""
    if CHUNK_HEADER_SEP in raw_text:
        text = raw_text.split(CHUNK_HEADER_SEP, 1)[1].strip()
    else:
        text = raw_text.strip()
    # Defense-in-depth: if this chunk file predates the chunk_documents.py
    # provenance-preamble fix (or embeddings are being regenerated against
    # stale chunks), also strip any surviving source-level header. No-op on
    # already-clean text.
    text, _ = strip_provenance_preamble(text)
    return text


def looks_like_raw_markup(text: str) -> bool:
    """
    Defensive guard: flags text that is raw scraped HTML rather than clean
    prose (found this affecting A-SPICE-006 during a manual audit — its
    matched raw file was leftover scrape debris, not the claimed derived
    summary). Checks only the first 3000 chars for speed.
    """
    sample = text[:3000]
    tag_count = len(re.findall(r"<[a-zA-Z/][^>]{0,30}>", sample))
    has_doctype = "<!DOCTYPE" in sample or "<html" in sample.lower()[:500]
    return tag_count > 5 or has_doctype


def build_parent_lookup(df_master: pd.DataFrame):
    """
    Same resolution strategy as chunk_documents.py's get_parent_info:
    match raw files back to a registered doc_id via exact doc_id filename
    match first, then via title_url_query, then via fuzzy substring match.
    Necessary because some registered docs (e.g. A-EUDR-101) are stored
    under source filenames that don't match their doc_id at all.
    """
    lookup_by_id = {}
    lookup_by_file = {}
    for _, row in df_master.iterrows():
        doc_id = str(row["doc_id"]).strip()
        info = {
            "doc_id": doc_id,
            "corpus_tier": str(row["corpus_tier"]).strip(),
            "locus_tag": str(row.get("locus_tag", "unassigned")),
            "verification_logic": str(row.get("verification_logic", "unassigned")),
            "dqa_score": str(row.get("dqa_context_score", "")),
            "full_text_available": str(row.get("full_text_available", "")),
        }
        lookup_by_id[doc_id] = info
        title_val = str(row.get("title_url_query", "")).strip()
        lookup_by_file[title_val] = info
        split_part = title_val.split("/")[-1]
        if split_part and len(split_part) > 2:
            clean_name = Path(split_part).name
            if clean_name and len(clean_name) > 2:
                lookup_by_file[clean_name] = info
    return lookup_by_id, lookup_by_file


def resolve_parent_info(txt_path: Path, lookup_by_id, lookup_by_file, expected_tier=None):
    base_id = txt_path.stem
    if base_id in lookup_by_id and (not expected_tier or lookup_by_id[base_id]["corpus_tier"] == expected_tier):
        return lookup_by_id[base_id]
    pdf_name = txt_path.with_suffix(".pdf").name
    if pdf_name in lookup_by_file and (not expected_tier or lookup_by_file[pdf_name]["corpus_tier"] == expected_tier):
        return lookup_by_file[pdf_name]
    if txt_path.name in lookup_by_file and (not expected_tier or lookup_by_file[txt_path.name]["corpus_tier"] == expected_tier):
        return lookup_by_file[txt_path.name]
    for k, v in lookup_by_file.items():
        if not k or len(k) < 4:
            continue
        if expected_tier and v["corpus_tier"] != expected_tier:
            continue
        if pdf_name in k or k in pdf_name:
            return v
    return None


def assemble_modeling_units():
    df_master = pd.read_csv(MASTER_REG_PATH)
    df_chunks = pd.read_csv(CHUNK_MANIFEST_PATH)

    lookup_by_id, lookup_by_file = build_parent_lookup(df_master)
    chunked_parents = set(df_chunks["parent_doc_id"].unique())

    rows = []
    skipped = []

    # 1. Chunk-level units (already-resolved, already-cleaned text on disk)
    for _, crow in df_chunks.iterrows():
        # chunk_manifest.csv was generated on Windows and stores paths with
        # backslashes (e.g. "CorpusA_Chunks\A-RES-100\...txt"); normalize
        # before joining or every lookup fails on POSIX systems.
        normalized_path = str(crow["chunk_path"]).replace("\\", "/")
        chunk_path = PROJECT_ROOT / normalized_path
        if not chunk_path.exists():
            skipped.append((crow["chunk_id"], "chunk file missing on disk"))
            continue
        raw = open(chunk_path, encoding="utf-8", errors="replace").read()
        text = strip_chunk_header(raw)
        if looks_like_raw_markup(text):
            skipped.append((crow["chunk_id"], "looks like raw HTML markup"))
            continue
        rows.append({
            "unit_id": crow["chunk_id"],
            "source_type": "chunk",
            "parent_doc_id": crow["parent_doc_id"],
            "corpus_tier": crow["corpus_tier"],
            "locus_tag": crow["parent_locus_tag"],
            "verification_logic": crow["parent_verification_logic"],
            "dqa_score": crow["parent_dqa_score"],
            "word_count": crow["word_count"],
            "text": text,
        })

    # 2. Whole-document units for every registered doc NOT already chunked
    all_txts = list((PROJECT_ROOT / "CorpusA").rglob("*.txt")) + list((PROJECT_ROOT / "CorpusB").rglob("*.txt"))
    resolved_whole_parents = set()
    for f in all_txts:
        info = resolve_parent_info(f, lookup_by_id, lookup_by_file)
        if info is None:
            continue
        doc_id = info["doc_id"]
        if doc_id in chunked_parents or doc_id in resolved_whole_parents:
            continue
        raw_text = open(f, encoding="utf-8", errors="replace").read().strip()
        if not raw_text:
            continue
        text, preamble_marker = strip_provenance_preamble(raw_text)
        if preamble_marker:
            skipped.append((doc_id, f"provenance preamble stripped ('{preamble_marker}'): "
                                     f"{len(raw_text.split())} words -> {len(text.split())} words"))
        # See DEC-2026-0XX (chunk_documents.py): after removing the
        # collection-pipeline header, some records (observed: all 3 Reddit
        # stubs) have little or no genuine discourse text left. Log and
        # exclude rather than embedding a near-empty unit.
        if len(text.split()) < 30:
            skipped.append((doc_id, f"whole-doc has only {len(text.split())} words of genuine "
                                     f"content after provenance-header removal (was "
                                     f"{len(raw_text.split())} words including header) — excluded "
                                     f"as near-empty, not modeled"))
            resolved_whole_parents.add(doc_id)
            continue
        if looks_like_raw_markup(text):
            skipped.append((doc_id, f"whole-doc looks like raw HTML markup ({f})"))
            continue
        resolved_whole_parents.add(doc_id)
        rows.append({
            "unit_id": doc_id,
            "source_type": "whole_document",
            "parent_doc_id": doc_id,
            "corpus_tier": info["corpus_tier"],
            "locus_tag": info["locus_tag"],
            "verification_logic": info["verification_logic"],
            "dqa_score": info["dqa_score"],
            "word_count": len(text.split()),
            "text": text,
        })

    # 3. Registered docs that never resolved to any text at all (structured-csv, etc.)
    all_registered = set(df_master["doc_id"].unique())
    covered = chunked_parents | resolved_whole_parents
    unresolved = all_registered - covered
    for doc_id in unresolved:
        row = df_master[df_master.doc_id == doc_id].iloc[0]
        skipped.append((doc_id, f"no text resolved (full_text_available='{row['full_text_available']}')"))

    df_units = pd.DataFrame(rows)
    return df_units, skipped


def main():
    df_units, skipped = assemble_modeling_units()

    print(f"[*] Assembled {len(df_units)} modeling units "
          f"({(df_units.source_type == 'chunk').sum()} chunks, "
          f"{(df_units.source_type == 'whole_document').sum()} whole documents).")
    print(f"[*] corpus_tier split: {df_units['corpus_tier'].value_counts().to_dict()}")
    if skipped:
        print(f"[!] {len(skipped)} items skipped / flagged — review before modeling:")
        for doc_id, reason in skipped:
            print(f"    - {doc_id}: {reason}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df_units.to_csv(OUT_DIR / "modeling_units_metadata.csv", index=False, encoding="utf-8")

    # --- Encoding step: requires sentence-transformers + HF access ---
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("\n[!] sentence-transformers not installed. Metadata table written to "
              f"{OUT_DIR / 'modeling_units_metadata.csv'}. Install deps and re-run "
              "to generate embeddings:\n    pip install sentence-transformers torch --break-system-packages")
        sys.exit(0)

    model = SentenceTransformer(EMBED_MODEL_NAME)
    # e5 models require a "passage: " prefix for all documents in symmetric
    # (clustering) use — not the "query: " prefix, which is for retrieval only.
    prefixed_texts = ["passage: " + t for t in df_units["text"].tolist()]
    embeddings = model.encode(
        prefixed_texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    np.save(OUT_DIR / "unit_embeddings.npy", embeddings)
    print(f"[*] Saved embeddings: {OUT_DIR / 'unit_embeddings.npy'} shape={embeddings.shape}")
    print(f"[*] Saved metadata:   {OUT_DIR / 'modeling_units_metadata.csv'}")


if __name__ == "__main__":
    main()