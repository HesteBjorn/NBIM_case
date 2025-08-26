import pandas as pd
from datetime import datetime
import json

# ---------------------------
# Basic helpers (simple)
# ---------------------------
def parse_date(date_field):
    if pd.isna(date_field):
        return None
    s = str(date_field).strip()
    if not s:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return s  # leave as-is if unknown format

def to_decimal(number_field):
    if pd.isna(number_field):
        return None
    try:
        return float(str(number_field).replace(" ", "").replace(",", ""))
    except Exception:
        try:
            return float(number_field)
        except Exception:
            return None

def pick_first_nonnull(values):
    for value in values:
        if value is not None and str(value).lower() not in ("nan", "none", ""):
            return value
    return None

# ---------------------------
# Normalizers (straight map)
# ---------------------------
def normalize_nbim(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert NBIM data to a normalized format with same field names as Custody.
    
    Note: Includes fields that may not exist in Custody for root cause analysis.
    These context fields help explain WHY comparable fields might differ between systems.
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
        "settlement_currency": df.get("SETTLEMENT_CURRENCY"),
        "custodian": df.get("CUSTODIAN"),
        "company_name": df.get("ORGANISATION_NAME"),
        "gross_amount": df["GROSS_AMOUNT_QUOTATION"].apply(to_decimal) if "GROSS_AMOUNT_QUOTATION" in df.columns else None,
        "net_amount": df["NET_AMOUNT_QUOTATION"].apply(to_decimal) if "NET_AMOUNT_QUOTATION" in df.columns else None,
        "withholding_tax": df["WTHTAX_COST_QUOTATION"].apply(to_decimal) if "WTHTAX_COST_QUOTATION" in df.columns else None,
        "withholding_rate": df["WTHTAX_RATE"].apply(to_decimal) if "WTHTAX_RATE" in df.columns else None,
        "total_tax_rate": df["TOTAL_TAX_RATE"].apply(to_decimal) if "TOTAL_TAX_RATE" in df.columns else None,
        "settlement_net_amount": df["NET_AMOUNT_SETTLEMENT"].apply(to_decimal) if "NET_AMOUNT_SETTLEMENT" in df.columns else None,
        # NBIM-specific fields for comprehensive analysis
        "local_tax": df["LOCALTAX_COST_QUOTATION"].apply(to_decimal) if "LOCALTAX_COST_QUOTATION" in df.columns else None,
        "local_tax_settlement": df["LOCALTAX_COST_SETTLEMENT"].apply(to_decimal) if "LOCALTAX_COST_SETTLEMENT" in df.columns else None,
        "portfolio_gross_amount": df["GROSS_AMOUNT_PORTFOLIO"].apply(to_decimal) if "GROSS_AMOUNT_PORTFOLIO" in df.columns else None,
        "portfolio_net_amount": df["NET_AMOUNT_PORTFOLIO"].apply(to_decimal) if "NET_AMOUNT_PORTFOLIO" in df.columns else None,
        "portfolio_withholding_tax": df["WTHTAX_COST_PORTFOLIO"].apply(to_decimal) if "WTHTAX_COST_PORTFOLIO" in df.columns else None,
        "fx_rate_to_portfolio": df["AVG_FX_RATE_QUOTATION_TO_PORTFOLIO"].apply(to_decimal) if "AVG_FX_RATE_QUOTATION_TO_PORTFOLIO" in df.columns else None,
        "instrument_description": df.get("INSTRUMENT_DESCRIPTION"),
        "organisation_name": df.get("ORGANISATION_NAME"),
        "restitution_rate": df["RESTITUTION_RATE"].apply(to_decimal) if "RESTITUTION_RATE" in df.columns else None,
        # Position fields
        "quantity": df["NOMINAL_BASIS"].apply(to_decimal) if "NOMINAL_BASIS" in df.columns else None,
        "holding_quantity": None,  # Not available in NBIM
        "loan_quantity": None,     # Not available in NBIM
        "lending_percentage": None, # Not available in NBIM
        # FX and cross-currency fields
        "fx_rate": None, # Not available in NBIM
        "is_cross_currency_reversal": None,  # Not available in NBIM
        # Restitution fields
        "restitution_payment": None,  # Not available in NBIM
        "restitution_amount": None    # Not available in NBIM
    })

