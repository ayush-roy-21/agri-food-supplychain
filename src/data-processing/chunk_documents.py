"""
chunk_documents.py

Splits long source documents across Corpus A (and must-chunk/borderline files in Corpus B GDELT) into modeling chunks.
1. Uses existing `--- PAGE N ---` markers from pypdf extraction as natural chunk boundaries.
2. Bakes the parent ID into chunk IDs (e.g., `A-MPEDA-004-C01`).
3. Keeps chunks in separate derived directories (`CorpusA_Chunks/` and `CorpusB_Chunks/`).
4. Generates a unified manifest (`data/chunk_manifest.csv`) inheriting parent DQA scores and locus tags without re-scoring chunks.
5. Does NOT modify or touch `data/master_registry.csv` (which remains the document-level source of truth).
"""

import os
import re
import shutil
import pandas as pd
import numpy as np
from pathlib import Path

from text_cleaning_utils import strip_provenance_preamble

def stratify_document_chunks(df, doc_id_col='doc_id', text_col='chunk_text'):
    """
    Applies sub-linear down-weighting (square root) and stratified sampling 
    to document chunks to prevent clustering dominance.
    """
    sampled_rows = []
    
    # Group the dataframe by the parent document ID
    for doc_id, group in df.groupby(doc_id_col, sort=False):
        total_chunks = len(group)
        
        # 1. Calculate the sub-linear target (ceiling of square root)
        target_chunk_count = int(np.ceil(np.sqrt(total_chunks)))
        
        # 2. Generate evenly spaced indices across the document
        # linspace gives float values, so we cast to integer to get exact row indices
        stratified_indices = np.linspace(0, total_chunks - 1, target_chunk_count, dtype=int)
        
        # 3. Extract those specific chunks
        sampled_group = group.iloc[stratified_indices]
        sampled_rows.append(sampled_group)
        
    # Recombine into a new, balanced dataframe
    balanced_df = pd.concat(sampled_rows, ignore_index=True)
    
    return balanced_df

