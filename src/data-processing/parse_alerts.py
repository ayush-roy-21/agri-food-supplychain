import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path
import re

def _parse_alert_html(filepath, require_india=True):
    r"""Shared parsing logic for FDA Import Alert HTML files.
    
    Spec (from C.2):
      1. Strip HTML to text, preserving line breaks.
      2. Match ^Date Published\s*:\s*(\d{2}/\d{2}/\d{4})$
      3. Take the nearest preceding non-empty line (not matching product-code
         or known non-firm patterns) as the firm name.
      4. Search the next 8 lines for "INDIA".
      5. Dedupe on (firm_name, date_published).
    """
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f, "html.parser")
        text = soup.get_text(separator="\n")

    lines = [line.strip() for line in text.split("\n")]

    date_pub_re = re.compile(
        r"^Date Published\s*:\s*(\d{2}/\d{2}/\d{4})$", re.IGNORECASE
    )
    product_code_re = re.compile(r"^\d{2}\s*[A-Z]", re.IGNORECASE)

    # Additional patterns to skip when scanning backwards for firm name
    skip_patterns = [
        re.compile(r",\s*N\.E\.C\.\s*$"),                    # FDA product categories
        re.compile(r"^Desc:", re.IGNORECASE),                  # product descriptions
        re.compile(r"^,"),                                     # address continuation
        re.compile(r"^Date Published", re.IGNORECASE),         # other date lines
        re.compile(r"^OASIS charge", re.IGNORECASE),           # metadata
        re.compile(r"^List of firms", re.IGNORECASE),          # header
        re.compile(r"^substance which may", re.IGNORECASE),    # charge text
        re.compile(r"INDUSTRIAL AREA|MIDC|MIE\b", re.IGNORECASE), # address indicators
        # FDA product-category headers (exact matches)
        re.compile(r"^Vegetables/Vegetable Products$", re.IGNORECASE),
        re.compile(r"^Snack Food Items$", re.IGNORECASE),
        re.compile(r"^Spices, Flavors And Salts$", re.IGNORECASE),
        re.compile(r"^Fruits/Fruit Products$", re.IGNORECASE),
        re.compile(r"^Fishery/Seafood Products$", re.IGNORECASE),
        re.compile(r"^Bakery Products/Dough/Mix$", re.IGNORECASE),
        re.compile(r"^Candy w/o Choc", re.IGNORECASE),
        re.compile(r"^Nuts and Edible Seeds$", re.IGNORECASE),
        re.compile(r"^Whole Grain/Milled Grain$", re.IGNORECASE),
    ]

    # Country names found in the file — skip lines that are just a country
    countries = {
        "AFGHANISTAN", "BANGLADESH", "BRAZIL", "CHINA", "EGYPT", "INDIA",
        "INDONESIA", "IRAN", "JAPAN", "KOREA", "MEXICO", "NEPAL", "PAKISTAN",
        "SRI LANKA", "THAILAND", "TURKEY", "VIETNAM", "UNITED KINGDOM",
    }

    # Pattern for "<State> INDIA" address lines (not firm names)
    state_india_re = re.compile(r"^\w+\s+INDIA$", re.IGNORECASE)

    def _is_skip(cand):
        if cand == "":
            return True
        if product_code_re.match(cand):
            return True
        upper = cand.upper().strip()
        if upper in countries:
            return True
        if state_india_re.match(cand):
            return True
        for pat in skip_patterns:
            if pat.search(cand):
                return True
        return False

    records = []
    for i, line in enumerate(lines):
        m = date_pub_re.match(line)
        if not m:
            continue
        date_published = m.group(1)

        # Backward scan for firm name
        firm_name = None
        for j in range(i - 1, max(-1, i - 20), -1):
            cand = lines[j]
            if _is_skip(cand):
                continue
            firm_name = cand
            break

        if not firm_name:
            continue

        if require_india:
            is_india = False
            for j in range(i + 1, min(i + 9, len(lines))):
                if "INDIA" in lines[j].upper():
                    is_india = True
                    break
            if not is_india:
                continue

        records.append({
            "firm_name": firm_name,
            "date_published": date_published,
        })

    df = pd.DataFrame(records)
    df = df.drop_duplicates(subset=["firm_name", "date_published"])
    return df


def main():
    root = Path(".")
    results_dir = root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # ── Task 7.2: Alert 16-35 (India section) ──────────────────────────
    alert_16_35_path = root / "alert_16_35.html"
    if alert_16_35_path.exists():
        df_16_35 = _parse_alert_html(alert_16_35_path, require_india=True)

        assert len(df_16_35) == 231, (
            f"alert_16_35: expected 231 rows, got {len(df_16_35)}"
        )

        df_16_35.to_csv(results_dir / "alert_16_35_india.csv", index=False)
        print(
            f"Task 7.2: Extracted exactly {len(df_16_35)} rows from "
            f"alert_16_35.html ({df_16_35['firm_name'].nunique()} unique firms)"
        )
    else:
        print("alert_16_35.html not found.")

    # ── Task 7.1: Alert 99-19 (India section, real extraction) ─────────
    alert_99_19_path = root / "alert_99_19.html"
    if alert_99_19_path.exists():
        df_99_19 = _parse_alert_html(alert_99_19_path, require_india=True)

        df_99_19.to_csv(results_dir / "alert_99_19_india.csv", index=False)
        print(
            f"Task 7.1: Extracted {len(df_99_19)} rows from "
            f"alert_99_19.html ({df_99_19['firm_name'].nunique()} unique firms)"
        )
    else:
        print("alert_99_19.html not found.")


if __name__ == "__main__":
    main()
