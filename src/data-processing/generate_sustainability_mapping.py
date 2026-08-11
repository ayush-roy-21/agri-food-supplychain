import pandas as pd
from pathlib import Path
import os

def main():
    root = Path(".")
    results_dir = root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Classification of EU vs US commodities and Mandates
    data = [
        {"destination_regime": "EU", "commodity": "chilli", "sustainability_mandate": "Reg. 2019/1793", "aspect": "Spices Emergency Controls"},
        {"destination_regime": "EU", "commodity": "nutmeg", "sustainability_mandate": "Reg. 2019/1793", "aspect": "Spices Emergency Controls"},
        {"destination_regime": "EU", "commodity": "cumin", "sustainability_mandate": "Reg. 2019/1793", "aspect": "Spices Emergency Controls"},
        {"destination_regime": "EU", "commodity": "curry leaves", "sustainability_mandate": "Reg. 2019/1793", "aspect": "Spices Emergency Controls"},
        {"destination_regime": "EU", "commodity": "Agri-Forestry", "sustainability_mandate": "EUDR 2023/1115", "aspect": "Deforestation"},
        {"destination_regime": "EU", "commodity": "All Exports", "sustainability_mandate": "CSRD/Directive 2022/2464", "aspect": "Sustainability Reporting"},
        {"destination_regime": "US", "commodity": "black pepper", "sustainability_mandate": "US FDA import alerts", "aspect": "Spices under Salmonella"},
        {"destination_regime": "US", "commodity": "All Exports", "sustainability_mandate": "US FDA FSMA", "aspect": "Foreign Supplier Verification Program"},
        {"destination_regime": "India", "commodity": "All Exports", "sustainability_mandate": "FSSAI", "aspect": "Domestic Compliance / FoSCoS"},
        {"destination_regime": "Global", "commodity": "All Exports", "sustainability_mandate": "Private Certifications", "aspect": "B2B Compliance"}
    ]
    
    df = pd.DataFrame(data)
    
    mapping_csv_path = results_dir / "sustainability_mandate_mapping.csv"
    df.to_csv(mapping_csv_path, index=False)
    print(f"Generated {mapping_csv_path}")

    # Generate the grouped matrix (pivot table)
    grouped_matrix = df.pivot_table(
        index=["destination_regime", "sustainability_mandate", "aspect"],
        values=["commodity"],
        aggfunc=lambda x: ", ".join(x)
    )
    
    matrix_csv_path = results_dir / "sustainability_grouped_matrix.csv"
    grouped_matrix.to_csv(matrix_csv_path)
    print(f"Generated {matrix_csv_path}")

if __name__ == "__main__":
    main()
