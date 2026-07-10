"""
ocr_corpus_a.py

OCR preprocessing for non-machine-readable Corpus A documents.
Resolves scanned-image PDFs and standalone JPGs that yielded 0 words
via pypdf text extraction, unblocking BERTopic ingestion.

Pipeline:
  1. Scans CorpusA/ for PDFs without .txt counterparts + standalone JPGs.
  2. Converts scanned PDF pages to images via PyMuPDF (no Poppler needed).
  3. Runs Tesseract OCR on each page image (or directly on JPGs).
  4. Post-OCR cleaning: strips form-feeds, normalizes whitespace, removes
     non-printable characters.
  5. Saves .txt output alongside source files and mirrors to data/ dirs.
  6. Updates master_registry.csv DQA scores and full_text_available status.
  7. Generates data/results/ocr_audit_log.csv with per-document stats.

Dependencies:
  pip install pytesseract pymupdf Pillow
  Tesseract OCR binary (UB-Mannheim build on Windows).
"""

import os
import re
import csv
import sys
from pathlib import Path
from datetime import datetime

import fitz  # PyMuPDF — renders PDF pages to images without Poppler
import pytesseract
from PIL import Image
import pandas as pd

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

# Tesseract binary path (UB-Mannheim default install on Windows)
TESSERACT_CMD = r"C:\Users\SCP\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# OCR settings
OCR_LANG = "eng"  # Language model for Tesseract
OCR_PSM = 6       # Page segmentation mode: assume uniform block of text
DPI = 300          # Resolution for PDF page rendering
LOW_CONFIDENCE_THRESHOLD = 70  # Flag documents below this mean confidence


def ocr_pdf_pages(pdf_path: Path) -> tuple[str, float]:
    """
    Render each page of a scanned PDF to an image via PyMuPDF,
    then run Tesseract OCR. Returns (extracted_text, mean_confidence).
    """
    doc = fitz.open(pdf_path)
    all_text_parts = []
    page_confidences = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        # Render page at specified DPI
        zoom = DPI / 72  # 72 is the default PDF resolution
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Run OCR with TSV output for confidence scoring
        tsv_data = pytesseract.image_to_data(
            img, lang=OCR_LANG, config=f"--psm {OCR_PSM}", output_type=pytesseract.Output.DATAFRAME
        )

        # Extract text
        page_text = pytesseract.image_to_string(img, lang=OCR_LANG, config=f"--psm {OCR_PSM}")

        if page_text.strip():
            all_text_parts.append(f"--- PAGE {page_num + 1} ---\n{page_text.strip()}")

        # Calculate mean confidence for words with confidence > 0
        word_confs = tsv_data[tsv_data["conf"] > 0]["conf"]
        if len(word_confs) > 0:
            page_confidences.append(word_confs.mean())

    doc.close()

    full_text = "\n\n".join(all_text_parts)
    mean_conf = sum(page_confidences) / len(page_confidences) if page_confidences else 0.0

    return full_text, mean_conf


def ocr_image_file(img_path: Path) -> tuple[str, float]:
    """
    Run Tesseract OCR directly on a standalone image file (JPG/PNG).
    Returns (extracted_text, mean_confidence).
    """
    img = Image.open(img_path)

    # Get text
    text = pytesseract.image_to_string(img, lang=OCR_LANG, config=f"--psm {OCR_PSM}")

    # Get confidence
    tsv_data = pytesseract.image_to_data(
        img, lang=OCR_LANG, config=f"--psm {OCR_PSM}", output_type=pytesseract.Output.DATAFRAME
    )
    word_confs = tsv_data[tsv_data["conf"] > 0]["conf"]
    mean_conf = word_confs.mean() if len(word_confs) > 0 else 0.0

    return text.strip(), mean_conf


def clean_ocr_text(raw_text: str) -> str:
    """
    Post-OCR cleaning:
    - Remove form-feed characters (\\x0c)
    - Remove null bytes
    - Strip non-printable characters (except newlines/tabs)
    - Normalize excessive whitespace
    - Fix common OCR artifacts (broken ligatures)
    """
    # Remove form-feeds and null bytes
    text = raw_text.replace("\x0c", "").replace("\x00", "")

    # Remove non-printable characters (keep newlines, tabs, spaces)
    text = re.sub(r"[^\x09\x0a\x0d\x20-\x7e\u00a0-\uffff]", "", text)

    # Normalize multiple spaces (but preserve newlines for structure)
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize excessive blank lines (max 2 consecutive)
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


