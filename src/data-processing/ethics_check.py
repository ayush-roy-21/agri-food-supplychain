# ethics_check.py
"""
Ethics Check Module (Section 11 Ethics Protocol Enforcement for Corpus B)
Enforces ethics clearance before data collection across social and user platforms
(Reddit, YouTube, X, LinkedIn, etc.).
Stored in data-processing as part of compliance, DQA, and sanitization rules.
"""

import json
from datetime import datetime
from pathlib import Path

def ethics_clearance(platform: str, public: bool, deident_rule: str, storage_plan: str):
    """
    Ethics clearance check before data collection.
    """
    checklist = {
        "platform": platform,
        "public_vs_private": "public" if public else "private",
        "deidentification_rule": deident_rule,
        "storage_retention": storage_plan,
        "status": "approved" if public and deident_rule and storage_plan else "pending",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Automatically log clearance decision to Corpus B ethics log
    try:
        project_root = Path(__file__).resolve().parent.parent.parent
        log_dirs = [
            project_root / "CorpusB",
            project_root / "data" / "CorpusB",
            project_root / "data" / "raw" / "CorpusB"
        ]
        for d in log_dirs:
            d.mkdir(parents=True, exist_ok=True)
            log_file = d / "ethics_clearance_log.json"
            
            existing = []
            if log_file.exists():
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                except Exception:
                    existing = []
            
            existing.append(checklist)
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)
    except Exception as e:
        print(f"[!] Warning: Could not save ethics log: {e}")
        
    return checklist


if __name__ == "__main__":
    # Example: Reddit is public, de-identification rule applied, storage plan defined
    clearance = ethics_clearance(
        platform="Reddit (PRAW)",
        public=True,
        deident_rule="Remove handles, names, locations before analysis",
        storage_plan="Encrypted institutional repository, 3-year retention"
    )
    print("Ethics Clearance:", clearance)
