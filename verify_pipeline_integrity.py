"""
verify_pipeline_integrity.py

Self-check for the modeling pipeline (chunk_documents.py -> generate_embeddings.py
-> enrich_metadata_4x5.py -> run_bertopic_topics_per_class.py). Catches the specific
failure modes that came up repeatedly during development: stale embeddings/topics
left over from a partial re-run, provenance-header contamination creeping back in,
and topics_per_class_*.csv files computed against a different topic count than the
current bertopic_topic_info.csv.

Run after any pipeline step, from the repo root:
    python src/data-processing/verify_pipeline_integrity.py

Exits 0 if everything is consistent, 1 if anything fails.
"""

import sys
import glob
from pathlib import Path

import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTAMINATION_PATTERNS = "DQA Status|DQA Justification|FULL SUBSTANTIVE ARTICLE TEXT|Section 10 DQA|Section 6.2 DQA"

ok = True


def check(label, passed, detail=""):
    global ok
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail else ""))
    if not passed:
        ok = False


# 1. Row consistency across the three core files
meta = pd.read_csv(PROJECT_ROOT / "data/embeddings/modeling_units_metadata.csv")
emb = np.load(PROJECT_ROOT / "data/embeddings/unit_embeddings.npy")
topics = pd.read_csv(PROJECT_ROOT / "data/embeddings/modeling_units_with_topics.csv")

check(
    "Row counts consistent (metadata / embeddings / topics)",
    len(meta) == emb.shape[0] == len(topics),
    f"metadata={len(meta)}, embeddings={emb.shape[0]}, topics={len(topics)}",
)

# 2. Zero provenance-header contamination in the modeled text
contaminated = topics["text"].astype(str).str.contains(CONTAMINATION_PATTERNS, na=False)
check("No provenance-header contamination", contaminated.sum() == 0, f"{contaminated.sum()} contaminated units")

# 3. bertopic_topic_info.csv is the source of truth for topic count / outlier total
bt = pd.read_csv(PROJECT_ROOT / "data/results/bertopic_topic_info.csv")
current_max_topic = bt["Topic"].max()
current_non_outlier_total = bt[bt["Topic"] != -1]["Count"].sum()

# 4. Every topics_per_class_*.csv must reference the SAME topic run, not a stale one
per_class_files = sorted(glob.glob(str(PROJECT_ROOT / "data/results/topics_per_class_*.csv")))
if not per_class_files:
    check("topics_per_class_*.csv files found", False, "none found")
else:
    for f in per_class_files:
        df = pd.read_csv(f)
        max_t = df["Topic"].max()
        total_f = df[df["Topic"] != -1]["Frequency"].sum()
        aligned = (max_t == current_max_topic) and (total_f == current_non_outlier_total)
        check(
            f"{Path(f).name} aligned with current bertopic_topic_info.csv",
            aligned,
            f"file: max_topic={max_t}, total={total_f} | current: max_topic={current_max_topic}, total={current_non_outlier_total}",
        )

print()
print("ALL CHECKS PASSED" if ok else "ONE OR MORE CHECKS FAILED -- re-run the pipeline in order before trusting these outputs")
sys.exit(0 if ok else 1)