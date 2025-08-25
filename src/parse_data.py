import pandas as pd
from datetime import datetime
import json

# ---------------------------
# Basic helpers (simple)
# ---------------------------
def parse_date(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if not s:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return s  # leave as-is if unknown format

def to_decimal(x):
    if pd.isna(x):
        return None
    try:
        return float(str(x).replace(" ", "").replace(",", ""))
    except Exception:
        try:
            return float(x)
        except Exception:
            return None

def pick_first_nonnull(vals):
    for v in vals:
        if v is not None and str(v).lower() not in ("nan", "none", ""):
            return v
    return None

# ---------------------------
# Normalizers (straight map)
# ---------------------------
def normalize_nbim(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert NBIM data to a normalized format with same field names as Custody.
    """
    df = df.reset_index().rename(columns={"index": "source_row"})
    return pd.DataFrame({
        "source": "NBIM",
        "source_row": df["source_row"],
        "coac_event_key": df.get("COAC_EVENT_KEY"),
        "isin": df.get("ISIN"),
        "sedol": df.get("SEDOL"),
        "ticker": df.get("TICKER"),
        "dividend_rate": df["DIVIDENDS_PER_SHARE"].apply(to_decimal) if "DIVIDENDS_PER_SHARE" in df.columns else None,
        "ex_date": df["EXDATE"].apply(parse_date) if "EXDATE" in df.columns else None,
        # record_date not available in NBIM - excluded from comparison
        "pay_date": df["PAYMENT_DATE"].apply(parse_date) if "PAYMENT_DATE" in df.columns else None,
        "account_id": df.get("BANK_ACCOUNT"),
        "currency": df.get("QUOTATION_CURRENCY"),
        "gross_amount": df["GROSS_AMOUNT_QUOTATION"].apply(to_decimal) if "GROSS_AMOUNT_QUOTATION" in df.columns else None,
        "net_amount": df["NET_AMOUNT_QUOTATION"].apply(to_decimal) if "NET_AMOUNT_QUOTATION" in df.columns else None,
        "withholding_tax": df["WTHTAX_COST_QUOTATION"].apply(to_decimal) if "WTHTAX_COST_QUOTATION" in df.columns else None,
        "withholding_rate": df["WTHTAX_RATE"].apply(to_decimal) if "WTHTAX_RATE" in df.columns else None,
        # fx_rate represents different concepts in NBIM vs Custody - excluded from comparison
        "quantity": df["NOMINAL_BASIS"].apply(to_decimal) if "NOMINAL_BASIS" in df.columns else None
    })

def normalize_custody(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert Custody data to a normalized format with same field names as NBIM.
    """
    df = df.reset_index().rename(columns={"index": "source_row"})
    return pd.DataFrame({
        "source": "Custody",
        "source_row": df["source_row"],
        "coac_event_key": df.get("COAC_EVENT_KEY"),
        "isin": df.get("ISIN"),
        "sedol": df.get("SEDOL"),
        "ticker": None,
        "dividend_rate": df["DIV_RATE"].apply(to_decimal) if "DIV_RATE" in df.columns else None,
        "ex_date": df["EX_DATE"].apply(parse_date) if "EX_DATE" in df.columns else (df["EVENT_EX_DATE"].apply(parse_date) if "EVENT_EX_DATE" in df.columns else None),
        # record_date not available in NBIM - excluded from comparison
        "pay_date": df["PAY_DATE"].apply(parse_date) if "PAY_DATE" in df.columns else (df["EVENT_PAYMENT_DATE"].apply(parse_date) if "EVENT_PAYMENT_DATE" in df.columns else None),
        "account_id": df.get("BANK_ACCOUNTS"),
        "currency": df.get("CURRENCIES"),
        "gross_amount": df["GROSS_AMOUNT"].apply(to_decimal) if "GROSS_AMOUNT" in df.columns else None,
        "net_amount": df["NET_AMOUNT_QC"].apply(to_decimal) if "NET_AMOUNT_QC" in df.columns else None,
        "withholding_tax": df["TAX"].apply(to_decimal) if "TAX" in df.columns else None,
        "withholding_rate": df["TAX_RATE"].apply(to_decimal) if "TAX_RATE" in df.columns else None,
        # fx_rate represents different concepts in NBIM vs Custody - excluded from comparison
        "quantity": df["HOLDING_QUANTITY"].apply(to_decimal) if "HOLDING_QUANTITY" in df.columns else None
    })

# ---------------------------
# Mismatch analysis
# ---------------------------
def add_mismatch_analysis(events):
    """
    Add mismatch analysis to identify fields that differ between NBIM and Custody entries.
    Modifies the events dictionary in-place by adding 'mismatches' field to each account.
    """
    # Fields to compare between NBIM and Custody entries
    comparable_fields = [
        'isin', 'sedol', 'ex_date', 'pay_date', 'currency', 
        'dividend_rate', 'gross_amount', 'net_amount', 'withholding_tax', 
        'withholding_rate', 'quantity'
    ]
    
    def values_are_different(val1, val2):
        """Check if two values are meaningfully different, handling None/null cases."""
        # Both None/null - not different
        if val1 is None and val2 is None:
            return False
        # One is None, other is not - different
        if val1 is None or val2 is None:
            return True
        # Both have values - compare as strings to handle type differences
        return str(val1).strip() != str(val2).strip()
    
    for event in events.values():
        for account_key, account_data in event["accounts"].items():
            nbim_entries = account_data["NBIM"]["entries"]
            custody_entries = account_data["Custody"]["entries"]
            
            # Initialize mismatches
            account_data["mismatches"] = []
            
            # Compare entries (assuming 1:1 mapping for now, but could be extended)
            if nbim_entries and custody_entries:
                # For simplicity, compare first entries of each type
                # This could be extended to handle multiple entries per side
                nbim_entry = nbim_entries[0]
                custody_entry = custody_entries[0]
                
                mismatched_fields = []
                
                for field in comparable_fields:
                    nbim_val = nbim_entry.get(field)
                    custody_val = custody_entry.get(field)
                    
                    if values_are_different(nbim_val, custody_val):
                        mismatched_fields.append({
                            "field": field,
                            "nbim_value": nbim_val,
                            "custody_value": custody_val
                        })
                
                account_data["mismatches"] = mismatched_fields
            
            elif nbim_entries and not custody_entries:
                account_data["mismatches"] = [{"field": "missing_custody", "nbim_value": "present", "custody_value": "missing"}]
            
            elif custody_entries and not nbim_entries:
                account_data["mismatches"] = [{"field": "missing_nbim", "nbim_value": "missing", "custody_value": "present"}]

# ---------------------------
# Main parser
# ---------------------------
def parse_data(custody_raw: pd.DataFrame, nbim_raw: pd.DataFrame):
    """
    Main parser function.
    - Normalizes data
    - Adds mismatch analysis (fields that are not strictly equal between NBIM and Custody)
    - Returns a list of events (dict format for easy manipulation and sending to LLM)
    """
    nbim = normalize_nbim(nbim_raw)
    custody = normalize_custody(custody_raw)
    facts = pd.concat([nbim, custody], ignore_index=True)

    # normalize account ids
    facts["account_id"] = facts["account_id"].astype(str).str.strip()
    facts.loc[facts["account_id"].isin(["", "nan", "none", "None"]), "account_id"] = None

    events = {}

    for _, r in facts.iterrows():
        ekey = r["coac_event_key"]
        if pd.isna(ekey):
            continue  # skip lines with no event key

        acct = r["account_id"]
        acct_key = "_NO_ACCOUNT_" if acct is None else str(acct)
        side = r["source"]

        if ekey not in events:
            events[ekey] = {
                "coac_event_key": ekey,
                "isin": r.get("isin"),
                "ex_date": r.get("ex_date"),
                "pay_date": r.get("pay_date"),
                "accounts": {}
            }
        ev = events[ekey]

        # fill missing event-level fields opportunistically
        ev["isin"] = pick_first_nonnull([ev.get("isin"), r.get("isin")])
        ev["ex_date"] = pick_first_nonnull([ev.get("ex_date"), r.get("ex_date")])
        ev["pay_date"] = pick_first_nonnull([ev.get("pay_date"), r.get("pay_date")])

        if acct_key not in ev["accounts"]:
            ev["accounts"][acct_key] = {
                "NBIM": {"entries": [], "summary": {}},
                "Custody": {"entries": [], "summary": {}},
            }

        entry = {
            "row_id": int(r.get("source_row")) if r.get("source_row") is not None and pd.notna(r.get("source_row")) else None,
            "isin": r.get("isin"),
            "sedol": r.get("sedol"),
            "ex_date": r.get("ex_date"),
            "pay_date": r.get("pay_date"),
            "currency": r.get("currency"),
            "dividend_rate": r.get("dividend_rate"),
            "gross_amount": r.get("gross_amount"),
            "net_amount": r.get("net_amount"),
            "withholding_tax": r.get("withholding_tax"),
            "withholding_rate": r.get("withholding_rate"),
            "quantity": r.get("quantity"),
        }

        ev["accounts"][acct_key][side]["entries"].append(entry)

    # very light summaries (optional; keep it simple)
    def sum_safe(values):
        vals = [v for v in values if v is not None]
        return float(sum(vals)) if vals else None

    for ev in events.values():
        for acct_key, acct in ev["accounts"].items():
            for side in ("NBIM", "Custody"):
                entries = acct[side]["entries"]
                acct[side]["summary"] = {
                    "gross_amount_sum": sum_safe([e["gross_amount"] for e in entries]),
                    "net_amount_sum": sum_safe([e["net_amount"] for e in entries]),
                    "withholding_tax_sum": sum_safe([e["withholding_tax"] for e in entries]),
                }

    # Add mismatch analysis
    add_mismatch_analysis(events)
    
    event_data = list(events.values())
    for event in event_data:
        for account_key, account_values in event['accounts'].items():
            if account_values['mismatches']:
                print(f"Mismatch event {event['coac_event_key']}, account {account_key}:")
                print(account_values['mismatches'])
                
    # Return Python objects (easy to work with, and can be converted to JSON for LLM later)
    return event_data

