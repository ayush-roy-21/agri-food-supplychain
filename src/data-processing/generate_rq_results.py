import pandas as pd
import numpy as np
from pathlib import Path
from itertools import combinations
from collections import defaultdict

def main():
    root = Path(".")
    units_df = pd.read_csv(root / "data" / "embeddings" / "modeling_units_with_topics.csv")
    meta_df = pd.read_csv(root / "data" / "master_registry.csv")
    topic_map = pd.read_csv(root / "data" / "results" / "topic_locus_mapping.csv")
    
    # Drop outlier topic if any
    topic_map = topic_map[topic_map['Topic'] != -1]
    
    # units_df already contains corpus_tier, verification_logic, and institutional_pillar.
    df = units_df.merge(topic_map[['Topic', 'hurdle_name', 'locus_primary']], left_on='assigned_topic', right_on='Topic', how='inner')
    
    # --- RQ1 ---
    rq1_records = []
    for hurdle in df['hurdle_name'].unique():
        h_df = df[df['hurdle_name'] == hurdle]
        locus = h_df['locus_primary'].iloc[0]
        u_count = len(h_df)
        a_count = len(h_df[h_df['corpus_tier'] == 'A'])
        b_count = len(h_df[h_df['corpus_tier'] == 'B'])
        
        logics = h_df['verification_logic'].dropna().unique()
        # Drop not-applicable if present
        logics = [l for l in logics if str(l).lower() != 'not-applicable']
        scope = 'structural' if len(logics) > 1 else 'specific'
        
        rq1_records.append({
            'hurdle': hurdle,
            'locus': locus,
            'unit_count': u_count,
            'corpus_a_count': a_count,
            'corpus_b_count': b_count,
            'scope': scope
        })
    rq1 = pd.DataFrame(rq1_records)
    rq1.to_csv(root / "data" / "results" / "rq1_locus_distribution.csv", index=False)
    print("Generated RQ1: rq1_locus_distribution.csv")
    
    # --- RQ2 ---
    # Co-occurrence at parent-document level
    doc_hurdles = df.groupby('parent_doc_id')['hurdle_name'].apply(lambda x: list(set(x))).to_dict()
    
    pair_counts = defaultdict(int)
    doc_pair_map = defaultdict(list)
    hurdle_doc_count = defaultdict(int)
    
    for doc, hurdles in doc_hurdles.items():
        for h in hurdles:
            hurdle_doc_count[h] += 1
        for h1, h2 in combinations(sorted(hurdles), 2):
            pair = (h1, h2)
            pair_counts[pair] += 1
            if len(doc_pair_map[pair]) < 3:
                doc_pair_map[pair].append(doc)
                
    rq2_records = []
    for pair, count in pair_counts.items():
        h1, h2 = pair
        jaccard = count / (hurdle_doc_count[h1] + hurdle_doc_count[h2] - count)
        rq2_records.append({
            'hurdle_a': h1,
            'hurdle_b': h2,
            'co_occurrence_count': count,
            'jaccard': round(jaccard, 4),
            'example_doc_ids': ", ".join(doc_pair_map[pair])
        })
    rq2 = pd.DataFrame(rq2_records)
    if not rq2.empty:
        rq2 = rq2.sort_values(by='co_occurrence_count', ascending=False)
    else:
        rq2 = pd.DataFrame(columns=['hurdle_a', 'hurdle_b', 'co_occurrence_count', 'jaccard', 'example_doc_ids'])
    rq2.to_csv(root / "data" / "results" / "rq2_hurdle_cooccurrence.csv", index=False)
    print("Generated RQ2: rq2_hurdle_cooccurrence.csv")
    
    # --- RQ3 ---
    def assign_actor(row):
        pillar = str(row.get('institutional_pillar', '')).lower()
        if 'fda' in pillar or 'apeda' in pillar or 'mpeda' in pillar or 'fssai' in pillar or 'statutory' in pillar or 'dgft' in pillar or 'eic' in pillar or 'eu ' in pillar:
            return 'regulator'
        elif 'media' in pillar:
            return 'media'
        else:
            return 'firm'
            
    meta_df['actor_type'] = meta_df.apply(assign_actor, axis=1)
    
    df_act = pd.merge(df, meta_df[['doc_id', 'actor_type']], left_on='parent_doc_id', right_on='doc_id', how='left')
    rq3_records = []
    for hurdle in df_act['hurdle_name'].unique():
        h_df = df_act[df_act['hurdle_name'] == hurdle]
        for actor in h_df['actor_type'].dropna().unique():
            a_count = len(h_df[h_df['actor_type'] == actor])
            rq3_records.append({
                'hurdle_name': hurdle,
                'actor_type': actor,
                'unit_count': a_count,
                'paraphrased_framing': "Simulated framing for this actor."
            })
    rq3 = pd.DataFrame(rq3_records)
    rq3.to_csv(root / "data" / "results" / "rq3_actor_framing.csv", index=False)
    print("Generated RQ3: rq3_actor_framing.csv")

if __name__ == "__main__":
    main()
