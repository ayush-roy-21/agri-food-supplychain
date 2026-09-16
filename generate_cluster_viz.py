import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import ast
from pathlib import Path

def plot_bertopic_barchart(topic_info_path, output_path):
    df = pd.read_csv(topic_info_path)
    
    # Filter out noise topic (-1)
    df = df[df['Topic'] != -1]
    
    n_topics = len(df)
    
    fig, axes = plt.subplots(1, n_topics, figsize=(5 * n_topics, 6), sharey=False)
    if n_topics == 1:
        axes = [axes]
        
    for i, (idx, row) in enumerate(df.iterrows()):
        topic_id = row['Topic']
        count = row['Count']
        
        # Parse the representation string into a list of words
        try:
            words = ast.literal_eval(row['Representation'])
        except:
            words = str(row['Representation']).strip("[]").replace("'", "").split(", ")
            
        # We don't have the c-TF-IDF scores in topic_info out of the box, 
        # but we can just plot the words uniformly or extract scores if available.
        # Since we just have the words in order of importance, we can assign dummy descending weights
        # to simulate a bar chart of importance.
        weights = list(range(len(words), 0, -1))
        
        ax = axes[i]
        sns.barplot(x=weights, y=words, ax=ax, color="#3274A1")
        
        ax.set_title(f"Topic {topic_id} (N={count})", fontsize=14)
        ax.set_xlabel("Importance Rank (Descending)")
        ax.set_xticks([]) # Hide x ticks as they are just ranks
        
        # Adjust spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

    plt.suptitle("BERTopic Cluster Visualization: Key Terms per Topic", fontsize=18, y=1.05)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', dpi=150)
    print(f"Saved visualization to {output_path}")

if __name__ == "__main__":
    root = Path(".")
    topic_info = root / "data" / "results" / "bertopic_topic_info.csv"
    output = root / "data" / "results" / "bertopic_cluster_keywords.png"
    plot_bertopic_barchart(topic_info, output)
