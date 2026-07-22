import pandas as pd
import numpy as np
from pathlib import Path
import csv
from datetime import datetime

def is_noise(topic_name):
    topic_name = str(topic_name).lower()
    
    scraper_noise = ['comments', 'download', 'pdf', 'format', 'subscribe', 'author', 'user', 'sir', 'print', 'related articles', 'english', 'news']
    earnings_noise = ['company results', 'fy26', 'growth', 'profit', 'quarterly', 'shares']
    
    # Check if any noise keywords are present in the topic name
    # The topic name is typically something like "1_author_user_sir_iec"
    words = topic_name.replace('_', ' ').split()
    for w in words:
        if w in scraper_noise or w in earnings_noise:
            return True
    
    # Also check full string matching for multi-word phrases
    for w in scraper_noise + earnings_noise:
        if w in topic_name:
            return True
            
    return False

def main():
    root = Path(".")
    topic_info = pd.read_csv(root / "data" / "results" / "bertopic_topic_info.csv")
    units_with_topics = pd.read_csv(root / "data" / "embeddings" / "modeling_units_with_topics.csv")
    metadata = pd.read_csv(root / "data" / "embeddings" / "modeling_units_metadata.csv")
    embeddings = np.load(root / "data" / "embeddings" / "unit_embeddings.npy")
    
    noisy_topics = []
    for idx, row in topic_info.iterrows():
        if row['Topic'] == -1:
            continue
        if is_noise(row['Name']):
            noisy_topics.append(row['Topic'])
            
    if not noisy_topics:
        print("No noise topics found! Clean.")
        return
        
    print(f"Found noisy topics: {noisy_topics}")
    
    # Get units to drop
    noisy_units = units_with_topics[units_with_topics['assigned_topic'].isin(noisy_topics)]['unit_id'].tolist()
    print(f"Dropping {len(noisy_units)} units due to noise.")
    
    # Log to exceptions_log.csv
    with open(root / "data" / "exceptions_log.csv", 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for u in noisy_units:
            writer.writerow([u, datetime.today().strftime('%Y-%m-%d'), 'preprocessing-noise', 'BERTopic noise gate'])
            
    # Filter metadata and embeddings
    valid_mask = ~metadata['unit_id'].isin(noisy_units)
    filtered_metadata = metadata[valid_mask].copy()
    filtered_embeddings = embeddings[valid_mask.values]
    
    filtered_metadata.to_csv(root / "data" / "embeddings" / "modeling_units_metadata.csv", index=False)
    np.save(root / "data" / "embeddings" / "unit_embeddings.npy", filtered_embeddings)
    
    print(f"Saved cleaned matrices. Remaining units: {len(filtered_metadata)}")

if __name__ == "__main__":
    main()
