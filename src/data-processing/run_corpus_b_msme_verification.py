# run_corpus_b_msme_verification.py
"""
Stage 4 Post-DQA Empirical Scale Verification & Stratification Engine
=====================================================================

Ongoing Structural Meaning & Purpose in the Project Pipeline:
1. Continuous Verification Engine (Section 11 / Section 15 DQA):
   Whenever new GDELT articles, YouTube videos, or Reddit threads are scraped and processed through
   initial DQA filters (`dqa_filter_gdelt.py` / `dqa_filter_youtube.py`), this engine serves as the
   official Stage 4 post-DQA verification step. It scans all dossier texts against formal Udyam
   registration numbers (`UDYAM-XX-YY-ZZZZZZZ`), statutory APEDA/MPEDA/Spices Board/IEC RCMC directory
   keywords, and allowlisted corporate comparators (`VERIFIED_FIRM_ALLOWLIST`).

2. Unified Master Registry & Extract Synchronization:
   Synchronizes the 6-column verification metadata (`firm_mentioned`, `iec_verification_status`,
   `verification_method`, `verification_date`, `enterprise_scale_tier`, `relevance_to_study`) across
   `data/master_registry.csv` and all analytical JSON/CSV extracts across `data/CorpusB/GDELT`,
   `CorpusB/GDELT`, and `data/CorpusB/YouTube`, ensuring zero data drift between registry and extracts.

3. Automated Stratification Orchestrator:
   Automatically triggers `separate_gdelt_tiers.py` after verification to re-stratify analytical
   datasets into `_MSMEs_Extract` (Target Population Under Study) vs `_Large_Listed_Extract`
   (Comparator Group), ensuring downstream topic modeling (`BERTopic`) and econometric analyses always
   operate on verified, unskewed populations.

Governance Compliance:
- Strict Scope Adherence & No Invented Data or Assumptions (§11 / §15 DQA & AGENTS.md).
"""

import sys
import os
import csv
import json
import glob
import argparse
from pathlib import Path
from datetime import datetime

# Add project root and src directories to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root / "src" / "data-collection"))
sys.path.append(str(project_root / "src" / "data-processing"))

import entity_allowlist
import separate_gdelt_tiers

try:
    import pandas as pd
except ImportError:
    pd = None


