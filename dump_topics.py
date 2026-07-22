import pandas as pd
import json

df = pd.read_csv('data/results/bertopic_topic_info.csv')
with open('topic_dump.txt', 'w', encoding='utf-8') as f:
    for i, row in df.iterrows():
        f.write(f"Topic {row['Topic']}: {row['Name']} (Count: {row['Count']})\n")
        docs = eval(row['Representative_Docs'])
        for idx, d in enumerate(docs[:3]):
            f.write(f"  Doc {idx+1}: {d[:500].replace(chr(10), ' ')}\n")
        f.write("-" * 80 + "\n")
