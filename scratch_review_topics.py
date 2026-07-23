import pandas as pd
import ast

topic_info = pd.read_csv('data/results/bertopic_topic_info.csv')
units = pd.read_csv('data/embeddings/modeling_units_with_topics.csv')
meta = pd.read_csv('data/master_registry.csv')

topics_to_review = [-1, 0, 2, 3, 4, 6, 7, 8, 10, 11, 12, 14]

with open('topic_review_notes.txt', 'w', encoding='utf-8') as f:
    for t in topics_to_review:
        row = topic_info[topic_info['Topic'] == t].iloc[0]
        f.write(f"\n\n=== TOPIC {t}: {row['Name']} ===\n")
        # Get the units assigned to this topic
        t_units = units[units['assigned_topic'] == t]
        # Get unique parent doc ids
        doc_ids = t_units['parent_doc_id'].unique()[:5]
        f.write(f"Docs: {list(doc_ids)}\n")
        
        # Try to parse Representative_Docs
        if 'Representative_Docs' in row and pd.notna(row['Representative_Docs']):
            try:
                docs = ast.literal_eval(row['Representative_Docs'])
                for i, d in enumerate(docs[:3]):
                    f.write(f"  Doc {i+1}: {d[:400]}...\n")
            except Exception as e:
                f.write(f"  Could not parse docs: {e}\n")
