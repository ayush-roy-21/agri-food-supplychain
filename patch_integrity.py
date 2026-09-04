import pandas as pd

def patch_file():
    with open("src/data-processing/verify_pipeline_integrity.py", "r") as f:
        content = f.read()

    replacement = """
    # 16. Round 2 Fixes Check
    import pandas as pd
    
    # a. alert_99_19_firms_verified.csv has no dummies and IS actually verified
    alert_99_path = results_dir / "alert_99_19_firms_verified.csv"
    if alert_99_path.exists():
        df_99 = pd.read_csv(alert_99_path)
        if df_99["firm_name"].str.contains("Dummy Firm").any():
            errors.append("Round 2 Check failed: alert_99_19_firms_verified.csv still contains Dummy Firms.")
        elif df_99["register_consulted"].isnull().any() or (df_99["register_consulted"] == "").any() or df_99["lookup_date"].isnull().any():
            errors.append("Round 2 Check failed: alert_99_19_firms_verified.csv is missing verification data (register_consulted/lookup_date).")
        else:
            print("[OK] Round 2 Check passed: alert_99_19_firms_verified.csv has real firms and is fully verified.")
            
    # b. alert_16_35_firms_verified.csv is actually verified
    alert_16_path = results_dir / "alert_16_35_firms_verified.csv"
    if alert_16_path.exists():
        df_16 = pd.read_csv(alert_16_path)
        if df_16["register_consulted"].isnull().any() or (df_16["register_consulted"] == "").any() or df_16["lookup_date"].isnull().any():
            errors.append("Round 2 Check failed: alert_16_35_firms_verified.csv is missing verification data (register_consulted/lookup_date).")
        else:
            print("[OK] Round 2 Check passed: alert_16_35_firms_verified.csv is fully verified.")
            
    # c. msme_voice.csv no dummy text
    msme_path = results_dir / "msme_voice.csv"
    if msme_path.exists():
        df_msme = pd.read_csv(msme_path)
        if df_msme["comment_text"].str.contains("Placeholder hand-coded").any():
            errors.append("Round 2 Check failed: msme_voice.csv still contains dummy text.")
        else:
            print("[OK] Round 2 Check passed: msme_voice.csv has real quotes.")
            
    # d. hurdle_evidence_trace.csv logic
    trace_path = results_dir / "hurdle_evidence_trace.csv"
    if trace_path.exists():
        df_trace = pd.read_csv(trace_path)
        if df_trace["evidence_files"].str.contains("SupplyChain_Research").any():
            errors.append("Round 2 Check failed: hurdle_evidence_trace.csv uses SupplyChain_Research.")
        
        invalid_dest = df_trace[~df_trace["destination_regime"].isin(["EU", "US"])]
        if not invalid_dest.empty:
            errors.append(f"Round 2 Check failed: hurdle_evidence_trace.csv has invalid destination_regime (must be EU or US strictly). Found: {invalid_dest['destination_regime'].unique()}")
        else:
            print("[OK] Round 2 Check passed: hurdle_evidence_trace.csv avoids SupplyChain_Research and has strict EU/US regimes.")

    print("-" * 80)
"""
    
    start_idx = content.find("    # 16. Round 2 Fixes Check")
    end_idx = content.find("    print(\"-\" * 80)")
    
    if start_idx != -1 and end_idx != -1:
        new_content = content[:start_idx] + replacement + content[end_idx + 22:]
        with open("src/data-processing/verify_pipeline_integrity.py", "w") as f:
            f.write(new_content)
        print("Patched.")
    else:
        print("Could not find patch bounds.")

if __name__ == "__main__":
    patch_file()
