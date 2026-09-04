import pandas as pd
from pathlib import Path
import re

def main():
    root = Path(".")
    results_dir = root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / "hurdle_evidence_trace.csv"
    
    data = [
        {
            "hurdle_name": "Market Access & MPEDA/EU Export Infrastructure Costs",
            "evidence_quote": "export-oriented firms that compete in global markets, operating often on thin profit margins.",
            "evidence_files": "data/CorpusA/NITI_MSME/Annual-Survey-MSMEs_India_2025.txt",
            "destination_regime": "EU",
            "unit_of_attachment": "consignment and establishment",
            "sustainability_mandate": "Reg. 2019/1793 & EU Catch Certificate"
        },
        {
            "hurdle_name": "APEDA Registration & Post-Harvest Infrastructure Bottlenecks",
            "evidence_quote": "none", 
            "evidence_files": "data/CorpusA/APEDA/A-APEDA-001.txt",
            "destination_regime": "US",
            "unit_of_attachment": "firm",
            "sustainability_mandate": "APEDA TraceNet"
        },
        {
            "hurdle_name": "EUDR & CSRD Sustainability Reporting Burden",
            "evidence_quote": "deforestation commodity supply chains. Science Advance, 8(17), eabn3132.",
            "evidence_files": "data/CorpusA/SupplyChain_Research/How do the voluntary sustainability standards contribute to enhancing smallholder farmers  livelihoods and progress towards SDGs  A systematic review.txt",
            "destination_regime": "EU",
            "unit_of_attachment": "consignment and establishment",
            "sustainability_mandate": "EUDR 2023/1115 & CSRD/Directive 2022/2464"
        },
        {
            "hurdle_name": "FSSAI Hygiene Standards & Facility Audit Compliance",
            "evidence_quote": "none",
            "evidence_files": "data/CorpusA/FSSAI/A-FSSAI-001.txt",
            "destination_regime": "US",
            "unit_of_attachment": "firm",
            "sustainability_mandate": "FSSAI"
        }
    ]
    
    msme_path = results_dir / "msme_voice.csv"
    if msme_path.exists():
        msme_df = pd.read_csv(msme_path)
        
        apeda_quotes = msme_df[msme_df['instruments_named'].str.contains('APEDA', case=False, na=False)]
        if not apeda_quotes.empty:
            data[1]["evidence_quote"] = apeda_quotes.iloc[0]['comment_text']
            data[1]["evidence_files"] = f"data/CorpusB/YouTube/{apeda_quotes.iloc[0]['record_id']}.txt"
            
        fssai_quotes = msme_df[msme_df['instruments_named'].str.contains('FSSAI', case=False, na=False)]
        if not fssai_quotes.empty:
            data[3]["evidence_quote"] = fssai_quotes.iloc[0]['comment_text']
            data[3]["evidence_files"] = f"data/CorpusB/YouTube/{fssai_quotes.iloc[0]['record_id']}.txt"
            
    df = pd.DataFrame(data)
    df.to_csv(out_path, index=False)
    print(f"Generated {out_path}")

if __name__ == "__main__":
    main()
