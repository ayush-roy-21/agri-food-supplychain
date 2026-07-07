# separate_gdelt_tiers.py
"""
Separates GDELT Corpus B datasets into two distinct analytical tiers:
1. MSMEs (Target Population Under Study) -> Corpus_B_*_GDELT_MSMEs_Extract.*
2. Large Listed & Star Export Houses (Comparator Group) -> Corpus_B_*_GDELT_Large_Listed_Extract.*

Processes both clean extracts (CorpusB/GDELT and data/CorpusB/GDELT) and raw extracts (data/raw/CorpusB/GDELT).
"""

import csv
import json
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    pd = None

def separate_dataset(file_path):
    if not file_path.exists():
        return
    
    records = []
    if file_path.suffix == ".json":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception as e:
            print(f"    [!] Error reading JSON {file_path.name}: {e}")
            return
    elif file_path.suffix == ".csv":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                records = list(reader)
        except Exception as e:
            print(f"    [!] Error reading CSV {file_path.name}: {e}")
            return
    else:
        return

    if not records:
        return

    msme_records = []
    large_records = []

    for item in records:
        scale = str(item.get("enterprise_scale_tier", "")).lower()
        relevance = str(item.get("relevance_to_study", "")).lower()
        
        if scale in ["large-listed", "large-private-star-export-house"] or "large-firm-comparator" in relevance:
            large_records.append(item)
        else:
            msme_records.append(item)

    parent = file_path.parent
    stem = file_path.stem
    
    if "_Extract" in stem:
        msme_stem = stem.replace("_Extract", "_MSMEs_Extract")
        large_stem = stem.replace("_Extract", "_Large_Listed_Extract")
    else:
        msme_stem = f"{stem}_MSMEs"
        large_stem = f"{stem}_Large_Listed"

    msme_path = parent / f"{msme_stem}{file_path.suffix}"
    large_path = parent / f"{large_stem}{file_path.suffix}"

    try:
        if file_path.suffix == ".csv":
            if pd:
                if msme_records:
                    df_msme = pd.DataFrame(msme_records)
                    df_msme.to_csv(msme_path, index=False)
                if large_records:
                    df_large = pd.DataFrame(large_records)
                    df_large.to_csv(large_path, index=False)
            else:
                if msme_records:
                    with open(msme_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=msme_records[0].keys())
                        writer.writeheader()
                        writer.writerows(msme_records)
                if large_records:
                    with open(large_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=large_records[0].keys())
                        writer.writeheader()
                        writer.writerows(large_records)

        print(f"[*] Separated {file_path.name}:")
        print(f"    -> MSME records: {len(msme_records)} saved to {msme_path.name}")
        print(f"    -> Large Listed records: {len(large_records)} saved to {large_path.name}")
    except Exception as e:
        print(f"    [!] Error saving separated files for {file_path.name}: {e}")

def main():
    project_root = Path(__file__).resolve().parent.parent.parent

    print("==========================================================================")
    print("  SEPARATING GDELT DATASETS: MSMES VS. LARGE LISTED COMPARATORS")
    print("==========================================================================")

    for d in [project_root / "CorpusB" / "GDELT", project_root / "data" / "CorpusB" / "GDELT"]:
        if d.exists():
            print(f"\n[*] Processing clean directory: {d}")
            separate_dataset(d / "Corpus_B_Clean_GDELT_Extract.csv")

    raw_dir = project_root / "data" / "raw" / "CorpusB" / "GDELT"
    if raw_dir.exists():
        print(f"\n[*] Processing raw directory: {raw_dir}")
        separate_dataset(raw_dir / "Corpus_B_Raw_GDELT_Extract.csv")

    print("\n[OK] Tier separation completed successfully!")

if __name__ == "__main__":
    main()
