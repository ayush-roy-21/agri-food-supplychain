import pandas as pd
import numpy as np
from pathlib import Path

def main():
    root = Path(".")
    
    # 1. Purge from Master Registry
    registry_path = root / "data" / "master_registry.csv"
    registry = pd.read_csv(registry_path)
    
    drop_mask = registry['doc_id'].isin([
        'A-CSR-100', 'A-CSR-101', 'A-CSR-102',
        'A-EUDR-100', 'A-EUDR-102',
        'B-REDDIT-001', 'B-REDDIT-002', 'B-REDDIT-003'  # Reddit stubs already removed
    ]) | registry['doc_id'].str.contains('REDDIT')
    docs_to_drop = registry[drop_mask]['doc_id'].tolist()
    print(f"Found {len(docs_to_drop)} documents to purge: {docs_to_drop}")
    
    registry_clean = registry[~drop_mask].copy()
    registry_clean.to_csv(registry_path, index=False)
    print(f"Purged master_registry.csv. New length: {len(registry_clean)}")
    
    # 2. Purge from Modeling Matrices
    metadata_path = root / "data" / "embeddings" / "modeling_units_metadata.csv"
    embeddings_path = root / "data" / "embeddings" / "unit_embeddings.npy"
    
    metadata = pd.read_csv(metadata_path)
    embeddings = np.load(embeddings_path)
    
    unit_drop_mask = metadata['parent_doc_id'].isin(docs_to_drop)
    units_to_drop = metadata[unit_drop_mask]['unit_id'].tolist()
    print(f"Found {len(units_to_drop)} units to purge from matrices.")
    
    metadata_clean = metadata[~unit_drop_mask].copy()
    embeddings_clean = embeddings[(~unit_drop_mask).values]
    
    metadata_clean.to_csv(metadata_path, index=False)
    np.save(embeddings_path, embeddings_clean)
    
    print(f"Purged modeling matrices. New units length: {len(metadata_clean)}")

if __name__ == "__main__":
    main()
