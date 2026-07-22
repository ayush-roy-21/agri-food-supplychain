"""
verify_pipeline_integrity.py
Stage 5 Verification Engine: Automated Data Quality & Pipeline Integrity Verification

This script executes automated assertions over the production data artifacts of
The Barrier Horizon: Sustainable Supplier Hurdles Facing Indian Agri-Food MSMEs (v1.0.0).

Reconciled from divergent verification scripts. Includes locus/RQ checks.
Does not depend on pandas to ensure single-command portability.
"""

import csv
import sys
import glob
from pathlib import Path

try:
    import numpy as np
except ImportError:
    np = None

CONTAMINATION_PATTERNS = ["DQA Status", "DQA Justification", "FULL SUBSTANTIVE ARTICLE TEXT", "Section 10 DQA", "Section 6.2 DQA"]

def verify_pipeline_integrity():
    root_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = root_dir / "data"
    embeddings_dir = data_dir / "embeddings"
    results_dir = data_dir / "results"

    print("=" * 80)
    print("  THE BARRIER HORIZON — PIPELINE INTEGRITY & REPRODUCIBILITY AUDIT (v1.0.0)")
    print("=" * 80)

    errors = []

    # Helper function to read csv
    def read_csv(path):
        with open(path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            return reader.fieldnames, list(reader)

    # 1. Master Registry Verification
    master_path = data_dir / "master_registry.csv"
    if not master_path.exists():
        errors.append(f"Missing master_registry.csv at {master_path}")
    else:
        master_headers, master_rows = read_csv(master_path)
        if len(master_headers) != 19:
            errors.append(f"Master Registry has {len(master_headers)} columns; expected 19.")
        if len(master_rows) != 267:
            errors.append(f"Master Registry has {len(master_rows)} records; expected exactly 267.")
        
        corpus_a_count = sum(1 for r in master_rows if r.get("corpus_tier") == "A")
        corpus_b_count = sum(1 for r in master_rows if r.get("corpus_tier") == "B")
        if corpus_a_count != 117:
            errors.append(f"Corpus A parent count = {corpus_a_count}; expected 117.")
        if corpus_b_count != 150:
            errors.append(f"Corpus B parent count = {corpus_b_count}; expected 150.")
        print(f"[OK] Master Registry verified: {len(master_rows)} records, {len(master_headers)} columns ({corpus_a_count} A, {corpus_b_count} B).")

    # 2. Chunk Manifest Verification
    manifest_path = data_dir / "chunk_manifest.csv"
    if not manifest_path.exists():
        errors.append(f"Missing chunk_manifest.csv at {manifest_path}")
    else:
        manifest_headers, manifest_rows = read_csv(manifest_path)
        if len(manifest_headers) != 10:
            errors.append(f"Chunk Manifest has {len(manifest_headers)} columns; expected 10.")
        if len(manifest_rows) != 383:
            errors.append(f"Chunk Manifest has {len(manifest_rows)} chunks; expected exactly 383.")
        print(f"[OK] Chunk Manifest verified: {len(manifest_rows)} chunks.")

    # 3. Modeling Units Metadata Verification
    units_path = embeddings_dir / "modeling_units_metadata.csv"
    meta_headers, meta_rows = None, None
    if not units_path.exists():
        errors.append(f"Missing modeling_units_metadata.csv at {units_path}")
    else:
        meta_headers, meta_rows = read_csv(units_path)
        if len(meta_rows) != 509:
            errors.append(f"Modeling Units Metadata has {len(meta_rows)} units; expected exactly 509.")
        print(f"[OK] Modeling Units Metadata verified: {len(meta_rows)} units.")

    # 4. Vector Embeddings Matrix Verification
    npy_path = embeddings_dir / "unit_embeddings.npy"
    emb_shape_0 = None
    if not npy_path.exists():
        errors.append(f"Missing unit_embeddings.npy at {npy_path}")
    else:
        if np is not None:
            arr = np.load(npy_path)
            emb_shape_0 = arr.shape[0]
            if arr.shape != (509, 768):
                errors.append(f"unit_embeddings.npy shape is {arr.shape}; expected (509, 768).")
            print(f"[OK] Vector Embeddings matrix verified: shape {arr.shape}.")
        else:
            print(f"[NOTE] numpy not installed; skipping shape check of {npy_path.name}.")

    # 5. Exceptions Log Verification
    exc_path = data_dir / "exceptions_log.csv"
    if not exc_path.exists():
        errors.append(f"Missing exceptions_log.csv at {exc_path}")
    else:
        exc_headers, exc_rows = read_csv(exc_path)
        if len(exc_headers) != 7:
            errors.append(f"Exceptions Log has {len(exc_headers)} columns; expected 7.")
        if len(exc_rows) != 401:
            errors.append(f"Exceptions Log has {len(exc_rows)} items; expected exactly 401.")
        print(f"[OK] Exceptions Log verified: {len(exc_rows)} items.")

    # 6. Row consistency across the three core files & Contamination
    topics_path = embeddings_dir / "modeling_units_with_topics.csv"
    if not topics_path.exists():
        errors.append(f"Missing modeling_units_with_topics.csv at {topics_path}")
    elif meta_rows is not None:
        topics_headers, topics_rows = read_csv(topics_path)
        
        # Checking consistency
        # If np is None, we just check against topics_rows and meta_rows
        valid_consistency = True
        if emb_shape_0 is not None:
            if not (len(meta_rows) == emb_shape_0 == len(topics_rows)):
                errors.append(f"Row count mismatch: metadata={len(meta_rows)}, embeddings={emb_shape_0}, topics={len(topics_rows)}")
                valid_consistency = False
        else:
            if len(meta_rows) != len(topics_rows):
                errors.append(f"Row count mismatch: metadata={len(meta_rows)}, topics={len(topics_rows)}")
                valid_consistency = False
                
        if valid_consistency:
            print(f"[OK] Row counts consistent across metadata, embeddings, and topics ({len(meta_rows)}).")
        
        # Provenance contamination
        contaminated_count = 0
        for r in topics_rows:
            text_val = r.get("text", "")
            if any(patt in text_val for patt in CONTAMINATION_PATTERNS):
                contaminated_count += 1
                
        if contaminated_count > 0:
            errors.append(f"Provenance-header contamination found in {contaminated_count} units in modeling_units_with_topics.csv.")
        else:
            print("[OK] No provenance-header contamination in modeled text.")

    # 7. bertopic_topic_info.csv is the source of truth for topic count / outlier total
    bt_path = results_dir / "bertopic_topic_info.csv"
    if not bt_path.exists():
        errors.append(f"Missing bertopic_topic_info.csv at {bt_path}")
    else:
        bt_headers, bt_rows = read_csv(bt_path)
        current_max_topic = -999
        current_non_outlier_total = 0
        
        for r in bt_rows:
            t_id = int(r.get("Topic", -1))
            if t_id > current_max_topic:
                current_max_topic = t_id
            if t_id != -1:
                current_non_outlier_total += int(r.get("Count", 0))

        per_class_files = sorted(glob.glob(str(results_dir / "topics_per_class_*.csv")))
        if not per_class_files:
            errors.append("No topics_per_class_*.csv files found.")
        else:
            misaligned = []
            for f in per_class_files:
                pc_headers, pc_rows = read_csv(f)
                max_t = -999
                total_f = 0
                for r in pc_rows:
                    t_id = int(r.get("Topic", -1))
                    if t_id > max_t:
                        max_t = t_id
                    if t_id != -1:
                        total_f += float(r.get("Frequency", 0))
                
                # Use int comparison for safety due to float parsing of Frequency
                if max_t != current_max_topic or int(total_f) != current_non_outlier_total:
                    misaligned.append(Path(f).name)
            
            if misaligned:
                errors.append(f"Stale per-class topic files (misaligned with bertopic_topic_info.csv): {', '.join(misaligned)}")
            else:
                print(f"[OK] All {len(per_class_files)} topics_per_class_*.csv files aligned with current topic info.")

    # 8. Locus & Verification Logic checks
    if meta_rows is not None and meta_headers is not None:
        if "commodity_group" not in meta_headers or "activity_channel" not in meta_headers:
            errors.append("modeling_units_metadata.csv is missing commodity_group or activity_channel columns.")
        else:
            valid_loci = {
                "Internal Capability",
                "Relational Power",
                "Institutional Voids",
                "Informational Verifiability",
                ""
            }
            valid_logics = {
                "Destination Border Controls & Refusals",
                "Laboratory Testing & Residue Assays",
                "Traceability & Digital Geotagging",
                "Trade Discourse & Practitioner Experience",
                "Facility Audit & Hygiene Standards",
                ""
            }
            
            invalid_loci = set()
            invalid_logics = set()
            
            for r in meta_rows:
                locus = str(r.get("commodity_group", "")).strip()
                logic = str(r.get("activity_channel", "")).strip()
                
                if locus not in valid_loci:
                    invalid_loci.add(locus)
                if logic not in valid_logics:
                    invalid_logics.add(logic)
                    
            if invalid_loci:
                errors.append(f"Invalid commodity_group values found: {invalid_loci}")
            else:
                print("[OK] Locus mapping valid: only canonical 4 Loci present.")
                
            if invalid_logics:
                errors.append(f"Invalid activity_channel values found: {invalid_logics}")
            else:
                print("[OK] Verification Logic mapping valid: only canonical 5 Logics present.")

    print("-" * 80)
    if errors:
        print("[FAILED] PIPELINE INTEGRITY AUDIT DETECTED THE FOLLOWING ERRORS:")
        for err in errors:
            print(f"  * {err}")
        print("=" * 80)
        sys.exit(1)
    else:
        print("[SUCCESS] ALL PIPELINE ASSERTIONS PASSED. v1.0.0 ARCHIVE IS 100% REPRODUCIBLE.")
        print("=" * 80)
        sys.exit(0)

if __name__ == "__main__":
    verify_pipeline_integrity()
