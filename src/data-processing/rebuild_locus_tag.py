import pandas as pd
from pathlib import Path
from collections import Counter

def main():
    root = Path(".")
    reg_path = root / "data" / "master_registry.csv"
    units_path = root / "data" / "embeddings" / "modeling_units_with_topics.csv"
    mapping_path = root / "data" / "results" / "topic_locus_mapping.csv"
    
    reg_df = pd.read_csv(reg_path)
    units_df = pd.read_csv(units_path)
    mapping_df = pd.read_csv(mapping_path)
    
    # Priority order for tie-breaking (rarest first gets higher priority)
    priority = {
        'informational-verifiability': 4,
        'relational-power': 3,
        'internal-capability': 2,
        'institutional-voids': 1,
        'inductive-other': 0
    }
    
    # Create topic to valid loci dictionary (combining primary and secondary)
    topic_to_loci = {}
    for _, row in mapping_df.iterrows():
        topic = row['Topic']
        loci = []
        if pd.notna(row['locus_primary']) and row['locus_primary'] != 'not-applicable':
            loci.append(row['locus_primary'])
        if pd.notna(row['locus_secondary']) and row['locus_secondary'] != 'not-applicable':
            loci.append(row['locus_secondary'])
        topic_to_loci[topic] = loci
        
    allowed_loci = {'internal-capability', 'relational-power', 'institutional-voids', 'informational-verifiability'}
    
    # Calculate dominant valid locus per parent_doc_id across all its chunks' topics
    doc_locus_map = {}
    for doc_id, group in units_df.groupby('parent_doc_id'):
        all_loci = []
        for topic in group['assigned_topic']:
            if pd.notna(topic) and topic in topic_to_loci:
                all_loci.extend(topic_to_loci[topic])
        
        # Filter for only allowed core valid loci
        valid_loci = [l for l in all_loci if l in allowed_loci]
        
        if valid_loci:
            # Count loci
            counts = Counter(valid_loci)
            # Find the max count
            max_count = max(counts.values())
            # Find all loci that have the max count
            top_loci = [locus for locus, count in counts.items() if count == max_count]
            # Tie-break using priority
            best_locus = max(top_loci, key=lambda x: priority.get(x, -1))
            doc_locus_map[doc_id] = best_locus
        else:
            if all_loci:
                doc_locus_map[doc_id] = Counter(all_loci).most_common(1)[0][0]
                
    updated_count = 0
    for idx, row in reg_df.iterrows():
        doc_id = row['doc_id']
        new_locus = doc_locus_map.get(doc_id)
        if new_locus:
            reg_df.at[idx, 'locus_tag'] = new_locus
            updated_count += 1
        else:
            # If document missing from units or has no valid topics, fallback ONLY IF it doesn't already have a valid tag
            if row['locus_tag'] not in allowed_loci:
                reg_df.at[idx, 'locus_tag'] = 'inductive-other'
            
    reg_df.to_csv(reg_path, index=False)
    
    print(f"Updated {updated_count} rows with mapped locus_tags.")
    print("Frequency count of locus_tag:")
    freq = reg_df['locus_tag'].value_counts()
    print(freq)
    
    for val in allowed_loci:
        if val not in freq.index or freq[val] == 0:
            print(f"[!] Warning: Structural failure! Valid locus sits at 0%: {val}")

if __name__ == "__main__":
    main()
