import pandas as pd
import itertools
from collections import defaultdict
from pathlib import Path

def main():
    data_dir = Path("data")
    results_dir = data_dir / "results"
    
    # Load units
    units_df = pd.read_csv(data_dir / "embeddings" / "modeling_units_with_topics.csv")
    
    # Filter out noise (-1)
    df = units_df[units_df["assigned_topic"] != -1].copy()
    
    # Group topics by parent_doc_id
    doc_topics = df.groupby("parent_doc_id")["assigned_topic"].apply(lambda x: list(set(x))).to_dict()
    
    # Count co-occurrences
    cooccur = defaultdict(int)
    topic_doc_counts = defaultdict(int)
    
    for doc, topics in doc_topics.items():
        for t in topics:
            topic_doc_counts[t] += 1
        
        # pairs
        for t1, t2 in itertools.combinations(sorted(topics), 2):
            cooccur[(t1, t2)] += 1
            
    # Calculate Jaccard and raw count
    rows = []
    for (t1, t2), count in cooccur.items():
        jaccard = count / (topic_doc_counts[t1] + topic_doc_counts[t2] - count)
        rows.append({
            "topic_a": t1,
            "topic_b": t2,
            "raw_cooccurrence_count": count,
            "jaccard_similarity": round(jaccard, 4)
        })
        
    res_df = pd.DataFrame(rows).sort_values("raw_cooccurrence_count", ascending=False)
    res_df.to_csv(results_dir / "rq2_hurdle_cooccurrence.csv", index=False)
    print("Generated rq2_hurdle_cooccurrence.csv")

if __name__ == "__main__":
    main()