def save_and_mirror_txt(
    txt_content: str,
    source_path: Path,
    corpus_a_root: Path,
    data_corpus_a: Path,
    data_raw_corpus_a: Path,
) -> None:
    """Save .txt alongside source file and mirror to data directories."""
    # Save alongside source
    txt_path = source_path.with_suffix(".txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(txt_content)

    # Mirror to data/CorpusA and data/raw/CorpusA
    rel_path = source_path.relative_to(corpus_a_root)
    for mirror_root in [data_corpus_a, data_raw_corpus_a]:
        mirror_txt = mirror_root / rel_path.with_suffix(".txt")
        mirror_txt.parent.mkdir(parents=True, exist_ok=True)
        with open(mirror_txt, "w", encoding="utf-8") as f:
            f.write(txt_content)


# Prefix mapping (same as extract_and_classify_corpus_a.py)
FOLDER_PREFIX_MAP = {
    "APEDA": "A-APEDA",
    "SpicesBoard": "A-SPICE",
    "MPEDA": "A-MPEDA",
    "FSSAI": "A-FSSAI",
    "EIC": "A-EIC",
    "DGFT_TradePortal": "A-DGFT",
    "EU_DGSANTE": "A-EU",
    "US_FDA": "A-FDA",
    "EUDR_CSDDD": "A-EUDR",
    "LegalInstruments": "A-LEGAL",
    "Certifications": "A-CERT",
    "CSR": "A-CSR",
    "IEC_Exporters": "A-IEC",
    "NITI_MSME": "A-MSME",
    "DataGov": "A-DATA",
    "StateAndGazette": "A-STATE",
    "MoFPI_PIB": "A-MOFPI",
    "SupplyChain_Research": "A-RES",
}


def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    corpus_a_root = project_root / "CorpusA"
    data_corpus_a = project_root / "data" / "CorpusA"
    data_raw_corpus_a = project_root / "data" / "raw" / "CorpusA"
    master_reg_path = project_root / "data" / "master_registry.csv"
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    ocr_audit_path = results_dir / "ocr_audit_log.csv"

    print("=" * 74)
    print("  CORPUS A: OCR PREPROCESSING FOR NON-MACHINE-READABLE DOCUMENTS")
    print("=" * 74)

    # Verify Tesseract is accessible
    try:
        version = pytesseract.get_tesseract_version()
        print(f"\n[OK] Tesseract OCR v{version} found at: {TESSERACT_CMD}")
    except Exception as e:
        print(f"\n[FATAL] Tesseract not found: {e}")
        print("        Install from: https://github.com/UB-Mannheim/tesseract/wiki")
        sys.exit(1)

    # ──────────────────────────────────────────
    # 1. Identify non-machine-readable files
    # ──────────────────────────────────────────
    print("\n[*] Step 1: Scanning for non-machine-readable documents...")

    targets = []

    # PDFs without .txt counterparts
    for pdf_path in sorted(corpus_a_root.rglob("*.pdf")):
        txt_path = pdf_path.with_suffix(".txt")
        if not txt_path.exists():
            targets.append(("pdf", pdf_path))
            print(f"    -> Queued (scanned PDF): {pdf_path.relative_to(corpus_a_root)}")

    # Standalone image files (JPG, PNG)
    for ext in ["*.jpg", "*.jpeg", "*.png"]:
        for img_path in sorted(corpus_a_root.rglob(ext)):
            txt_path = img_path.with_suffix(".txt")
            if not txt_path.exists():
                targets.append(("image", img_path))
                print(f"    -> Queued (image): {img_path.relative_to(corpus_a_root)}")

    if not targets:
        print("[OK] No non-machine-readable documents found. All files have .txt counterparts.")
        return

    print(f"\n[*] Found {len(targets)} documents requiring OCR.\n")

    # ──────────────────────────────────────────
    # 2. Run OCR on each target
    # ──────────────────────────────────────────
    print("[*] Step 2: Running Tesseract OCR...")

    audit_rows = []
    ocr_results = []  # (source_path, cleaned_text, word_count, confidence, file_type)

    for file_type, source_path in targets:
        rel = source_path.relative_to(corpus_a_root)
        print(f"\n    Processing: {rel}")

        try:
            if file_type == "pdf":
                raw_text, confidence = ocr_pdf_pages(source_path)
            else:
                raw_text, confidence = ocr_image_file(source_path)

            cleaned = clean_ocr_text(raw_text)
            word_count = len(cleaned.split())

            # Confidence flag
            conf_flag = "OK" if confidence >= LOW_CONFIDENCE_THRESHOLD else "LOW"
            if word_count == 0:
                conf_flag = "FAIL"

            print(f"      Words: {word_count:,} | Confidence: {confidence:.1f}% | Status: {conf_flag}")

            if conf_flag == "LOW":
                print(f"      [!] WARNING: Confidence below {LOW_CONFIDENCE_THRESHOLD}% — flagged for review")

            # Save and mirror
            if word_count > 0:
                save_and_mirror_txt(cleaned, source_path, corpus_a_root, data_corpus_a, data_raw_corpus_a)
                print(f"      Saved: {source_path.with_suffix('.txt').name}")

            ocr_results.append((source_path, cleaned, word_count, confidence, file_type))

            audit_rows.append({
                "timestamp": datetime.now().isoformat(),
                "source_file": str(rel),
                "file_type": file_type,
                "ocr_method": f"Tesseract {OCR_LANG} PSM-{OCR_PSM} @ {DPI}dpi",
                "word_count": word_count,
                "mean_confidence_pct": round(confidence, 1),
                "status": conf_flag,
                "output_file": str(rel.with_suffix(".txt")) if word_count > 0 else "N/A",
            })

        except Exception as e:
            print(f"      [ERROR] OCR failed: {e}")
            audit_rows.append({
                "timestamp": datetime.now().isoformat(),
                "source_file": str(rel),
                "file_type": file_type,
                "ocr_method": "FAILED",
                "word_count": 0,
                "mean_confidence_pct": 0.0,
                "status": "ERROR",
                "output_file": "N/A",
            })

    # ──────────────────────────────────────────
    # 3. Write OCR audit log
    # ──────────────────────────────────────────
    print(f"\n[*] Step 3: Writing OCR audit log to {ocr_audit_path.relative_to(project_root)}")

    with open(ocr_audit_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "source_file", "file_type", "ocr_method",
            "word_count", "mean_confidence_pct", "status", "output_file"
        ])
        writer.writeheader()
        writer.writerows(audit_rows)

    print(f"[OK] Audit log written with {len(audit_rows)} entries.")

    # ──────────────────────────────────────────
    # 4. Update master_registry.csv
    # ──────────────────────────────────────────
    print(f"\n[*] Step 4: Updating master_registry.csv...")

    if not master_reg_path.exists():
        print("[!] master_registry.csv not found — skipping registry update.")
    else:
        df_master = pd.read_csv(master_reg_path)
        existing_doc_ids = set(df_master["doc_id"].astype(str))

        # Build a lookup from filename → OCR result
        ocr_lookup = {}
        for source_path, cleaned, word_count, confidence, file_type in ocr_results:
            ocr_lookup[source_path.name] = (cleaned, word_count, confidence, file_type)

        updated_count = 0
        new_rows = []

        # Update existing registry rows (for PDFs already registered with DQA=I)
        for idx, row in df_master.iterrows():
            doc_id = str(row["doc_id"]).strip()
            title = str(row.get("title_url_query", "")).strip()

            # Match by filename in title_url_query, or by doc_id matching filename stem
            matched_key = None
            for fname in ocr_lookup:
                fname_stem = Path(fname).stem
                # Match if filename appears in title_url_query (direct filename or URL)
                if fname in title or fname_stem in title:
                    matched_key = fname
                    break
                # Match if doc_id matches the filename stem (e.g. A-SPICE-003 == A-SPICE-003.pdf)
                if doc_id == fname_stem:
                    matched_key = fname
                    break

            fta_val = str(row.get("full_text_available", "")).strip().lower()
            is_unreadable = fta_val.startswith("no") or fta_val == "i"
            if matched_key and is_unreadable:
                cleaned, word_count, confidence, file_type = ocr_lookup[matched_key]
                conf_flag = "OK" if confidence >= LOW_CONFIDENCE_THRESHOLD else "LOW"

                if word_count > 0:
                    # Update full_text_available
                    df_master.at[idx, "full_text_available"] = "yes (OCR)"

                    # Update DQA scores: recalculate Gran, Comp, Mach
                    folder_name = str(row.get("source_name_instrument_body", ""))
                    dqa_auth = "A" if any(k in folder_name.upper() for k in
                                          ["APEDA", "MPEDA", "SPICE", "FSSAI", "DGFT", "MOFPI", "EIC"]) else "M"
                    dqa_rel = "A"
                    dqa_gran = "A" if word_count >= 600 else ("M" if word_count >= 100 else "I")
                    dqa_curr = "A"
                    dqa_comp = "A" if word_count >= 600 else ("M" if word_count >= 100 else "I")
                    dqa_mach = "M" if conf_flag == "LOW" else "A"
                    new_dqa_score = f"{dqa_auth},{dqa_rel},{dqa_gran},{dqa_curr},{dqa_comp},{dqa_mach}"

                    df_master.at[idx, "dqa_context_score"] = new_dqa_score

                    # Update content score justification
                    df_master.at[idx, "dqa_content_score"] = (
                        f"Auth: Verified institutional source | "
                        f"Rel: High relevance ({word_count:,} words via OCR) | "
                        f"Gran: {'Substantive' if word_count >= 600 else 'Moderate' if word_count >= 100 else 'Minimal'} "
                        f"depth ({word_count:,} words) | "
                        f"Curr: Active policy/study corpus | "
                        f"Comp: OCR-extracted text ({word_count:,} words) | "
                        f"Mach: Tesseract OCR (confidence: {confidence:.1f}%)"
                    )

                    # Update access notes
                    df_master.at[idx, "access_status_notes"] = (
                        f"OCR-extracted {word_count:,} words via Tesseract {OCR_LANG} "
                        f"(confidence: {confidence:.1f}%, PSM-{OCR_PSM}, {DPI}dpi)"
                    )

                    updated_count += 1
                    print(f"    -> Updated: {doc_id} ({word_count:,} words, {confidence:.1f}% conf)")

                # Remove from lookup so we don't double-register
                del ocr_lookup[matched_key]

        # Register any remaining unregistered files (e.g., the 2 JPGs)
        if ocr_lookup:
            # Calculate next available doc_id counters
            folder_counters = {k: 100 for k in FOLDER_PREFIX_MAP.keys()}
            # Special counter for root-level unclassified files
            root_counter = 200

            for doc_id_str in existing_doc_ids:
                for folder, prefix in FOLDER_PREFIX_MAP.items():
                    if doc_id_str.startswith(prefix + "-"):
                        try:
                            num = int(doc_id_str.split("-")[-1])
                            if num >= folder_counters[folder]:
                                folder_counters[folder] = num + 1
                        except ValueError:
                            pass
                # Track RCAC counters too
                if doc_id_str.startswith("RCAC-"):
                    try:
                        num = int(doc_id_str.split("-")[-1])
                        if num >= root_counter:
                            root_counter = num + 1
                    except ValueError:
                        pass

            for fname, (cleaned, word_count, confidence, file_type) in ocr_lookup.items():
                if word_count == 0:
                    continue

                # Determine folder and prefix
                source_path_match = None
                for sp, _, _, _, _ in ocr_results:
                    if sp.name == fname:
                        source_path_match = sp
                        break

                if source_path_match is None:
                    continue

                parent_folder = source_path_match.parent.name
                if parent_folder == "CorpusA" or parent_folder == corpus_a_root.name:
                    # Root-level file
                    doc_id = f"RCAC-{root_counter:03d}"
                    root_counter += 1
                    folder_label = "CorpusA_Root"
                else:
                    prefix = FOLDER_PREFIX_MAP.get(parent_folder, "A-EXTRA")
                    doc_id = f"{prefix}-{folder_counters.get(parent_folder, 200):03d}"
                    if parent_folder in folder_counters:
                        folder_counters[parent_folder] += 1
                    folder_label = parent_folder

                conf_flag = "OK" if confidence >= LOW_CONFIDENCE_THRESHOLD else "LOW"
                dqa_gran = "A" if word_count >= 600 else ("M" if word_count >= 100 else "I")
                dqa_comp = dqa_gran
                dqa_mach = "M" if conf_flag == "LOW" else "A"

                new_row = {
                    "doc_id": doc_id,
                    "corpus_tier": "A",
                    "source_name_instrument_body": f"Corpus A OCR Recovery [{folder_label}]",
                    "title_url_query": fname,
                    "retrieval_date_format_language": f"{datetime.now().strftime('%Y-%m-%d')}, {file_type.upper()}->OCR->TXT, English",
                    "production_context": f"OCR-recovered {file_type} document from {folder_label}",
                    "dqa_context_score": f"M,A,{dqa_gran},A,{dqa_comp},{dqa_mach}",
                    "dqa_content_score": (
                        f"Auth: Image/infographic source (moderate authority) | "
                        f"Rel: High relevance ({word_count:,} words via OCR) | "
                        f"Gran: {word_count:,} words OCR-extracted | "
                        f"Curr: Active corpus | "
                        f"Comp: OCR text ({word_count:,} words) | "
                        f"Mach: Tesseract OCR (confidence: {confidence:.1f}%)"
                    ),
                    "full_text_available": "yes (OCR)",
                    "locus_tag": "ocr-recovered-document",
                    "verification_logic": "tesseract-ocr-extraction",
                    "deident_status": "not-applicable",
                    "access_status_notes": (
                        f"OCR-extracted {word_count:,} words via Tesseract {OCR_LANG} "
                        f"(confidence: {confidence:.1f}%, PSM-{OCR_PSM}, {DPI}dpi)"
                    ),
                    "firm_mentioned": "N/A - Regulatory / Reference Image",
                    "iec_verification_status": "N/A",
                    "verification_method": f"Tesseract OCR on {datetime.now().strftime('%Y-%m-%d')}",
                    "verification_date": datetime.now().strftime("%Y-%m-%d"),
                    "enterprise_scale_tier": "not-applicable",
                    "relevance_to_study": "Section 6 Corpus A baseline — OCR-recovered for BERTopic inclusion",
                }
                new_rows.append(new_row)
                print(f"    -> Registered NEW: {doc_id} ({fname}, {word_count:,} words)")

        if new_rows:
            df_new = pd.DataFrame(new_rows)
            df_master = pd.concat([df_master, df_new], ignore_index=True)

        if updated_count > 0 or new_rows:
            df_master.to_csv(master_reg_path, index=False, encoding="utf-8")
            print(f"\n[OK] Registry updated: {updated_count} existing rows upgraded, "
                  f"{len(new_rows)} new rows added.")
        else:
            print("[OK] No registry updates needed.")

    # ──────────────────────────────────────────
    # Summary
    # ──────────────────────────────────────────
    total_ok = sum(1 for r in audit_rows if r["status"] == "OK")
    total_low = sum(1 for r in audit_rows if r["status"] == "LOW")
    total_fail = sum(1 for r in audit_rows if r["status"] in ("FAIL", "ERROR"))
    total_words = sum(r["word_count"] for r in audit_rows)

    print(f"\n{'=' * 74}")
    print(f"  OCR PREPROCESSING COMPLETE")
    print(f"{'=' * 74}")
    print(f"  Documents processed:   {len(audit_rows)}")
    print(f"  Successful (>=70%):    {total_ok}")
    print(f"  Low confidence (<70%): {total_low}")
    print(f"  Failed:                {total_fail}")
    print(f"  Total words extracted: {total_words:,}")
    print(f"  Audit log:             data/results/ocr_audit_log.csv")
    print(f"{'=' * 74}")


if __name__ == "__main__":
    main()
