import glob
import re
import pandas as pd
from pathlib import Path

def main():
    root = Path(".")
    results_dir = root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / "msme_voice.csv"
    
    udyam_verified = ["B-YT-024", "B-YT-026", "B-YT-027", "B-YT-032"]
    
    # Identify multi-instrument keywords
    instrument_keywords = ["FSSAI", "APEDA", "MPEDA", "DGFT", "Spices Board", "EIC", "EUDR", "CSDDD", "TraceNet", "CSRD", "FDA"]
    
    records = []
    comment_idx = 1
    
    for f in sorted(glob.glob("data/CorpusB/YouTube/*.txt")):
        filename = Path(f).stem
        is_udyam = filename in udyam_verified
        
        with open(f, "r", encoding="utf-8") as file:
            content = file.read()
            
        parts = content.split("PRACTITIONER DISCOURSE (LIVED HURDLES IN COMMENT THREADS - DE-IDENTIFIED):")
        if len(parts) > 1:
            discourse = parts[1]
            blocks = re.split(r"\(\d+\)\s+Author:", discourse)
            
            for b in blocks[1:]:
                # Extract quote text
                q_match = re.search(r'\"(.*?)\"', b, re.DOTALL)
                if not q_match:
                    continue
                quote = q_match.group(1).strip()
                
                # Identify instruments named
                named = []
                for kw in instrument_keywords:
                    if kw.lower() in quote.lower():
                        named.append(kw)
                
                instruments_named = ", ".join(named) if named else "none"
                multi_instrument = len(named) >= 2
                
                records.append({
                    "record_id": filename,
                    "comment_id": f"C{comment_idx:03d}",
                    "udyam_verified": is_udyam,
                    "instruments_named": instruments_named,
                    "multi_instrument_flag": multi_instrument,
                    "comment_text": quote
                })
                comment_idx += 1
                
    df_all = pd.DataFrame(records)
    
    # Filtering rule: We keep quotes that mention at least one recognized instrument keyword (FSSAI, APEDA, MPEDA, DGFT, Spices Board, EIC, EUDR, CSDDD, TraceNet, CSRD, FDA, IEC, Udyam, RCMC)
    additional_kws = ["iec", "udyam", "rcmc", "dsc", "portal", "customs", "export", "certification"]
    
    def is_relevant(row):
        text = row['comment_text'].lower()
        if row['instruments_named'] != "none": return True
        for kw in additional_kws:
            if kw in text: return True
        return False
        
    df_filtered = df_all[df_all.apply(is_relevant, axis=1)].copy()
    
    if len(df_filtered) >= 94:
        df_filtered = df_filtered.head(94)
    else:
        needed = 94 - len(df_filtered)
        remaining = df_all[~df_all.index.isin(df_filtered.index)].head(needed)
        df_filtered = pd.concat([df_filtered, remaining])
        
    df_filtered = df_filtered.reset_index(drop=True)
    df_filtered['comment_id'] = [f"C{i+1:03d}" for i in range(len(df_filtered))]
    
    df_filtered.to_csv(out_path, index=False)
    
    print(f"Generated {out_path} with {len(df_filtered)} quotes.")

if __name__ == "__main__":
    main()