def verify_and_stratify_corpus_b(verify=True, stratify=True, quiet=False) -> dict:
    """
    Executes the empirical Udyam/RCMC verification pass over all Corpus B records and/or
    re-stratifies analytical extracts.
    
    Returns a summary dictionary of scale tier frequencies across verified Corpus B rows.
    """
    if not quiet:
        print("==========================================================================")
        print("  STAGE 4 POST-DQA EMPIRICAL UDYAM & RCMC VERIFICATION ENGINE")
        print("==========================================================================")
    
    now_str = datetime.now().strftime("%Y-%m-%d")
    master_csv_path = project_root / "data" / "master_registry.csv"
    tier_counts = {"large-listed": 0, "large-private-star-export-house": 0, "msme-verified": 0, "keyword-plausible-unverified": 0, "unknown-unverified": 0, "not-applicable": 0}
    
    if verify:
        if not master_csv_path.exists():
            if not quiet:
                print(f"[!] Master registry not found at {master_csv_path}")
            return tier_counts
            
        # Load clean GDELT extracts if available
        gdelt_json_paths = [
            project_root / "data" / "CorpusB" / "GDELT" / "Corpus_B_Clean_GDELT_Extract.json",
            project_root / "CorpusB" / "GDELT" / "Corpus_B_Clean_GDELT_Extract.json"
        ]
        gdelt_records_map = {}
        for p in gdelt_json_paths:
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        recs = json.load(f)
                        for r in recs:
                            if "doc_id" in r:
                                gdelt_records_map[r["doc_id"]] = r
                except Exception as e:
                    if not quiet:
                        print(f"[!] Could not read {p}: {e}")
                    
        # Load clean YouTube extracts if available
        yt_json_path = project_root / "data" / "CorpusB" / "YouTube" / "Corpus_B_Clean_YouTube_Extract.json"
        yt_records_map = {}
        if yt_json_path.exists():
            try:
                with open(yt_json_path, "r", encoding="utf-8") as f:
                    recs = json.load(f)
                    for r in recs:
                        if "doc_id" in r:
                            yt_records_map[r["doc_id"]] = r
            except Exception as e:
                if not quiet:
                    print(f"[!] Could not read {yt_json_path}: {e}")

        # Read all rows from master_registry.csv
        with open(master_csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            all_rows = list(reader)
            
        if not all_rows:
            if not quiet:
                print("[!] Master registry is empty.")
            return tier_counts
            
        header = all_rows[0]
        data_rows = all_rows[1:]
        
        updated_count = 0
        
        for row in data_rows:
            if len(row) < 19:
                row.extend([""] * (19 - len(row)))
                
            if row[1] != "B":
                continue
                
            doc_id = row[0]
            text_to_scan = row[5]  # default to title_or_description
            
            # Check if we have text file for this doc_id
            txt_path_gd = project_root / "data" / "CorpusB" / "GDELT" / f"{doc_id}.txt"
            txt_path_yt = project_root / "data" / "CorpusB" / "YouTube" / f"{doc_id}.txt"
            
            if txt_path_gd.exists():
                try:
                    with open(txt_path_gd, "r", encoding="utf-8", errors="replace") as f:
                        text_to_scan = f.read()
                except Exception:
                    pass
            elif txt_path_yt.exists():
                try:
                    with open(txt_path_yt, "r", encoding="utf-8", errors="replace") as f:
                        text_to_scan = f.read()
                except Exception:
                    pass
            elif doc_id in gdelt_records_map:
                rec = gdelt_records_map[doc_id]
                text_to_scan = str(rec.get("title", "")) + " " + str(rec.get("raw_text", ""))
            elif doc_id in yt_records_map:
                rec = yt_records_map[doc_id]
                text_to_scan = str(rec.get("title", "")) + " " + str(rec.get("description", ""))
                
            # Run empirical verification scan
            _, meta = entity_allowlist.scan_and_generalize_text(text_to_scan)
            
            # Update row columns 14..19 (indices 13..18)
            row[13] = meta["firm_mentioned"]
            row[14] = meta["iec_verification_status"]
            row[15] = meta["verification_method"]
            row[16] = meta["verification_date"]
            row[17] = meta["enterprise_scale_tier"]
            row[18] = meta["relevance_to_study"]
            
            tier = meta["enterprise_scale_tier"]
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            updated_count += 1
            
            # Also update extract map record if exists
            if doc_id in gdelt_records_map:
                gdelt_records_map[doc_id]["firm_mentioned"] = meta["firm_mentioned"]
                gdelt_records_map[doc_id]["iec_verification_status"] = meta["iec_verification_status"]
                gdelt_records_map[doc_id]["verification_method"] = meta["verification_method"]
                gdelt_records_map[doc_id]["verification_date"] = meta["verification_date"]
                gdelt_records_map[doc_id]["enterprise_scale_tier"] = meta["enterprise_scale_tier"]
                gdelt_records_map[doc_id]["relevance_to_study"] = meta["relevance_to_study"]
                
            if doc_id in yt_records_map:
                yt_records_map[doc_id]["firm_mentioned"] = meta["firm_mentioned"]
                yt_records_map[doc_id]["iec_verification_status"] = meta["iec_verification_status"]
                yt_records_map[doc_id]["verification_method"] = meta["verification_method"]
                yt_records_map[doc_id]["verification_date"] = meta["verification_date"]
                yt_records_map[doc_id]["enterprise_scale_tier"] = meta["enterprise_scale_tier"]
                yt_records_map[doc_id]["relevance_to_study"] = meta["relevance_to_study"]

        # Write back updated master_registry.csv
        if not quiet:
            print(f"\n[*] Synchronizing {master_csv_path.name} across {updated_count} verified Corpus B rows...")
        with open(master_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(data_rows)
            
        if not quiet:
            print("[*] Verified Corpus B Scale Tier Breakdown:")
            for k, v in tier_counts.items():
                print(f"    -> {k}: {v}")
            
        # Write updated GDELT extracts
        if gdelt_records_map:
            gd_list = list(gdelt_records_map.values())
            for p in gdelt_json_paths:
                if p.parent.exists():
                    try:
                        with open(p, "w", encoding="utf-8") as f:
                            json.dump(gd_list, f, indent=2)
                        csv_p = p.with_suffix(".csv")
                        if pd:
                            pd.DataFrame(gd_list).to_csv(csv_p, index=False)
                        else:
                            with open(csv_p, "w", newline="", encoding="utf-8") as f:
                                w = csv.DictWriter(f, fieldnames=gd_list[0].keys() if gd_list else [])
                                w.writeheader()
                                w.writerows(gd_list)
                        if not quiet:
                            print(f"[*] Synchronized GDELT extract at {p.name}")
                    except Exception as e:
                        if not quiet:
                            print(f"[!] Error saving {p}: {e}")
                        
        # Write updated YouTube extracts
        if yt_records_map:
            yt_list = list(yt_records_map.values())
            try:
                with open(yt_json_path, "w", encoding="utf-8") as f:
                    json.dump(yt_list, f, indent=2)
                csv_p = yt_json_path.with_suffix(".csv")
                if pd:
                    pd.DataFrame(yt_list).to_csv(csv_p, index=False)
                else:
                    with open(csv_p, "w", newline="", encoding="utf-8") as f:
                        w = csv.DictWriter(f, fieldnames=yt_list[0].keys() if yt_list else [])
                        w.writeheader()
                        w.writerows(yt_list)
                if not quiet:
                    print(f"[*] Synchronized YouTube extract at {yt_json_path.name}")
            except Exception as e:
                if not quiet:
                    print(f"[!] Error saving {yt_json_path}: {e}")
                
    # Run separate_gdelt_tiers to generate/update MSMEs vs Large Listed comparator extracts
    if stratify:
        if not quiet:
            print("\n[*] Invoking separate_gdelt_tiers to update analytical strata...")
        separate_gdelt_tiers.main()
        
    if not quiet:
        print("\n[OK] Stage 4 Post-DQA Verification and Stratification completed successfully!")
        
    return tier_counts


def main():
    parser = argparse.ArgumentParser(description="Stage 4 Post-DQA Empirical Udyam/RCMC Verification & Stratification Engine")
    parser.add_argument("--verify-only", action="store_true", help="Run verification pass without re-stratifying extracts")
    parser.add_argument("--stratify-only", action="store_true", help="Re-stratify analytical extracts without running verification scan")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose logging output")
    args = parser.parse_args()
    
    verify_flag = not args.stratify_only
    stratify_flag = not args.verify_only
    
    verify_and_stratify_corpus_b(verify=verify_flag, stratify=stratify_flag, quiet=args.quiet)


if __name__ == "__main__":
    main()
