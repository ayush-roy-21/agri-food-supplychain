import pandas as pd
from pathlib import Path

def main():
    root = Path(".")
    reg_path = root / "data" / "master_registry.csv"
    units_path = root / "data" / "embeddings" / "modeling_units_with_topics.csv"
    mapping_path = root / "data" / "results" / "topic_locus_mapping.csv"
    
    reg_df = pd.read_csv(reg_path)
    units_df = pd.read_csv(units_path)
    mapping_df = pd.read_csv(mapping_path)
    
    # Create topic to locus dictionary
    topic_to_locus = dict(zip(mapping_df['Topic'], mapping_df['locus_primary']))
    
    # Calculate dominant topic per parent_doc_id
    # We find the mode of assigned_topic for each parent_doc_id
    doc_topics = units_df.groupby('parent_doc_id')['assigned_topic'].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else None).to_dict()
    
    # Update locus_tag
    allowed_loci = {'internal-capability', 'relational-power', 'institutional-voids', 'informational-verifiability', 'inductive-other'}
    
    updated_count = 0
    for idx, row in reg_df.iterrows():
        doc_id = row['doc_id']
        topic = doc_topics.get(doc_id)
        if pd.notna(topic) and topic in topic_to_locus:
            new_locus = topic_to_locus[topic]
            reg_df.at[idx, 'locus_tag'] = new_locus
            updated_count += 1
        else:
            # If a document doesn't have a topic (e.g., dropped as noise, or no units), 
            # we must still overwrite it, perhaps with inductive-other.
            reg_df.at[idx, 'locus_tag'] = 'inductive-other'
            
    reg_df.to_csv(reg_path, index=False)
    
    print(f"Updated {updated_count} rows with mapped locus_tags.")
    print("Frequency count of locus_tag:")
    freq = reg_df['locus_tag'].value_counts()
    print(freq)
    
    for val in freq.index:
        if val not in allowed_loci:
            print(f"[!] Warning: Invalid locus found: {val}")

if __name__ == "__main__":
    main()
