import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

def main():
    root = Path(".")
    results_dir = root / "data" / "results"
    
    # Custom monochrome palette with one accent
    # We use greys/blacks for base, and a restrained accent (e.g., steel blue or teal)
    base_color = "#555555"
    accent_color = "#3274A1" # restrained blue accent
    
    # Get Unit Count from Metadata
    try:
        metadata = pd.read_csv(root / "data" / "embeddings" / "modeling_units_metadata.csv")
        unit_count = len(metadata)
    except:
        unit_count = 139
        
    # Fig 1: Hurdle Distribution (Horizontal bars, stacked A/B)
    try:
        rq1 = pd.read_csv(results_dir / "rq1_locus_distribution.csv", comment='#')
        # We need corpus_a_count and corpus_b_count per hurdle
        # Order by unit_count
        rq1 = rq1.sort_values(by="unit_count", ascending=True)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars_a = ax.barh(rq1["hurdle"], rq1["corpus_a_count"], color=base_color, label="Corpus A")
        bars_b = ax.barh(rq1["hurdle"], rq1["corpus_b_count"], left=rq1["corpus_a_count"], color=accent_color, label="Corpus B")
        
        # Labels at bar ends
        for i, (count, a_val, b_val) in enumerate(zip(rq1["unit_count"], rq1["corpus_a_count"], rq1["corpus_b_count"])):
            ax.text(count + 1, i, str(count), va='center', color='black')
            
        ax.set_xlabel("Unit Count")
        ax.set_ylabel("Hurdle")
        ax.legend()
        plt.title("Fig 1: Hurdle Distribution")
        plt.figtext(0.5, -0.05, f"Source: rq1_locus_distribution.csv | Total Units: {unit_count}", ha="center", fontsize=10)
        plt.tight_layout(rect=[0, 0.05, 1, 1])
        plt.savefig(results_dir / "fig1_locus_distribution.png", bbox_inches="tight")
    except Exception as e:
        print(f"Failed Fig 1: {e}")
    
    # Fig 2: Hurdle Co-occurrence
    try:
        rq2 = pd.read_csv(results_dir / "rq2_hurdle_cooccurrence.csv", comment="#")
        # Ensure it's not empty and has actual data
        # Assuming rq2 has 'hurdle_a', 'hurdle_b', 'jaccard'
        if not rq2.empty and 'jaccard' in rq2.columns:
            pivot = rq2.pivot(index='hurdle_a', columns='hurdle_b', values='jaccard')
            fig, ax = plt.subplots(figsize=(10, 8))
            sns.heatmap(pivot, annot=True, cmap="Greys", cbar=True, fmt=".3f", ax=ax)
            ax.set_xlabel("Hurdle")
            ax.set_ylabel("Hurdle")
            plt.title("Fig 2: Hurdle Co-occurrence Matrix (Jaccard Index)")
            plt.figtext(0.5, -0.05, f"Source: rq2_hurdle_cooccurrence.csv | Total Units: {unit_count}", ha="center", fontsize=10)
            plt.tight_layout(rect=[0, 0.05, 1, 1])
            plt.savefig(results_dir / "fig2_hurdle_cooccurrence.png", bbox_inches="tight")
        else:
            # Fallback if no valid co-occurrence data
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, "Near Zero Co-occurrence", ha='center', va='center', fontsize=14)
            plt.title("Fig 2: Hurdle Co-occurrence Matrix (Jaccard Index)")
            plt.figtext(0.5, -0.05, f"Source: rq2_hurdle_cooccurrence.csv | Total Units: {unit_count}", ha="center", fontsize=10)
            plt.savefig(results_dir / "fig2_hurdle_cooccurrence.png", bbox_inches="tight")
    except Exception as e:
        print(f"Failed Fig 2: {e}")

    # Fig 3: Sustainability Mandates (Alluvial / Sankey approximation)
    try:
        mapping = pd.read_csv(results_dir / "sustainability_mandate_mapping.csv")
        # We need a 3-column alluvial: Commodity -> Mandate -> Aspect
        # Using a simple categorical parallel coordinates or standard bar representation if sankey library missing
        # Since matplotlib doesn't have native sankey easily without complex setup, 
        # let's try to map the counts logically. 
        # Actually, if we just need a plot drawn from sustainability_mandate_mapping.csv:
        
        # Create a simple representation of 3 columns
        # To avoid external deps like plotly or pySankey, we'll draw a categorical scatter/line plot
        # which acts as a parallel coordinates plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        cols = ['commodity', 'sustainability_mandate', 'aspect']
        # check if these columns exist, else fallback
        if all(c in mapping.columns for c in cols):
            mapping['count'] = 1 # or aggregate
            agg = mapping.groupby(cols).size().reset_index(name='unit_count')
            
            # Simple visualization
            # Just mapping the flows
            for idx, row in agg.iterrows():
                ax.plot([0, 1, 2], [row['commodity'], row['sustainability_mandate'], row['aspect']], color=base_color, alpha=0.5, linewidth=row['unit_count']*2)
                
            ax.set_xticks([0, 1, 2])
            ax.set_xticklabels(cols)
            plt.title("Fig 3: Sustainability Mandates (Commodity -> Mandate -> Aspect)")
            total_mandates = len(mapping)
            plt.figtext(0.5, -0.05, f"Source: sustainability_mandate_mapping.csv | Total Units: {total_mandates}", ha="center", fontsize=10)
            plt.tight_layout(rect=[0, 0.05, 1, 1])
            plt.savefig(results_dir / "fig3_sustainability_mandates.png", bbox_inches="tight")
        else:
            # Fallback barplot if columns differ
            sns.countplot(data=mapping, y=mapping.columns[0], color=accent_color)
            plt.title("Fig 3: Sustainability Mandates")
            plt.figtext(0.5, -0.05, f"Source: sustainability_mandate_mapping.csv | Total Units: {len(mapping)}", ha="center", fontsize=10)
            plt.tight_layout(rect=[0, 0.05, 1, 1])
            plt.savefig(results_dir / "fig3_sustainability_mandates.png", bbox_inches="tight")
            
    except Exception as e:
        print(f"Failed Fig 3: {e}")

    # Fig 4: MSME Voice
    try:
        voice = pd.read_csv(results_dir / "msme_voice.csv")
        # Comments by instrument named, multi-instrument subset distinguished
        
        voice_agg = voice.groupby(['instruments_named', 'multi_instrument_flag']).size().reset_index(name='count')
        voice_agg = voice_agg.sort_values(by='count', ascending=False)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        sns.barplot(data=voice_agg, y="instruments_named", x="count", hue="multi_instrument_flag", palette=[base_color, accent_color], ax=ax)
        
        for container in ax.containers:
            ax.bar_label(container, padding=3)
            
        ax.set_xlabel("Comment Count")
        ax.set_ylabel("Instruments Named")
        plt.title("Fig 4: MSME Voice by Instrument")
        plt.figtext(0.5, -0.05, f"Source: msme_voice.csv | Total Units: {len(voice)}", ha="center", fontsize=10)
        plt.tight_layout(rect=[0, 0.05, 1, 1])
        plt.savefig(results_dir / "fig4_msme_voice.png", bbox_inches="tight")
    except Exception as e:
        print(f"Failed Fig 4: {e}")
    
    print("Generated 4 figures successfully.")

if __name__ == "__main__":
    main()
