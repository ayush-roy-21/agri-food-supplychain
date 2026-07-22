import pandas as pd

topic_info = pd.read_csv('data/results/bertopic_topic_info.csv')
units = pd.read_csv('data/embeddings/modeling_units_with_topics.csv')

with open('topic_evidence_real.md', 'w', encoding='utf-8') as f:
    for idx, row in topic_info.iterrows():
        topic = row['Topic']
        name = row['Name']
        f.write(f"## Topic {topic}: {name}\n")
        topic_units = units[units['assigned_topic'] == topic]
        docs = topic_units.drop_duplicates(subset=['parent_doc_id']).head(10)
        for _, doc_row in docs.iterrows():
            f.write(f"- Doc ID: {doc_row['parent_doc_id']}\n")
            text = str(doc_row['text'])[:600]
            f.write(f"- Text Snippet:\n{text}...\n\n")
        f.write("---\n")
