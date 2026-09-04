import pandas as pd
from pathlib import Path
import re
import glob

def get_sentence(text, keyword):
    # simple sentence extractor around keyword
    sentences = re.split(r'(?<=[.!?]) +', text.replace('\n', ' '))
    for s in sentences:
        if keyword.lower() in s.lower():
            return s.strip()
    return "none"

def main():
    root = Path(".")
    results_dir = root / "data" / "results"
    out_path = results_dir / "hurdle_evidence_trace.csv"
    
    hurdles = [
        {
            "name": "Market Access & MPEDA/EU Export Infrastructure Costs",
            "kws": ["MPEDA", "export infrastructure"],
            "dest": "EU",
            "unit": "consignment and establishment",
            "mandate": "Reg. 2019/1793 & EU Catch Certificate"
        },
        {
            "name": "APEDA Registration & Post-Harvest Infrastructure Bottlenecks",
            "kws": ["APEDA"],
            "dest": "",
            "unit": "firm",
            "mandate": "APEDA TraceNet"
        },
        {
            "name": "EUDR & CSRD Sustainability Reporting Burden",
            "kws": ["EUDR", "CSRD", "Directive 2022/2464"],
            "dest": "EU",
            "unit": "consignment and establishment",
            "mandate": "EUDR 2023/1115 & CSRD/Directive 2022/2464"
        },
        {
            "name": "FSSAI Hygiene Standards & Facility Audit Compliance",
            "kws": ["FSSAI"],
            "dest": "",
            "unit": "firm",
            "mandate": "FSSAI"
        }
    ]
    
    msme_path = results_dir / "msme_voice.csv"
    msme_df = pd.read_csv(msme_path) if msme_path.exists() else pd.DataFrame()
    
    # Collect corpus files
    corpus_files = []
    for f in glob.glob("data/CorpusA/**/*.txt", recursive=True):
        if "SupplyChain_Research" in f:
            continue
        corpus_files.append(f)
    for f in glob.glob("data/CorpusB/**/*.txt", recursive=True):
        corpus_files.append(f)
        
    records = []
    for h in hurdles:
        found_quote = "none"
        found_file = "none"
        
        # Try MSME voice first
        if not msme_df.empty:
            for kw in h["kws"]:
                matches = msme_df[msme_df['comment_text'].str.contains(kw, case=False, na=False)]
                if not matches.empty:
                    found_quote = matches.iloc[0]['comment_text']
                    found_file = f"data/CorpusB/YouTube/{matches.iloc[0]['record_id']}.txt"
                    break
        
        # If not found, try Corpus
        if found_quote == "none":
            for kw in h["kws"]:
                for cf in corpus_files:
                    try:
                        with open(cf, "r", encoding="utf-8", errors="ignore") as file:
                            text = file.read()
                            if kw.lower() in text.lower():
                                s = get_sentence(text, kw)
                                if s != "none":
                                    found_quote = s
                                    found_file = cf.replace('\\', '/')
                                    break
                    except Exception:
                        pass
                if found_quote != "none":
                    break
                    
        records.append({
            "hurdle_name": h["name"],
            "evidence_quote": found_quote,
            "evidence_files": found_file,
            "destination_regime": h["dest"],
            "unit_of_attachment": h["unit"],
            "sustainability_mandate": h["mandate"]
        })
        
    df = pd.DataFrame(records)
    df.to_csv(out_path, index=False)
    print(f"Generated {out_path} with {len(df)} rows.")

if __name__ == "__main__":
    main()