def normalize_custody(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert Custody data to a normalized format with same field names as NBIM.
    
    Note: Includes fields that may not exist in NBIM for root cause analysis.
    These context fields help explain WHY comparable fields might differ between systems.
    """
    df = df.reset_index().rename(columns={"index": "source_row"})
    return pd.DataFrame({
        "source": "Custody",
        "source_row": df["source_row"],
        "coac_event_key": df.get("COAC_EVENT_KEY"),
        "isin": df.get("ISIN"),
        "sedol": df.get("SEDOL"),
        "ticker": None,  # Not available in Custody
        "dividend_rate": df["DIV_RATE"].apply(to_decimal) if "DIV_RATE" in df.columns else None,
        "ex_date": df["EX_DATE"].apply(parse_date) if "EX_DATE" in df.columns else (df["EVENT_EX_DATE"].apply(parse_date) if "EVENT_EX_DATE" in df.columns else None),
        # record_date not available in NBIM - excluded from comparison
        "pay_date": df["PAY_DATE"].apply(parse_date) if "PAY_DATE" in df.columns else (df["EVENT_PAYMENT_DATE"].apply(parse_date) if "EVENT_PAYMENT_DATE" in df.columns else None),
        "account_id": df.get("BANK_ACCOUNTS"),
        "currency": df.get("CURRENCIES"),
        "settlement_currency": df.get("SETTLED_CURRENCY"),
        "custodian": df.get("CUSTODIAN"),
        "company_name": None,  # Not available in Custody
        "gross_amount": df["GROSS_AMOUNT"].apply(to_decimal) if "GROSS_AMOUNT" in df.columns else None,
        "net_amount": df["NET_AMOUNT_QC"].apply(to_decimal) if "NET_AMOUNT_QC" in df.columns else None,
        "settlement_net_amount": df["NET_AMOUNT_SC"].apply(to_decimal) if "NET_AMOUNT_SC" in df.columns else None,
        "withholding_tax": df["TAX"].apply(to_decimal) if "TAX" in df.columns else None,
        "withholding_rate": df["TAX_RATE"].apply(to_decimal) if "TAX_RATE" in df.columns else None,
        "total_tax_rate": None,  # Not available in Custody
        # Custody-specific fields for comprehensive analysis
        "local_tax": None,  # Not available in Custody
        "local_tax_settlement": None,  # Not available in Custody
        "portfolio_gross_amount": None,  # Not available in Custody
        "portfolio_net_amount": None,  # Not available in Custody
        "portfolio_withholding_tax": None,  # Not available in Custody
        "fx_rate_to_portfolio": None,  # Not available in Custody
        "instrument_description": None,  # Not available in Custody
        "organisation_name": None,  # Not available in Custody
        "restitution_rate": None,  # Not available in Custody
        # Position fields - CRITICAL FIX: Use NOMINAL_BASIS for primary quantity
        "quantity": df["NOMINAL_BASIS"].apply(to_decimal) if "NOMINAL_BASIS" in df.columns else None,
        "holding_quantity": df["HOLDING_QUANTITY"].apply(to_decimal) if "HOLDING_QUANTITY" in df.columns else None,
        "loan_quantity": df["LOAN_QUANTITY"].apply(to_decimal) if "LOAN_QUANTITY" in df.columns else None,
        "lending_percentage": df["LENDING_PERCENTAGE"].apply(to_decimal) if "LENDING_PERCENTAGE" in df.columns else None,
        # FX and cross-currency fields
        "fx_rate": df["FX_RATE"].apply(to_decimal) if "FX_RATE" in df.columns else None,
        "is_cross_currency_reversal": df["IS_CROSS_CURRENCY_REVERSAL"] if "IS_CROSS_CURRENCY_REVERSAL" in df.columns else None,
        # Restitution fields - Critical for Swiss dividend analysis
        "restitution_payment": df["POSSIBLE_RESTITUTION_PAYMENT"].apply(to_decimal) if "POSSIBLE_RESTITUTION_PAYMENT" in df.columns else None,
        "restitution_amount": df["POSSIBLE_RESTITUTION_AMOUNT"].apply(to_decimal) if "POSSIBLE_RESTITUTION_AMOUNT" in df.columns else None
    })

# ---------------------------
# Mismatch analysis
# ---------------------------
def add_mismatch_analysis(events):
    """
    Add mismatch analysis to identify comparable fields that differ between NBIM and Custody entries.
    Modifies the events dictionary in-place by adding 'mismatches' field to each account.
    Only checks fields that should be comparable between systems.
    """
    # Fields to compare between NBIM and Custody entries (fields that should exist in both)
    comparable_fields = [
        # Basic identifiers that should match
        'isin', 'sedol', 'ex_date', 'pay_date', 'currency', 'settlement_currency', 'custodian',
        # Core dividend fields that should be comparable
        'dividend_rate', 'gross_amount', 'net_amount', 'settlement_net_amount', 
        'withholding_tax', 'withholding_rate',
        # Position - using primary quantity field
        'quantity'
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
            nbim_entry = account_data["NBIM"]
            custody_entry = account_data["Custody"]
            
            if nbim_entry and custody_entry:
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
            elif nbim_entry and not custody_entry:
                account_data["mismatches"] = [{"field": "missing_custody", "nbim_value": "present", "custody_value": "missing"}]
            elif custody_entry and not nbim_entry:
                account_data["mismatches"] = [{"field": "missing_nbim", "nbim_value": "missing", "custody_value": "present"}]
            else:
                account_data["mismatches"] = []

# ---------------------------
# Main parser
# ---------------------------
def parse_data(custody_raw: pd.DataFrame, nbim_raw: pd.DataFrame):
    """
    Main parser function.
    - Normalizes data from both sources
    - Adds mismatch analysis for comparable fields only
    - Returns structured event data with full entry details for analysis
    """
    nbim = normalize_nbim(nbim_raw)
    custody = normalize_custody(custody_raw)
    facts = pd.concat([nbim, custody], ignore_index=True)

    # normalize account ids
    facts["account_id"] = facts["account_id"].astype(str).str.strip()
    facts.loc[facts["account_id"].isin(["", "nan", "none", "None"]), "account_id"] = None

    events = {}

    for _, event_row in facts.iterrows():
        event_key = event_row["coac_event_key"]
        if pd.isna(event_key):
            continue  # skip lines with no event key

        account_id = event_row["account_id"]
        account_key = "_NO_ACCOUNT_" if account_id is None else str(account_id)
        side = event_row["source"]

        if event_key not in events:
            events[event_key] = {
                "coac_event_key": event_key,
                "accounts": {}
            }
        event = events[event_key]

        if account_key not in event["accounts"]:
            event["accounts"][account_key] = {
                "NBIM": None,
                "Custody": None,
            }

        entry = {
            "row_id": int(event_row.get("source_row")) if event_row.get("source_row") is not None and pd.notna(event_row.get("source_row")) else None,
            # Basic identifiers
            "isin": event_row.get("isin"),
            "sedol": event_row.get("sedol"),
            "ticker": event_row.get("ticker"),
            "ex_date": event_row.get("ex_date"),
            "pay_date": event_row.get("pay_date"),
            "currency": event_row.get("currency"),
            "settlement_currency": event_row.get("settlement_currency"),
            "custodian": event_row.get("custodian"),
            "company_name": event_row.get("company_name"),
            "instrument_description": event_row.get("instrument_description"),
            "organisation_name": event_row.get("organisation_name"),
            # Dividend and amounts
            "dividend_rate": event_row.get("dividend_rate"),
            "gross_amount": event_row.get("gross_amount"),
            "net_amount": event_row.get("net_amount"),
            "settlement_net_amount": event_row.get("settlement_net_amount"),
            "withholding_tax": event_row.get("withholding_tax"),
            "withholding_rate": event_row.get("withholding_rate"),
            "total_tax_rate": event_row.get("total_tax_rate"),
            # Position fields - Critical for reconciliation
            "quantity": event_row.get("quantity"),
            "holding_quantity": event_row.get("holding_quantity"),
            "loan_quantity": event_row.get("loan_quantity"),
            "lending_percentage": event_row.get("lending_percentage"),
            # FX and cross-currency fields
            "fx_rate": event_row.get("fx_rate"),
            "fx_rate_to_portfolio": event_row.get("fx_rate_to_portfolio"),
            "is_cross_currency_reversal": event_row.get("is_cross_currency_reversal"),
            # Tax fields - Critical for complex tax analysis
            "local_tax": event_row.get("local_tax"),
            "local_tax_settlement": event_row.get("local_tax_settlement"),
            # Restitution fields - Critical for Swiss dividend analysis
            "restitution_payment": event_row.get("restitution_payment"),
            "restitution_amount": event_row.get("restitution_amount"),
            "restitution_rate": event_row.get("restitution_rate"),
            # Portfolio fields - For comprehensive analysis
            "portfolio_gross_amount": event_row.get("portfolio_gross_amount"),
            "portfolio_net_amount": event_row.get("portfolio_net_amount"),
            "portfolio_withholding_tax": event_row.get("portfolio_withholding_tax"),
        }

        event["accounts"][account_key][side] = entry

    # Add mismatch analysis
    add_mismatch_analysis(events)
    
    event_data = list(events.values())
    for event in event_data:
        for account_key, account_values in event['accounts'].items():
            if account_values.get('mismatches'):
                print(f"Field mismatches for event {event['coac_event_key']}, account {account_key}:")
                for mismatch in account_values['mismatches']:
                    print(f"  {mismatch['field']}: {mismatch['nbim_value']} ≠ {mismatch['custody_value']}")
            
    # Return Python objects (easy to work with, and can be converted to JSON for LLM later)
    return event_data

