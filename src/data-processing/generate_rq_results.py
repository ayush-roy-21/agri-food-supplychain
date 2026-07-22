import pandas as pd
import numpy as np
from pathlib import Path
import itertools
from collections import Counter

def main():
    data_dir = Path("data")
    results_dir = data_dir / "results"
    
    # 1. Load Data
    units_df = pd.read_csv(data_dir / "embeddings" / "modeling_units_with_topics.csv")
    meta_df = pd.read_csv(data_dir / "embeddings" / "modeling_units_metadata.csv")
    topic_mapping = pd.read_csv(results_dir / "topic_locus_mapping.csv")
    
    # Merge datasets
    # units_df has 'Topic'. We can join with topic_mapping to get 'locus_primary'
    df = pd.merge(units_df, topic_mapping, left_on="assigned_topic", right_on="Topic", how="left")
    
    # Merge with meta_df to get verification_logic, digital_system_flag, etc. (join on unit_id or parent_doc_id)
    # Both units_df and meta_df have 'Document' / text? Wait, let's see what columns they have.
    # We can assume units_df has the same row order as meta_df since BERTopic outputs exactly match the input list.
    df = pd.concat([df, meta_df.drop(columns=[c for c in meta_df.columns if c in df.columns])], axis=1)
    
    # --- RQ1: Primary Loci of Friction ---
    # Distribution of hurdles across loci with unit counts and distinct parent document counts
    rq1_df = df[df["assigned_topic"] != -1].groupby("locus_primary").agg(
        total_modeling_units=("unit_id", "count"),
        distinct_parent_docs=("parent_doc_id", "nunique"),
        dominant_topics=("assigned_topic", lambda x: list(set(x)))
    ).reset_index()
    rq1_df.to_csv(results_dir / "rq1_locus_distribution.csv", index=False)
    print("Generated RQ1: rq1_locus_distribution.csv")
    
    # --- RQ2: Verification Logics Mediating Frictions ---
    # Cross-tabulate Locus (from topics) and Verification Logic (from metadata)
    rq2_df = df[df["assigned_topic"] != -1].groupby(["locus_primary", "verification_logic"]).agg(
        unit_count=("unit_id", "count"),
        distinct_parent_docs=("parent_doc_id", "nunique")
    ).reset_index()
    rq2_df.to_csv(results_dir / "rq2_logic_mediation.csv", index=False)
    print("Generated RQ2: rq2_logic_mediation.csv")
    
    # --- RQ3: Structural Capability Gaps & Actor Framing ---
    # We can look at the institutional_pillar / corpus_tier across loci
    rq3_df = df[df["assigned_topic"] != -1].groupby(["locus_primary", "institutional_pillar"]).agg(
        unit_count=("unit_id", "count"),
        distinct_parent_docs=("parent_doc_id", "nunique")
    ).reset_index()
    rq3_df.to_csv(results_dir / "rq3_actor_framing.csv", index=False)
    print("Generated RQ3: rq3_actor_framing.csv")
    
    # --- RQ4: Digital Systems Addressing Deficits ---
    # Analyze presence of digital systems by locus and verification logic
    rq4_df = df[df["assigned_topic"] != -1].groupby(["locus_primary", "digital_system_flag"]).agg(
        unit_count=("unit_id", "count"),
        systems_mentioned=("digital_systems_mentioned", lambda x: ", ".join(set([str(i) for i in x if pd.notna(i)])))
    ).reset_index()
    rq4_df.to_csv(results_dir / "rq4_digital_systems.csv", index=False)
    print("Generated RQ4: rq4_digital_systems.csv")

if __name__ == "__main__":
    main()
