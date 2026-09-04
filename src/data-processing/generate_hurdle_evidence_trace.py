import pandas as pd
from pathlib import Path
import re
import glob

def get_sentence_score(text, keyword):
    lines = text.split('\n')
    skip_prefixes = ("Title:", "Doc ID:", "Retrieval Date:", "Source:", "URL:", "Scraped Date:", "OFFICIAL JOURNAL", "REGULATION (EU)", "on the making available")
    filtered_lines = [l for l in lines if not any(l.strip().startswith(p) for p in skip_prefixes)]
    clean_text = " ".join(filtered_lines).replace('\n', ' ')
    
    sentences = re.split(r'(?<=[.!?]) +', clean_text)
    
    strong = ['burden', 'disproportionate', 'administrative and financial', 'compliance cost', 'smallholder']
    medium = ['cost ', 'challenge', 'difficult', 'barrier', 'hurdle', 'require', 'expensive', 'margin', 'struggle', 'must collect']
    
    best_s = 'none'
    best_score = -1
    
    for s in sentences:
        if keyword.lower() in s.lower() and len(s) > 30 and 'http' not in s:
            if any(hw in s.lower() for hw in strong):
                return s.strip().replace('  ', ' '), 2
            elif any(hw in s.lower() for hw in medium):
                if best_score < 1:
                    best_s, best_score = s.strip().replace('  ', ' '), 1
            elif len(s) > 60 and not s.isupper():
                if best_score < 0:
                    best_s, best_score = s.strip().replace('  ', ' '), 0
                    
    return best_s, best_score

def main():
    root = Path(".")
    results_dir = root / "data" / "results"
    out_path = results_dir / "hurdle_evidence_trace.csv"
    
    hurdles = [
        {
            "name": "Market Access & MPEDA/EU Export Infrastructure Costs",
            "kws": ["MPEDA", "export infrastructure", "market access"],
            "dest": "EU",
            "unit": "consignment and establishment",
            "mandate": "Reg. 2019/1793 & EU Catch Certificate"
        },
        {
            "name": "APEDA Registration & Post-Harvest Infrastructure Bottlenecks",
            "kws": ["APEDA", "post-harvest"],
            "dest": "EU",
            "unit": "firm",
            "mandate": "APEDA TraceNet"
        },
        {
            "name": "EUDR & CSRD Sustainability Reporting Burden",
            "kws": ["EUDR", "CSRD", "Directive 2022/2464", "sustainability reporting"],
            "dest": "EU",
            "unit": "consignment and establishment",
            "mandate": "EUDR 2023/1115 & CSRD/Directive 2022/2464"
        },
        {
            "name": "FSSAI Hygiene Standards & Facility Audit Compliance",
            "kws": ["FSSAI", "hygiene", "audit compliance"],
            "dest": "US",
            "unit": "firm",
            "mandate": "FSSAI"
        }
    ]
    
    msme_path = results_dir / "msme_voice.csv"
    msme_df = pd.read_csv(msme_path) if msme_path.exists() else pd.DataFrame()
    
    corpus_files = []
    excluded = ["SupplyChain_Research", "MoFPI_PIB", "NITI_MSME", "DataGov", "CSR", "EUMOFA", "EFSA"]
    for f in glob.glob("data/CorpusA/**/*.txt", recursive=True):
        if not any(ep in f for ep in excluded):
            corpus_files.append(f)
    for f in glob.glob("data/CorpusB/**/*.txt", recursive=True):
        corpus_files.append(f)
        
    records = []
    for h in hurdles:
        best_quote = "none"
        best_file = "none"
        best_score = -2
        
        if not msme_df.empty:
            for kw in h["kws"]:
                matches = msme_df[msme_df['comment_text'].str.contains(kw, case=False, na=False)]
                if not matches.empty:
                    for idx, row in matches.iterrows():
                        if any(hw in row['comment_text'].lower() for hw in ['burden', 'cost', 'smallholder', 'challenge', 'difficult', 'barrier', 'hurdle', 'compliance', 'require', 'expensive']):
                            best_quote, best_file, best_score = row['comment_text'], f"data/CorpusB/YouTube/{row['record_id']}.txt", 3
                            break
                    if best_score < 3:
                        best_quote, best_file, best_score = matches.iloc[0]['comment_text'], f"data/CorpusB/YouTube/{matches.iloc[0]['record_id']}.txt", 2
                    break
        
        if best_score < 2:
            for kw in h["kws"]:
                for cf in corpus_files:
                    try:
                        with open(cf, "r", encoding="utf-8", errors="ignore") as file:
                            text = file.read()
                            if kw.lower() in text.lower():
                                s, score = get_sentence_score(text, kw)
                                if score > best_score:
                                    best_quote, best_file, best_score = s, cf.replace('\\', '/'), score
                                    if best_score == 2:
                                        break
                    except Exception:
                        pass
                if best_score == 2:
                    break
                    
        records.append({
            "hurdle_name": h["name"],
            "evidence_quote": best_quote,
            "evidence_files": best_file,
            "destination_regime": h["dest"],
            "unit_of_attachment": h["unit"],
            "sustainability_mandate": h["mandate"]
        })
        
    df = pd.DataFrame(records)
    df.to_csv(out_path, index=False)
    print(f"Generated {out_path} with {len(df)} rows.")

if __name__ == "__main__":
    main()
