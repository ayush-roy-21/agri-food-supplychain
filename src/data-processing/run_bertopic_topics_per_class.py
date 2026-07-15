"""
run_bertopic_topics_per_class.py

Fits BERTopic once on the existing 610-unit e5-base-v2 vector matrix (unit_embeddings.npy)
and enriched metadata (modeling_units_metadata.csv), then executes `topics_per_class()`
across 6 analytical criteria:
1. corpus_tier (Corpus A vs. Corpus B)
2. institutional_pillar (12-category regulatory/discourse source taxonomy)
3. locus_bucket (Canonical 4-Locus Grid)
4. logic_bucket (Canonical 5-Verification-Logic Grid)
5. grid_bucket (Canonical 4x5 Grid: Locus x Logic)
6. digital_system_flag (Yes vs. No digital export platform presence)

Usage:
    python src/data-processing/run_bertopic_topics_per_class.py
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

try:
    from bertopic import BERTopic
    from umap import UMAP
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import CountVectorizer
except ImportError as e:
    print(f"[ERROR] Required modeling packages missing: {e}")
    print("Please run: python -m pip install bertopic umap-learn hdbscan scikit-learn")
    sys.exit(1)


def main():
    root_dir = Path(__file__).resolve().parent.parent.parent
    embeddings_path = root_dir / "data" / "embeddings" / "unit_embeddings.npy"
    metadata_path = root_dir / "data" / "embeddings" / "modeling_units_metadata.csv"
    results_dir = root_dir / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    print("==========================================================================")
    print("      BERTOPIC FITTING & TOPICS_PER_CLASS MULTI-CRITERIA ANALYSIS         ")
    print("==========================================================================")
    
    if not embeddings_path.exists() or not metadata_path.exists():
        print(f"[ERROR] Missing required inputs:\n  Embeddings: {embeddings_path}\n  Metadata: {metadata_path}")
        sys.exit(1)
        
    print(f"[*] Loading e5-base-v2 vector embeddings from: {embeddings_path}")
    embeddings = np.load(embeddings_path)
    print(f"    Embeddings matrix shape: {embeddings.shape}")
    
    print(f"[*] Loading enriched modeling metadata from: {metadata_path}")
    meta_df = pd.read_csv(metadata_path)
    print(f"    Metadata rows: {len(meta_df)}")
    
    required_cols = {"corpus_tier", "institutional_pillar", "locus_bucket", "logic_bucket", "grid_bucket", "digital_system_flag"}
    if not required_cols.issubset(set(meta_df.columns)):
        print("[*] Required class variables missing from metadata. Automatically running enrich_metadata_4x5...")
        try:
            import enrich_metadata_4x5
            enrich_metadata_4x5.main()
            meta_df = pd.read_csv(metadata_path)
            print(f"    Re-loaded metadata rows: {len(meta_df)}")
        except Exception as e:
            print(f"[!] Warning: Auto-enrichment failed ({e}). Some class variables may be skipped.")
    
    if len(meta_df) != embeddings.shape[0]:
        print(f"[ERROR] Row mismatch! Embeddings has {embeddings.shape[0]} rows while metadata has {len(meta_df)} rows.")
        sys.exit(1)
        
    docs = meta_df["text"].astype(str).tolist()
    
    # Configure reproducible dimensionality reduction and clustering
    print("\n[*] Initializing BERTopic with UMAP (n_neighbors=15, n_components=5, random_state=42)")
    umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=42)
    
    print("[*] Configuring HDBSCAN clustering (min_cluster_size=8)")
    hdbscan_model = HDBSCAN(min_cluster_size=8, metric="euclidean", cluster_selection_method="eom", prediction_data=True)
    
    # Configure custom vectorizer for clean domain n-grams (1-2 words) without generic stopwords
    vectorizer_model = CountVectorizer(stop_words="english", ngram_range=(1, 2), min_df=2)
    
    topic_model = BERTopic(
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        calculate_probabilities=False,
        verbose=True
    )
    
    print("\n[*] Fitting BERTopic on 610 documents using pre-computed e5-base-v2 embeddings...")
    topics, _ = topic_model.fit_transform(docs, embeddings=embeddings)
    
    topic_info = topic_model.get_topic_info()
    topic_info_path = results_dir / "bertopic_topic_info.csv"
    topic_info.to_csv(topic_info_path, index=False)
    print(f"\n[OK] BERTopic model fitted successfully! Discovered {len(topic_info) - 1} distinct topics (+ outlier class -1).")
    print(f"     Topic info saved to: {topic_info_path}")
    
    # Save document topic assignments back to metadata
    meta_df["assigned_topic"] = topics
    meta_df["topic_name"] = meta_df["assigned_topic"].map(dict(zip(topic_info["Topic"], topic_info["Name"])))
    doc_topics_path = root_dir / "data" / "embeddings" / "modeling_units_with_topics.csv"
    meta_df.to_csv(doc_topics_path, index=False)
    print(f"[OK] Document-level topic assignments saved to: {doc_topics_path}")
    
    print("\n--------------------------------------------------------------------------")
    print("Top 10 Discovered Topics:")
    print("--------------------------------------------------------------------------")
    print(topic_info[["Topic", "Count", "Name"]].head(11).to_string(index=False))
    
    # Execute topics_per_class for each target variable without re-embedding
    class_variables = [
        ("corpus_tier", "topics_per_class_corpus_tier.csv"),
        ("institutional_pillar", "topics_per_class_institutional_pillar.csv"),
        ("locus_bucket", "topics_per_class_locus_bucket.csv"),
        ("logic_bucket", "topics_per_class_logic_bucket.csv"),
        ("grid_bucket", "topics_per_class_grid_bucket.csv"),
        ("digital_system_flag", "topics_per_class_digital_system_flag.csv"),
    ]
    
    print("\n==========================================================================")
    print("         EXECUTING TOPICS_PER_CLASS ACROSS ANALYTICAL CRITERIA            ")
    print("==========================================================================")
    
    for col, fname in class_variables:
        if col not in meta_df.columns:
            print(f"[WARNING] Column '{col}' not found in metadata. Skipping.")
            continue
            
        print(f"\n[*] Re-aggregating c-TF-IDF for class variable: '{col}'...")
        classes = meta_df[col].fillna("Unknown").astype(str).tolist()
        tpc_df = topic_model.topics_per_class(docs, classes=classes)
        
        out_path = results_dir / fname
        tpc_df.to_csv(out_path, index=False)
        print(f"    [OK] Saved {len(tpc_df)} class-topic aggregations to: {out_path}")
        
        # Display summary of top 3 topics per class
        print(f"    Top topics per class in '{col}':")
        for cls_name, grp in tpc_df[tpc_df["Topic"] != -1].groupby("Class"):
            top_topics = grp.sort_values(by="Frequency", ascending=False).head(2)
            desc_list = [f"Topic {r['Topic']} ({r['Frequency']} docs): {r['Words'].split(',')[0] if isinstance(r['Words'], str) else ''}" for _, r in top_topics.iterrows()]
            print(f"      -> {cls_name} [{len(grp)} active topics]: {' | '.join(desc_list)}")

    print("\n==========================================================================")
    print("[OK] BERTopic multi-criteria topics_per_class analysis complete!")
    print("==========================================================================")


if __name__ == "__main__":
    main()