def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    master_reg_path = project_root / "data" / "master_registry.csv"
    
    # 1. Load Master Registry for parent attribute lookup
    if not master_reg_path.exists():
        print("[!] Error: data/master_registry.csv not found.")
        return
        
    df_master = pd.read_csv(master_reg_path)
    
    # Create quick lookup dicts by exact filename AND by doc_id
    lookup_by_file = {}
    lookup_by_id = {}
    
    for _, row in df_master.iterrows():
        doc_id = str(row['doc_id']).strip()
        tier = str(row['corpus_tier']).strip()
        dqa_score = str(row.get('dqa_context_score', 'A,A,A,A,A,A'))
        locus_tag = str(row.get('locus_tag', 'unassigned'))
        verif_logic = str(row.get('verification_logic', 'unassigned'))
        title_val = str(row.get('title_url_query', '')).strip()
        
        info = {
            "doc_id": doc_id,
            "corpus_tier": tier,
            "dqa_score": dqa_score,
            "locus_tag": locus_tag,
            "verification_logic": verif_logic
        }
        lookup_by_id[doc_id] = info
        lookup_by_file[title_val] = info
        # Also map clean filename if title_url_query contains path or URL
        split_part = title_val.split("/")[-1]
        if split_part and len(split_part) > 2:
            clean_name = Path(split_part).name
            if clean_name and len(clean_name) > 2:
                lookup_by_file[clean_name] = info

    # Helper to resolve exact parent info from file path
    # pyrefly: ignore [bad-function-definition]
    def get_parent_info(txt_path: Path, expected_tier: str = None):
        base_id = txt_path.stem
        if base_id in lookup_by_id and (not expected_tier or lookup_by_id[base_id]["corpus_tier"] == expected_tier):
            return lookup_by_id[base_id]
            
        pdf_name = txt_path.with_suffix(".pdf").name
        if pdf_name in lookup_by_file and (not expected_tier or lookup_by_file[pdf_name]["corpus_tier"] == expected_tier):
            return lookup_by_file[pdf_name]
        if txt_path.name in lookup_by_file and (not expected_tier or lookup_by_file[txt_path.name]["corpus_tier"] == expected_tier):
            return lookup_by_file[txt_path.name]
            
        # Fallback partial match in lookup_by_file
        for k, v in lookup_by_file.items():
            if not k or len(k) < 4:
                continue
            if expected_tier and v["corpus_tier"] != expected_tier:
                continue
            if pdf_name in k or k in pdf_name:
                return v
                
        return None

    # Setup target directories
    chunks_root_a = project_root / "CorpusA_Chunks"
    data_chunks_a = project_root / "data" / "CorpusA_Chunks"
    chunks_root_b = project_root / "CorpusB_Chunks"
    data_chunks_b = project_root / "data" / "CorpusB_Chunks"
    
    for p in [chunks_root_a, data_chunks_a, chunks_root_b, data_chunks_b]:
        if p.exists():
            shutil.rmtree(p)
        p.mkdir(parents=True, exist_ok=True)
        
    # Collect candidate files across Corpus A (>=600 words) and specific must-chunk/borderline GDELT files (>=1400 words plus B-GD-007, B-GD-101)
    all_corpus_a_txts = list((project_root / "CorpusA").rglob("*.txt"))
    all_corpus_b_txts = list((project_root / "CorpusB").rglob("*.txt"))
    
    candidates = []
    for f in all_corpus_a_txts:
        # Exclude A-MPEDA-002 if stray
        if "A-MPEDA-002" in f.name:
            continue
        try:
            raw = open(f, encoding="utf-8", errors="replace").read()
            clean, _ = strip_provenance_preamble(raw)
            words = clean.split()
            if len(words) >= 400:
                candidates.append((f, "A"))
        except Exception:
            pass
            
    for f in all_corpus_b_txts:
        try:
            raw = open(f, encoding="utf-8", errors="replace").read()
            clean, _ = strip_provenance_preamble(raw)
            words = clean.split()
            # User specifically noted B-GD-007, B-GD-101, and B-GD-071 plus borderline files
            if f.stem in ["B-GD-007", "B-GD-101", "B-GD-071"] or len(words) >= 400:
                candidates.append((f, "B"))
        except Exception:
            pass

    print(f"[*] Total target documents identified for chunking: {len(candidates)}")
    
    manifest_rows = []
    total_chunks = 0
    preamble_strip_log = []
    
    for txt_path, tier in sorted(candidates, key=lambda x: x[0].name):
        parent_info = get_parent_info(txt_path, tier)
        if not parent_info:
            print(f"[!] Warning: Could not resolve parent ID for {txt_path.name}. Skipping.")
            continue
            
        parent_id = parent_info["doc_id"]
        parent_tier = parent_info["corpus_tier"]
        dqa_score = parent_info["dqa_score"]
        locus_tag = parent_info["locus_tag"]
        verif_logic = parent_info["verification_logic"]
        
        with open(txt_path, "r", encoding="utf-8", errors="replace") as f:
            raw_content = f.read()

        content, preamble_marker = strip_provenance_preamble(raw_content)
        if preamble_marker:
            preamble_strip_log.append({
                "doc_id": parent_id,
                "source_file": txt_path.relative_to(project_root).as_posix(),
                "marker": preamble_marker,
                "words_before": len(raw_content.split()),
                "words_after": len(content.split()),
            })

        # DEC-2026-0XX: after removing the collection-pipeline provenance
        # header, some Corpus B records (observed: all 3 Reddit stubs) have
        # little or no genuine discourse text left -- e.g. a header claiming
        # "de-identified public discourse samples" with no samples attached,
        # or only post titles/URLs with no body/comment text. Log and skip
        # rather than silently modeling near-empty units.
        if len(content.split()) < 30:
            print(f"    -> Parent [{parent_id}] ({txt_path.name[:45]}...) has only "
                  f"{len(content.split())} words of genuine content after provenance-header "
                  f"removal (was {len(raw_content.split())} words including header). Skipping.")
            preamble_strip_log.append({
                "doc_id": parent_id,
                "source_file": txt_path.relative_to(project_root).as_posix(),
                "marker": "EXCLUDED_NEAR_EMPTY_AFTER_STRIP",
                "words_before": len(raw_content.split()),
                "words_after": len(content.split()),
            })
            continue
            
        # Determine target output root for this parent
        if parent_tier == "A":
            out_dir = chunks_root_a / parent_id
            data_out_dir = data_chunks_a / parent_id
        else:
            out_dir = chunks_root_b / parent_id
            data_out_dir = data_chunks_b / parent_id
        
        chunks = []
        
        # Check if file has pypdf page markers
        if "--- PAGE " in content:
            # Split by exact page markers
            parts = re.split(r'--- PAGE (\d+) ---', content)
            # parts[0] is header/before first page (usually empty)
            # parts[1::2] are page numbers, parts[2::2] are page texts
            pages = []
            for idx in range(1, len(parts), 2):
                p_num = parts[idx]
                p_text = parts[idx+1].strip()
                if p_text:
                    pages.append((int(p_num), p_text))
                    
            # Group pages into chunks of roughly ~250 words target (max 400 hard cap)
            curr_pages = []
            curr_words = []
            
            for p_num, p_text in pages:
                p_words = p_text.split()
                curr_pages.append(p_num)
                curr_words.extend(p_words)
                
                while len(curr_words) >= 400:
                    chunk_w = curr_words[:250]
                    chunks.append((curr_pages[:], chunk_w[:], "\n\n".join([f"[Page {n}]\n{t}" for n, t in pages if n in curr_pages])))
                    curr_words = curr_words[220:] # keep ~30 words overlap when force-splitting mid-page blob
                    curr_pages = [curr_pages[-1]] if curr_pages else []
                    
                if len(curr_words) >= 250:
                    chunks.append((curr_pages[:], curr_words[:], "\n\n".join([f"[Page {n}]\n{t}" for n, t in pages if n in curr_pages])))
                    curr_pages = []
                    curr_words = []
                    
            # Any remaining pages/words (< 250 words)
            if curr_words:
                if len(curr_words) < 90 and chunks:
                    # Merge trailing remainder (< 90 floor) into previous chunk
                    prev_pages, prev_words, prev_text = chunks[-1]
                    prev_pages.extend(curr_pages)
                    seen_p = set()
                    prev_pages = [p for p in prev_pages if not (p in seen_p or seen_p.add(p))]
                    prev_words.extend(curr_words)
                    
                    if len(prev_words) > 400:
                        # Ensure hard cap 400 is not violated by merge
                        chunk1_w = prev_words[:250]
                        chunk2_w = prev_words[220:]
                        chunks[-1] = (prev_pages[:], chunk1_w, "\n\n".join([f"[Page {n}]\n{t}" for n, t in pages if n in prev_pages]))
                        chunks.append((prev_pages[:], chunk2_w, "\n\n".join([f"[Page {n}]\n{t}" for n, t in pages if n in prev_pages])))
                    else:
                        chunks[-1] = (prev_pages, prev_words, prev_text + "\n\n" + "\n\n".join([f"[Page {n}]\n{t}" for n, t in pages if n in curr_pages]))
                else:
                    chunks.append((curr_pages[:], curr_words[:], "\n\n".join([f"[Page {n}]\n{t}" for n, t in pages if n in curr_pages])))
                    
            if len(chunks) == 0:
                if out_dir.exists() and not any(out_dir.iterdir()): out_dir.rmdir()
                if data_out_dir.exists() and not any(data_out_dir.iterdir()): data_out_dir.rmdir()
                continue
            if len(chunks) == 1:
                group_word_count = len(chunks[0][1])
                if group_word_count < 400 and parent_id not in ["B-GD-007", "B-GD-101", "B-GD-071"]:
                    print(f"    -> Parent [{parent_id}] ({txt_path.name[:45]}...) produced only 1 chunk ({group_word_count} words). Skipping separate chunk storage.")
                    if out_dir.exists() and not any(out_dir.iterdir()): out_dir.rmdir()
                    if data_out_dir.exists() and not any(data_out_dir.iterdir()): data_out_dir.rmdir()
                    continue
                
            # Format chunks
            word_offset = 1
            for idx, (p_nums, c_words, c_text) in enumerate(chunks, 1):
                c_id = f"{parent_id}-C{idx:02d}"
                w_count = len(c_words)
                w_range_str = f"{word_offset} - {word_offset + w_count - 1}"
                word_offset += w_count
                
                if len(p_nums) == 1:
                    p_range_str = f"Page {p_nums[0]}"
                else:
                    p_range_str = f"Page {p_nums[0]} to Page {p_nums[-1]}"
                    
                chunks_formatted_list = (c_id, p_range_str, w_range_str, w_count, c_text)
                
                # Write chunk file
                header = (
                    f"--- CHUNK HEADER ---\n"
                    f"Chunk ID: {c_id}\n"
                    f"Parent Doc ID: {parent_id}\n"
                    f"Page Range: {p_range_str}\n"
                    f"Word Range: {w_range_str}\n"
                    f"Word Count: {w_count:,}\n"
                    f"--------------------\n\n"
                    f"{c_text}"
                )
                
                chunk_file = out_dir / f"{c_id}.txt"
                
                manifest_rows.append({
                    "chunk_id": c_id,
                    "parent_doc_id": parent_id,
                    "corpus_tier": parent_tier,
                    "page_range": p_range_str,
                    "word_range": w_range_str,
                    "word_count": w_count,
                    "chunk_path": chunk_file.relative_to(project_root).as_posix(),
                    "parent_dqa_score": dqa_score,
                    "parent_locus_tag": locus_tag,
                    "parent_verification_logic": verif_logic,
                    "_chunk_header": header
                })
                total_chunks += 1
                
        else:
            # Fallback for web-scraped or non-page text files (~250 words target, 400 hard cap, 90 floor, ~30 overlap)
            paras = [p.strip() for p in re.split(r'\n\s*\n', content) if p.strip()]
            curr_paras = []
            curr_words = []
            
            for para in paras:
                p_words = para.split()
                curr_paras.append(para)
                curr_words.extend(p_words)
                
                while len(curr_words) >= 400:
                    chunk_w = curr_words[:250]
                    chunks.append((chunk_w, " ".join(chunk_w)))
                    curr_words = curr_words[220:] # ~30 words overlap W_overlap = 30
                    curr_paras = [" ".join(curr_words)] if curr_words else []
                    
                if len(curr_words) >= 250:
                    chunks.append((curr_words[:], " ".join(curr_words)))
                    curr_words = curr_words[-30:] if len(curr_words) >= 30 else curr_words[:] # ~30 words overlap for next chunk
                    curr_paras = [" ".join(curr_words)] if curr_words else []
                    
            if curr_words:
                if chunks and len(curr_words) <= 30 and curr_words == chunks[-1][0][-len(curr_words):]:
                    # Remainder is purely the overlap from the previous chunk, discard
                    pass
                elif len(curr_words) < 90 and chunks:
                    new_w = curr_words[30:] if (len(curr_words) > 30 and curr_words[:30] == chunks[-1][0][-30:]) else curr_words
                    if new_w and len(chunks[-1][0]) + len(new_w) <= 400:
                        prev_words, prev_text = chunks[-1]
                        prev_words.extend(new_w)
                        chunks[-1] = (prev_words, " ".join(prev_words))
                    elif new_w:
                        chunks.append((curr_words[:], " ".join(curr_words)))
                else:
                    chunks.append((curr_words[:], " ".join(curr_paras)))
                    
            if len(chunks) == 0:
                if out_dir.exists() and not any(out_dir.iterdir()): out_dir.rmdir()
                if data_out_dir.exists() and not any(data_out_dir.iterdir()): data_out_dir.rmdir()
                continue
            if len(chunks) == 1:
                group_word_count = len(chunks[0][0])
                if group_word_count < 400 and parent_id not in ["B-GD-007", "B-GD-101", "B-GD-071"]:
                    print(f"    -> Parent [{parent_id}] ({txt_path.name[:45]}...) produced only 1 chunk ({group_word_count} words). Skipping separate chunk storage.")
                    if out_dir.exists() and not any(out_dir.iterdir()): out_dir.rmdir()
                    if data_out_dir.exists() and not any(data_out_dir.iterdir()): data_out_dir.rmdir()
                    continue
                
            word_offset = 1
            for idx, (c_words, c_text) in enumerate(chunks, 1):
                c_id = f"{parent_id}-C{idx:02d}"
                w_count = len(c_words)
                w_range_str = f"{word_offset} - {word_offset + w_count - 1}"
                word_offset += w_count
                p_range_str = "N/A (Web Scraped / Text Extract)"
                
                header = (
                    f"--- CHUNK HEADER ---\n"
                    f"Chunk ID: {c_id}\n"
                    f"Parent Doc ID: {parent_id}\n"
                    f"Page Range: {p_range_str}\n"
                    f"Word Range: {w_range_str}\n"
                    f"Word Count: {w_count:,}\n"
                    f"--------------------\n\n"
                    f"{c_text}"
                )
                
                chunk_file = out_dir / f"{c_id}.txt"
                
                manifest_rows.append({
                    "chunk_id": c_id,
                    "parent_doc_id": parent_id,
                    "corpus_tier": parent_tier,
                    "page_range": p_range_str,
                    "word_range": w_range_str,
                    "word_count": w_count,
                    "chunk_path": chunk_file.relative_to(project_root).as_posix(),
                    "parent_dqa_score": dqa_score,
                    "parent_locus_tag": locus_tag,
                    "parent_verification_logic": verif_logic,
                    "_chunk_header": header
                })
                total_chunks += 1

        print(f"    -> Chunked parent [{parent_id}] ({txt_path.name[:45]}...) into {len(chunks)} chunks.")
        
    # Apply sub-linear down-weighting (ceiling square-root) and stratified sampling
    df_manifest = pd.DataFrame(manifest_rows)
    raw_total = len(df_manifest)
    print(f"\n[*] Total raw chunks generated across all candidate documents: {raw_total}")
    
    df_manifest = stratify_document_chunks(df_manifest, doc_id_col="parent_doc_id", text_col="_chunk_header")
    balanced_total = len(df_manifest)
    print(f"[*] Total balanced chunks after sub-linear down-weighting (stratified square-root): {balanced_total}")
    
    # Write only the sampled chunk files to disk
    for _, row in df_manifest.iterrows():
        chunk_file = project_root / row["chunk_path"]
        data_chunk_file = project_root / "data" / row["chunk_path"]
        
        chunk_file.parent.mkdir(parents=True, exist_ok=True)
        data_chunk_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(chunk_file, "w", encoding="utf-8") as f:
            f.write(row["_chunk_header"])
        with open(data_chunk_file, "w", encoding="utf-8") as f:
            f.write(row["_chunk_header"])
            
    # Drop temporary header column and save Manifest
    df_manifest = df_manifest.drop(columns=["_chunk_header"])
    manifest_out = project_root / "data" / "chunk_manifest.csv"
    manifest_out_a = chunks_root_a / "chunk_manifest.csv"
    
    df_manifest.to_csv(manifest_out, index=False, encoding="utf-8")
    df_manifest.to_csv(manifest_out_a, index=False, encoding="utf-8")

    if preamble_strip_log:
        strip_log_path = project_root / "data" / "preamble_strip_log.csv"
        pd.DataFrame(preamble_strip_log).to_csv(strip_log_path, index=False, encoding="utf-8")
        n_excluded = sum(1 for r in preamble_strip_log if r["marker"] == "EXCLUDED_NEAR_EMPTY_AFTER_STRIP")
        print(f"\n[*] Provenance-preamble strip log: {len(preamble_strip_log)} source files had a "
              f"collection-pipeline header removed before chunking ({n_excluded} excluded entirely "
              f"as near-empty after stripping). Details: {strip_log_path}")
    
    print("\n==========================================================================")
    print(f"  CHUNKING COMPLETE! Total Chunks Generated: {balanced_total} (down-weighted from {raw_total})")
    print(f"  Manifest saved to: data/chunk_manifest.csv ({len(df_manifest)} records)")
    print("==========================================================================")

if __name__ == "__main__":
    main()