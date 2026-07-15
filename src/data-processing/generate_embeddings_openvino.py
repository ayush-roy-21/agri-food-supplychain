"""
generate_embeddings_openvino.py

Accelerated embedding generation for intfloat/e5-base-v2 on local Intel GPUs
(e.g., Intel Iris Xe) using OpenVINO (optimum.intel + openvino).

Reads the 515 assembled modeling units from:
    data/embeddings/modeling_units_metadata.csv
Generates normalized 768-dimensional embeddings via OpenVINO on Intel GPU:
    data/embeddings/unit_embeddings.npy

Usage:
    python src/data-processing/generate_embeddings_openvino.py
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METADATA_PATH = PROJECT_ROOT / "data" / "embeddings" / "modeling_units_metadata.csv"
EMBED_OUTPUT_PATH = PROJECT_ROOT / "data" / "embeddings" / "unit_embeddings.npy"
MODEL_ID = "intfloat/e5-base-v2"


def main():
    print("==========================================================================")
    print("   OPENVINO ACCELERATED E5-BASE-V2 EMBEDDING GENERATOR (INTEL IRIS XE)    ")
    print("==========================================================================")

    try:
        import torch
        import torch.nn.functional as F
        from transformers import AutoTokenizer
        from optimum.intel import OVModelForFeatureExtraction
    except ImportError as e:
        print(f"[ERROR] Missing required OpenVINO/PyTorch packages: {e}")
        print("Please install:\n    pip install torch transformers optimum[openvino] openvino")
        sys.exit(1)

    print("[*] Assembling clean modeling units from chunk_manifest and master_registry...")
    try:
        from generate_embeddings import assemble_modeling_units
    except ImportError:
        sys.path.append(str(Path(__file__).resolve().parent))
        from generate_embeddings import assemble_modeling_units

    df_units, skipped = assemble_modeling_units()
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_units.to_csv(METADATA_PATH, index=False)
    
    # --- Run metadata enrichment so modeling_units_metadata.csv has canonical 4x5 grid & institutional pillars ---
    try:
        import enrich_metadata_4x5
        enrich_metadata_4x5.main()
        df_units = pd.read_csv(METADATA_PATH)
    except Exception as e:
        print(f"[!] Warning: Metadata enrichment step failed or missing ({e}). Proceeding with base metadata.")

    n_docs = len(df_units)
    print(f"[*] Saved {n_docs} pristine modeling units to {METADATA_PATH}")
    if skipped:
        print(f"    (Excluded {len(skipped)} noisy/corrupt units during assembly)")

    # E5 models specifically require the 'passage: ' prefix for symmetric clustering
    raw_texts = df_units["text"].astype(str).tolist()
    formatted_docs = [f"passage: {doc}" for doc in raw_texts]

    print(f"\n[*] Initializing AutoTokenizer for {MODEL_ID}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

    print("[*] Loading OVModelForFeatureExtraction (export=True for OpenVINO IR conversion)...")
    print("    (If running for the first time, this downloads/converts the model weights)")
    model = OVModelForFeatureExtraction.from_pretrained(MODEL_ID, export=True)

    print("[*] Targeting local Intel GPU (e.g., Iris Xe)...")
    try:
        model.to("GPU")
        print("    [OK] Successfully bound model to OpenVINO 'GPU' device.")
    except Exception as e:
        print(f"    [WARN] Could not bind to 'GPU' ({e}). Falling back to OpenVINO 'CPU' device.")
        model.to("CPU")

    print(f"\n[*] Generating embeddings in batches (batch_size=16)...")
    batch_size = 16
    all_embeddings = []

    for start_idx in range(0, n_docs, batch_size):
        end_idx = min(start_idx + batch_size, n_docs)
        batch_texts = formatted_docs[start_idx:end_idx]

        inputs = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )

        with torch.no_grad():
            outputs = model(**inputs)

            # E5 average pooling over the last hidden state
            attention_mask = inputs["attention_mask"]
            last_hidden = outputs.last_hidden_state.masked_fill(~attention_mask[..., None].bool(), 0.0)
            embeddings = last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

            # L2 normalization (required for E5 cosine similarity/clustering)
            embeddings = F.normalize(embeddings, p=2, dim=1)

            all_embeddings.append(embeddings.cpu().numpy())

        # Progress indicator
        print(f"    Processed {end_idx}/{n_docs} documents ({(end_idx / n_docs) * 100:.1f}%)", end="\r")

    print() # Newline after loop
    final_matrix = np.vstack(all_embeddings)

    EMBED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.save(EMBED_OUTPUT_PATH, final_matrix)

    print("\n==========================================================================")
    print(f"  EMBEDDINGS GENERATED SUCCESSFULLY!")
    print(f"  Saved matrix to: {EMBED_OUTPUT_PATH} (shape: {final_matrix.shape})")
    print("==========================================================================")
    print("\nNext step -> Run BERTopic clustering on these accelerated embeddings:")
    print("    python src/data-processing/run_bertopic_topics_per_class.py")


if __name__ == "__main__":
    main()
