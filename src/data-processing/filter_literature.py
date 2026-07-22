import pandas as pd
import numpy as np
from pathlib import Path

def main():
    root = Path(".")
    metadata_path = root / "data" / "embeddings" / "modeling_units_metadata.csv"
    embeddings_path = root / "data" / "embeddings" / "unit_embeddings.npy"
    registry_path = root / "data" / "master_registry.csv"
    
    metadata = pd.read_csv(metadata_path)
    embeddings = np.load(embeddings_path)
    registry = pd.read_csv(registry_path)
    
    # Identify literature docs
    lit_docs = registry[registry['corpus_role'] == 'background-literature']['doc_id'].tolist()
    
    # Find units belonging to these docs
    invalid_mask = metadata['parent_doc_id'].isin(lit_docs)
    num_dropped = invalid_mask.sum()
    
    if num_dropped > 0:
        print(f"Dropping {num_dropped} units that are background literature.")
        filtered_metadata = metadata[~invalid_mask].copy()
        filtered_embeddings = embeddings[(~invalid_mask).values]
        
        filtered_metadata.to_csv(metadata_path, index=False)
        np.save(embeddings_path, filtered_embeddings)
        print(f"Saved cleaned matrices. Remaining units: {len(filtered_metadata)}")
    else:
        print("No literature units found in the current matrix.")

if __name__ == "__main__":
    main()
