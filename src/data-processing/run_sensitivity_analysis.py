import pandas as pd
import numpy as np
from pathlib import Path
import sys

try:
    from bertopic import BERTopic
    from umap import UMAP
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import CountVectorizer
except ImportError:
    pass

def main():
    root = Path(".")
    metadata_path = root / "data" / "embeddings" / "modeling_units_metadata.csv"
    embeddings_path = root / "data" / "embeddings" / "unit_embeddings.npy"
    registry_path = root / "data" / "master_registry.csv"
    
    meta_df = pd.read_csv(metadata_path)
    embeddings = np.load(embeddings_path)
    reg_df = pd.read_csv(registry_path)
    
    # Merge tier information
    meta_df = pd.merge(meta_df, reg_df[['doc_id', 'scale_tier_v2']], left_on='parent_doc_id', right_on='doc_id', how='left')
    
    # Filter for sensitivity: Only Corpus A + Corpus B (Tier 1-3)
    # Tier 1-3 means scale_tier_v2 contains "Tier 1" or "Tier 2" or "Tier 3"
    valid_idx = meta_df['corpus_tier'].eq('A') | meta_df['scale_tier_v2'].str.contains('Tier 1|Tier 2|Tier 3', na=False)
    
    subset_df = meta_df[valid_idx].copy()
    subset_embeddings = embeddings[valid_idx.values]
    
    docs = subset_df["text"].astype(str).tolist()
    
    umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=42)
    hdbscan_model = HDBSCAN(min_cluster_size=8, metric="euclidean", cluster_selection_method="eom", prediction_data=True)
    vectorizer_model = CountVectorizer(stop_words="english", ngram_range=(1, 2), min_df=2)
    
    topic_model = BERTopic(
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        calculate_probabilities=False,
        verbose=True
    )
    
    print(f"Fitting on subset of {len(docs)} documents (Tier 1-3 + Corpus A)...")
    topics, _ = topic_model.fit_transform(docs, embeddings=subset_embeddings)
    
    topic_info = topic_model.get_topic_info()
    
    # Count topics in subset
    subset_topic_count = len(topic_info) - 1
    
    # Read the full run topic count
    full_topic_info = pd.read_csv(root / "data" / "results" / "bertopic_topic_info.csv")
    full_topic_count = len(full_topic_info) - 1
    
    # Write robustness results
    out_df = pd.DataFrame([
        {"model": "Full Data", "topic_count": full_topic_count, "unit_count": len(meta_df)},
        {"model": "Sensitivity Subset (Tier 1-3 + A)", "topic_count": subset_topic_count, "unit_count": len(subset_df)}
    ])
    
    out_path = root / "data" / "results" / "rq_robustness_sensitivity.csv"
    out_df.to_csv(out_path, index=False)
    print("Saved rq_robustness_sensitivity.csv")
    
    conclusion = "The pattern is robust to scale attribution." if abs(subset_topic_count - full_topic_count) <= 3 else "Scale conditions the landscape."
    print("Write-up sentence:", conclusion)

if __name__ == "__main__":
    main()
