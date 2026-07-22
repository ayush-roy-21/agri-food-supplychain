import pandas as pd
import ast

df = pd.read_csv('data/results/bertopic_topic_info.csv')
with open('topic_evidence.md', 'w', encoding='utf-8') as f:
    for idx, row in df.iterrows():
        f.write(f"## Topic {row['Topic']}: {row['Name']}\n")
        try:
            docs = ast.literal_eval(row['Representative_Docs'])
            for i, doc in enumerate(docs[:5]):
                f.write(f"- Doc {i+1}:\n{doc[:400]}...\n\n")
        except:
            f.write("No representative docs found.\n\n")
