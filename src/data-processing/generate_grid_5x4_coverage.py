"""
src/data-processing/generate_grid_5x4_coverage.py

Generates `data/results/grid_5x4_coverage.csv` directly from the per-unit
enrichment labels in `data/embeddings/modeling_units_metadata.csv`.

Computes unit_count, distinct_parent_docs, corpus_A_units, corpus_B_units, and
assigns a coverage_flag (EMPTY, THIN (<=2 parent docs), or OK) across all
20 cells of the 4 Loci × 5 Verification Logics grid.
"""

import csv
from pathlib import Path
import pandas as pd

def main():
    root_dir = Path(__file__).resolve().parent.parent.parent
    metadata_path = root_dir / "data" / "embeddings" / "modeling_units_metadata.csv"
    output_path = root_dir / "data" / "results" / "grid_5x4_coverage.csv"
    
    print(f"[*] Loading modeling units metadata from: {metadata_path}")
    df = pd.read_csv(metadata_path)
    print(f"    Total units loaded: {len(df)}")
    
    loci_order = [
        "Marine & Aquaculture",
        "Spices & Botanical Herbs",
        "Horticulture, Cereals & Organic",
        "Cross-Cutting & Institutional Governance"
    ]
    
    logic_order = [
        "Laboratory Testing & Residue Assays",
        "Destination Border Controls & Refusals",
        "Traceability & Digital Geotagging",
        "Facility Audit & Hygiene Standards",
        "Trade Discourse & Practitioner Experience"
    ]
    
    rows = []
    for locus in loci_order:
        for logic in logic_order:
            subset = df[(df["commodity_group"] == locus) & (df["activity_channel"] == logic)]
            unit_count = len(subset)
            distinct_parent_docs = subset["parent_doc_id"].nunique() if unit_count > 0 else 0
            corpus_a_units = len(subset[subset["corpus_tier"] == "A"])
            corpus_b_units = len(subset[subset["corpus_tier"] == "B"])
            
            if unit_count == 0:
                coverage_flag = "EMPTY"
            elif distinct_parent_docs <= 2:
                coverage_flag = "THIN (<=2 parent docs)"
            else:
                coverage_flag = "OK"
                
            rows.append({
                "commodity_group": locus,
                "activity_channel": logic,
                "unit_count": unit_count,
                "distinct_parent_docs": distinct_parent_docs,
                "corpus_A_units": corpus_a_units,
                "corpus_B_units": corpus_b_units,
                "coverage_flag": coverage_flag
            })
            
    out_df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(output_path, index=False)
    print(f"[*] Saved 5x4 grid coverage table ({len(out_df)} rows) to: {output_path}\n")
    
    print(out_df.to_string(index=False))

if __name__ == "__main__":
    main()
