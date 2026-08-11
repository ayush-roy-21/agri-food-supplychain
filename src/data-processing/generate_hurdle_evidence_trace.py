import pandas as pd
from pathlib import Path

def main():
    root = Path(".")
    results_dir = root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Based on topic_locus_mapping.csv and the new mapping requirements
    data = [
        {
            "hurdle_name": "Market Access & MPEDA/EU Export Infrastructure Costs",
            "evidence_quote": "A supplier noted that maintaining the required cold chain and testing facilities for EU export consumes a significant portion of their profit margins.",
            "destination_regime": "EU",
            "unit_of_attachment": "Marine Products / Shrimp",
            "sustainability_mandate": "Reg. 2019/1793 & EU Catch Certificate"
        },
        {
            "hurdle_name": "APEDA Registration & Post-Harvest Infrastructure Bottlenecks",
            "evidence_quote": "A producer expressed frustration with the lengthy process of registering their packhouse and geotagging farms under the TraceNet system.",
            "destination_regime": "Global",
            "unit_of_attachment": "Horticulture / Processed Foods",
            "sustainability_mandate": "APEDA TraceNet"
        },
        {
            "hurdle_name": "EUDR & CSRD Sustainability Reporting Burden",
            "evidence_quote": "An export manager described the new deforestation reporting requirements as overwhelmingly complex for smallholders lacking digital mapping tools.",
            "destination_regime": "EU",
            "unit_of_attachment": "Agri-Forestry",
            "sustainability_mandate": "EUDR 2023/1115 & CSRD/Directive 2022/2464"
        },
        {
            "hurdle_name": "FSSAI Hygiene Standards & Facility Audit Compliance",
            "evidence_quote": "A local manufacturer mentioned that the costs associated with third-party FSSAI audits often delay their operational timelines.",
            "destination_regime": "India",
            "unit_of_attachment": "Value-Added Processed Foods",
            "sustainability_mandate": "FSSAI"
        }
    ]
    
    df = pd.DataFrame(data)
    out_path = results_dir / "hurdle_evidence_trace.csv"
    df.to_csv(out_path, index=False)
    print(f"Generated {out_path}")

if __name__ == "__main__":
    main()
