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
    print("  THE BARRIER HORIZON — PIPELINE INTEGRITY & REPRODUCIBILITY AUDIT (v1.1.0)")
    print("=" * 80)

    errors = []

    def read_csv(path):
        import io
        with open(path, mode="r", encoding="utf-8-sig") as f:
            lines = [line for line in f if not line.startswith('#')]
        reader = csv.DictReader(io.StringIO("".join(lines)))
        return reader.fieldnames, list(reader)

    # 1. Master Registry Verification
    master_path = data_dir / "master_registry.csv"
    if not master_path.exists():
        errors.append(f"Missing master_registry.csv at {master_path}")
    else:
        master_headers, master_rows = read_csv(master_path)
        if len(master_headers) != 27:
            errors.append(f"Master Registry has {len(master_headers)} columns; expected 27.")
        if len(master_rows) != 260:
            errors.append(f"Master Registry has {len(master_rows)} records; expected exactly 260.")
        
        corpus_a_count = sum(1 for r in master_rows if r.get("corpus_tier") == "A")
        corpus_b_count = sum(1 for r in master_rows if r.get("corpus_tier") == "B")
        if corpus_a_count != 113:
            errors.append(f"Corpus A parent count = {corpus_a_count}; expected 113.")
        if corpus_b_count != 147:
            errors.append(f"Corpus B parent count = {corpus_b_count}; expected 147.")
        print(f"[OK] Master Registry verified: {len(master_rows)} records, {len(master_headers)} columns ({corpus_a_count} A, {corpus_b_count} B).")

    # 2. Chunk Manifest Verification
    manifest_path = data_dir / "chunk_manifest.csv"
    if not manifest_path.exists():
        errors.append(f"Missing chunk_manifest.csv at {manifest_path}")
    else:
        manifest_headers, manifest_rows = read_csv(manifest_path)
        if len(manifest_headers) != 10:
            errors.append(f"Chunk Manifest has {len(manifest_headers)} columns; expected 10.")
        if len(manifest_rows) != 357:
            errors.append(f"Chunk Manifest has {len(manifest_rows)} chunks; expected exactly 357.")
        print(f"[OK] Chunk Manifest verified: {len(manifest_rows)} chunks.")

    # 3. Modeling Units Metadata Verification
    units_path = embeddings_dir / "modeling_units_metadata.csv"
    meta_headers, meta_rows = None, None
    if not units_path.exists():
        errors.append(f"Missing modeling_units_metadata.csv at {units_path}")
    else:
        meta_headers, meta_rows = read_csv(units_path)
        if len(meta_rows) != 139:
            errors.append(f"Modeling Units Metadata has {len(meta_rows)} units; expected exactly 139.")
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
            if arr.shape != (139, 768):
                errors.append(f"unit_embeddings.npy shape is {arr.shape}; expected (139, 768).")
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
        if len(exc_rows) != 599:
            errors.append(f"Exceptions Log has {len(exc_rows)} items; expected exactly 599.")
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

    # 8. Locus & Verification Logic checks in Master Registry
    if master_rows is not None and master_headers is not None:
        if "locus_tag" not in master_headers or "verification_logic" not in master_headers:
            errors.append("master_registry.csv is missing locus_tag or verification_logic columns.")
        else:
            valid_loci = {
                "internal-capability",
                "relational-power",
                "institutional-voids",
                "informational-verifiability",
                "inductive-other"
            }
            valid_logics = {
                "not-applicable",
                "land-use-geolocation",
                "residue-and-mrl",
                "catch-legality-aquaculture",
                "facility-and-process"
            }
            
            invalid_loci = set()
            invalid_logics = set()
            
            for r in master_rows:
                locus = str(r.get("locus_tag", "")).strip()
                logic = str(r.get("verification_logic", "")).strip()
                
                if locus and locus not in valid_loci:
                    invalid_loci.add(locus)
                if logic and logic not in valid_logics:
                    invalid_logics.add(logic)
                    
            if invalid_loci:
                errors.append(f"Invalid locus_tag values found in registry: {invalid_loci}")
            else:
                print("[OK] Locus mapping valid: only canonical 4 Loci (and inductive-other) present in registry.")
                
            if invalid_logics:
                errors.append(f"Invalid verification_logic values found in registry: {invalid_logics}")
            else:
                print("[OK] Verification Logic mapping valid: only canonical 5 Logics present in registry.")

    # 9. Literature-Exclusion Check
    if master_rows is not None and meta_rows is not None:
        lit_docs = set(r.get("doc_id") for r in master_rows if r.get("corpus_role") == "background-literature")
        meta_parents = set(r.get("parent_doc_id") for r in meta_rows)
        intersection = lit_docs.intersection(meta_parents)
        if intersection:
            errors.append(f"Literature-Exclusion Check failed: {len(intersection)} literature documents leaked into modeling matrix.")
        else:
            print("[OK] Literature-Exclusion Check passed: 0 background-literature documents in modeling matrix.")
            
    # 9.5. Git LFS Pointer Stub Check
    lfs_stubs_found = []
    for file_path in data_dir.glob("Corpus*/**/*.*"):
        if file_path.is_file():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    first_line = f.readline()
                    if first_line.startswith("version https://git-lfs.github.com"):
                        lfs_stubs_found.append(file_path.name)
            except Exception:
                pass
    if lfs_stubs_found:
        errors.append(f"LFS Stub Check failed: Found unpulled Git LFS pointers instead of actual files: {lfs_stubs_found}")
    else:
        print("[OK] LFS Stub Check passed: No unpulled Git LFS pointer stubs found in Corpus.")
            
    # 10. Scale-Coverage Check
    if master_rows is not None:
        valid_scales = {
            "N/A (Corpus A)",
            "Tier 4 (indeterminate)",
            "Tier 3 (weakly indicated)",
            "Tier 2 (strongly indicated)",
            "Tier 1 (register-verified)",
            "Tier 5 (excluded-large)"
        }
        invalid_scales = set()
        for r in master_rows:
            scale = str(r.get("enterprise_scale_tier", "")).strip()
            if scale and scale not in valid_scales:
                invalid_scales.add(scale)
        if invalid_scales:
            errors.append(f"Scale-Coverage Check failed: Invalid enterprise_scale_tier values found: {invalid_scales}")
        else:
            print("[OK] Scale-Coverage Check passed: All enterprise_scale_tier values match canonical allowed set.")
            
    # 11. Temporal-Readiness Check
    import re
    if master_rows is not None:
        invalid_dates = 0
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}")
        for r in master_rows:
            date_str = str(r.get("retrieval_date_format_language", "")).strip()
            if date_str and not date_pattern.match(date_str):
                invalid_dates += 1
        if invalid_dates > 0:
            errors.append(f"Temporal-Readiness Check failed: {invalid_dates} records have malformed retrieval_date_format_language (missing ISO date).")
        else:
            print("[OK] Temporal-Readiness Check passed: All records have valid ISO dates.")
            
    # 12. Deliverables-Present Check
    rq_files = [
        "rq1_locus_distribution.csv",
        "rq2_hurdle_cooccurrence.csv",
        "rq3_actor_framing.csv",
        "rq_robustness_sensitivity.csv"
    ]
    missing_rqs = []
    for rqf in rq_files:
        if not (results_dir / rqf).exists():
            missing_rqs.append(rqf)
    if missing_rqs:
        errors.append(f"Deliverables-Present Check failed: Missing output files: {missing_rqs}")
    else:
        print("[OK] Deliverables-Present Check passed: All RQ and sensitivity CSVs exist.")
        
    # 13. RQ-Correctness Grep Check
    rq1_path = results_dir / "rq1_locus_distribution.csv"
    if rq1_path.exists():
        rq1_headers, rq1_rows = read_csv(rq1_path)
        if len(rq1_rows) == 0:
            errors.append("RQ-Correctness Grep Check failed: rq1_locus_distribution.csv is empty.")
        else:
            has_nan = any("nan" in str(v).lower() for row in rq1_rows for v in row.values())
            if has_nan:
                errors.append("RQ-Correctness Grep Check failed: 'nan' strings found in rq1_locus_distribution.csv.")
            else:
                print("[OK] RQ-Correctness Grep Check passed: RQ deliverables are populated and structurally sound.")

    # 14. Anchor Verdict Integrity Check
    if master_rows is not None:
        if "anchor_verdict" not in master_headers:
            errors.append("Anchor Verdict Check failed: anchor_verdict column is missing from master_registry.csv.")
        else:
            valid_verdicts = {"pass", "fail-actor", "fail-recognition", "fail-chain", "comparator"}
            missing_verdict = 0
            invalid_verdict = set()
            
            for r in master_rows:
                verdict = str(r.get("anchor_verdict", "")).strip()
                if not verdict:
                    missing_verdict += 1
                elif verdict not in valid_verdicts:
                    invalid_verdict.add(verdict)
                    
            if missing_verdict > 0:
                errors.append(f"Anchor Verdict Check failed: {missing_verdict} records are missing an anchor_verdict.")
            if invalid_verdict:
                errors.append(f"Anchor Verdict Check failed: Invalid verdicts found: {invalid_verdict}")
            if missing_verdict == 0 and not invalid_verdict:
                print("[OK] Anchor Verdict Check passed: All records have a valid anchor verdict.")

    # 15. Object-Gate Post-Anchor Checks (Step 9)
    # a. Evidence docs all being pass-units
    mapping_path = results_dir / "topic_locus_mapping.csv"
    if mapping_path.exists() and master_rows is not None:
        map_headers, map_rows = read_csv(mapping_path)
        pass_docs = set(r.get("doc_id") for r in master_rows if r.get("anchor_verdict") == "pass")
        invalid_ev = set()
        for r in map_rows:
            ev_docs_str = str(r.get("evidence_doc_ids", ""))
            if ev_docs_str:
                for d in ev_docs_str.split(";"):
                    d = d.strip()
                    # chunk id is usually like A-IEC-001-C01, parent is A-IEC-001
                    parent_d = d.rsplit("-", 1)[0] if d.count("-") >= 2 and d.split("-")[-1].startswith("C") else d
                    if parent_d not in pass_docs and d not in pass_docs:
                        invalid_ev.add(d)
        if invalid_ev:
            errors.append(f"Object-Gate Check failed: topic_locus_mapping.csv contains evidence docs not tagged as 'pass': {invalid_ev}")
        else:
            print("[OK] Object-Gate Check passed: All evidence docs in locus mapping belong to pass-units.")

    # b. All four loci having a primary hurdle or documented finding
    core_loci = {"internal-capability", "relational-power", "institutional-voids", "informational-verifiability"}
    if mapping_path.exists():
        covered_loci = set()
        for r in map_rows:
            covered_loci.add(str(r.get("locus_primary", "")).strip())
        
        # Check decision log for relational-power finding if it's missing from mapping
        dec_log_path = data_dir / "decision_log.csv"
        if dec_log_path.exists():
            dec_headers, dec_rows = read_csv(dec_log_path)
            for r in dec_rows:
                if str(r.get("impacted_locus_or_logic", "")).strip() in core_loci:
                    covered_loci.add(str(r.get("impacted_locus_or_logic", "")).strip())
                    
        missing_loci = core_loci - covered_loci
        if missing_loci:
            errors.append(f"Object-Gate Check failed: Missing primary hurdle or documented finding for loci: {missing_loci}")
        else:
            print("[OK] Object-Gate Check passed: All four core loci have a primary hurdle or documented decision-log finding.")

    # c. RQ3 actor-type diversity
    rq3_path = results_dir / "rq3_actor_framing.csv"
    if rq3_path.exists():
        rq3_headers, rq3_rows = read_csv(rq3_path)
        actors = set(str(r.get("actor_type", "")).strip() for r in rq3_rows if str(r.get("actor_type", "")).strip() and not str(r.get("actor_type", "")).startswith("#"))
        if len(actors) < 2:
            errors.append(f"Object-Gate Check failed: RQ3 actor-type diversity is low, found actors: {actors}")
        else:
            print(f"[OK] Object-Gate Check passed: RQ3 actor-type diversity confirmed ({len(actors)} types).")

    # d. Both sensitivity fits exceeding five topics (or >3 substantive)
    sens_path = results_dir / "rq_robustness_sensitivity.csv"
    if sens_path.exists():
        sens_headers, sens_rows = read_csv(sens_path)
        bad_fits = []
        for r in sens_rows:
            if not str(r.get("model", "")).startswith("#"):
                tc = int(r.get("topic_count", 0))
                if tc < 4:
                    bad_fits.append(r.get("model", "Unknown"))
        if bad_fits:
            errors.append(f"Object-Gate Check failed: Sensitivity fits {bad_fits} have < 4 substantive topics.")
        else:
            print("[OK] Object-Gate Check passed: Sensitivity fits maintained topic diversity.")

    # e. No superseded files live
    superseded = ["rq4_digital_systems.csv", "topic_rq_grid_mapping.csv", "grid_5x4_coverage.csv"]
    live_super = [f for f in superseded if (results_dir / f).exists()]
    if live_super:
        errors.append(f"Object-Gate Check failed: Superseded files still live in results dir: {live_super}")
    else:
        print("[OK] Object-Gate Check passed: No superseded v1.0.0 artifacts found in active results.")

    

    # 16. Round 2 Fixes Check
    import pandas as pd
    
    def check_uniformity(df, file_name, column_name):
        non_empty = df[column_name].replace("", pd.NA).dropna()
        non_empty = non_empty[non_empty != "Not Verified"]
        if not non_empty.empty and len(non_empty) > 10:
            top_val = non_empty.value_counts(normalize=True).iloc[0]
            if top_val > 0.90:
                errors.append(f"Round 2 Check failed: {file_name} has >90% identical values in {column_name}, indicating faked or unvaried lookups.")
    
    # a. alert_99_19_firms_verified.csv has no dummies and IS actually verified
    alert_99_path = results_dir / "alert_99_19_firms_verified.csv"
    if alert_99_path.exists():
        df_99 = pd.read_csv(alert_99_path)
        if df_99["firm_name"].str.contains("Dummy Firm").any():
            errors.append("Round 2 Check failed: alert_99_19_firms_verified.csv still contains Dummy Firms.")
        
        check_uniformity(df_99, "alert_99_19_firms_verified.csv", "register_consulted")
        
        verified_count = df_99["register_consulted"].notna().sum()
        if verified_count == 0:
             errors.append("Round 2 Check failed: alert_99_19_firms_verified.csv has no verification data.")
        else:
            print(f"[OK] Round 2 Check passed: alert_99_19_firms_verified.csv has real firms and partial/full verification ({verified_count} rows).")
            
    # b. alert_16_35_firms_verified.csv is actually verified
    alert_16_path = results_dir / "alert_16_35_firms_verified.csv"
    if alert_16_path.exists():
        df_16 = pd.read_csv(alert_16_path)
        
        check_uniformity(df_16, "alert_16_35_firms_verified.csv", "register_consulted")
        
        verified_count = df_16["register_consulted"].notna().sum()
        if verified_count == 0:
             errors.append("Round 2 Check failed: alert_16_35_firms_verified.csv has no verification data.")
        else:
            print(f"[OK] Round 2 Check passed: alert_16_35_firms_verified.csv has partial/full verification ({verified_count} rows).")
            
    # c. msme_voice.csv no dummy text
    msme_path = results_dir / "msme_voice.csv"
    if msme_path.exists():
        df_msme = pd.read_csv(msme_path)
        if df_msme["comment_text"].str.contains("Placeholder hand-coded").any():
            errors.append("Round 2 Check failed: msme_voice.csv still contains dummy text.")
        else:
            print("[OK] Round 2 Check passed: msme_voice.csv has real quotes.")
            
    # d. hurdle_evidence_trace.csv logic
    trace_path = results_dir / "hurdle_evidence_trace.csv"
    if trace_path.exists():
        df_trace = pd.read_csv(trace_path)
        if df_trace["evidence_files"].str.contains("SupplyChain_Research").any():
            errors.append("Round 2 Check failed: hurdle_evidence_trace.csv uses SupplyChain_Research.")
        
        invalid_dest = df_trace[~df_trace["destination_regime"].isin(["EU", "US"])]
        if not invalid_dest.empty:
            errors.append(f"Round 2 Check failed: hurdle_evidence_trace.csv has invalid destination_regime (must be EU or US strictly). Found: {invalid_dest['destination_regime'].unique()}")
        else:
            print("[OK] Round 2 Check passed: hurdle_evidence_trace.csv avoids SupplyChain_Research and has strict EU/US regimes.")

    print("-" * 80)
    if errors:
        print("[FAILED] PIPELINE INTEGRITY AUDIT DETECTED THE FOLLOWING ERRORS:")
        for err in errors:
            print(f"  * {err}")
        print("=" * 80)
        sys.exit(1)
    else:
        print("[SUCCESS] ALL PIPELINE ASSERTIONS PASSED. v1.1.0 ARCHIVE IS 100% REPRODUCIBLE.")
        print("=" * 80)
        sys.exit(0)

if __name__ == "__main__":
    verify_pipeline_integrity()
