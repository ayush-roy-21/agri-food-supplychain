import pandas as pd
import numpy as np
from pathlib import Path
import csv
import datetime

def main():
    root = Path(".")
    metadata_path = root / "data" / "embeddings" / "modeling_units_metadata.csv"
    embeddings_path = root / "data" / "embeddings" / "unit_embeddings.npy"
    topics_path = root / "data" / "embeddings" / "modeling_units_with_topics.csv"
    decision_log_path = root / "data" / "decision_log.csv"
    
    metadata = pd.read_csv(metadata_path)
    embeddings = np.load(embeddings_path)
    topics = pd.read_csv(topics_path)
    
    # Prefixes to exclude
    prefixes_to_exclude = [
        "A-RES-",    # SupplyChain_Research
        "A-MOFPI-",  # MoFPI_PIB
        "A-ZED-",    # NITI_MSME
        "A-DATA-",   # DataGov
        "A-CSR-",    # CSR
        "A-EUMOFA-", # EUMOFA
        "A-EFSA-"    # EFSA
    ]
    
    # Create mask
    drop_mask = metadata['parent_doc_id'].str.startswith(tuple(prefixes_to_exclude))
    units_to_drop = metadata[drop_mask]['unit_id'].tolist()
    
    print(f"Found {len(units_to_drop)} units to exclude from matrices.")
    
    # Filter
    metadata_clean = metadata[~drop_mask].copy()
    embeddings_clean = embeddings[(~drop_mask).values]
    
    # Also filter topics file by unit_id
    topics_drop_mask = topics['unit_id'].isin(units_to_drop)
    topics_clean = topics[~topics_drop_mask].copy()
    
    # Save
    metadata_clean.to_csv(metadata_path, index=False)
    np.save(embeddings_path, embeddings_clean)
    topics_clean.to_csv(topics_path, index=False)
    
    print(f"Purged {len(units_to_drop)} units. New metadata length: {len(metadata_clean)}")
    print(f"New embeddings shape: {embeddings_clean.shape}")
    print(f"New topics length: {len(topics_clean)}")
    
    # Update decision log
    entry = [
        "DEC-2026-038",
        datetime.datetime.now().strftime("%Y-%m-%d"),
        "institutional-scope-narrowing",
        "SupplyChain_Research, MoFPI_PIB, NITI_MSME, DataGov, CSR, EUMOFA, EFSA",
        "Excluded pillars from hurdle-modeling matrix because they lack authority to withhold, suspend, or revoke something an exporter needs.",
        "institutional-scope-exclusion",
        "Antigravity Agent"
    ]
    
    with open(decision_log_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(entry)
    print("Added entry to decision_log.csv.")

if __name__ == "__main__":
    main()
