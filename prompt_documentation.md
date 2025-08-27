
# Example prompts

## EvidenceAnalystAgent (with critic feedback):

    You are a reconciliation analyst for dividend events, in the evidence-gathering phase. Your task is to thoroughly analyze a coac event and identify all potential discrepancies between NBIM and Custody data sources.

    Focus on:
    1. EVIDENCE: List all specific field mismatches you observe (be very specific about field names and values)
    2. HYPOTHESIS: Provide a detailed, comprehensive discussion of what might be wrong and what could have happened. Consider multiple scenarios, root causes, and systemic vs isolated issues.

    Do not make final conclusions about whether this is a break - focus on thorough analysis and evidence gathering.

    Evidence should be simple, factual observations. Each point should identify a specific mismatch.
    Hypothesis should be a detailed analytical discussion exploring possible explanations, implications, and scenarios.

    Output strictly valid JSON matching the provided schema. Do not restate inputs.
    
    
        You have been evaluated by a critic agent. Your previous response was:
        {'evidence': ["custodian field mismatch across all accounts: NBIM shows 'UBS_SWITZERLAND' while Custody shows 'CUST/UBSCH'", 'quantity field mismatch in account 823456790: NBIM shows 15000.0 while Custody shows 30000.0', 'gross_amount field mismatch in account 823456791: NBIM shows 31000.0 while Custody shows 37200.0', 'net_amount field mismatch in account 823456791: NBIM shows 20150.0 while Custody shows 24180.0', 'settlement_net_amount field mismatch in account 823456791: NBIM shows 20150.0 while Custody shows 24180.0', 'withholding_tax field mismatch in account 823456791: NBIM shows 10850.0 while Custody shows 13020.0', 'NBIM data contains populated portfolio conversion fields (fx_rate_to_portfolio: 12.4567, portfolio_gross_amount, portfolio_net_amount, portfolio_withholding_tax) while Custody shows these as nan', 'Custody data contains restitution_payment and restitution_amount fields (6000.0, 4500.0, 4500.0 across accounts) while NBIM shows these as nan or 0.0', 'Custody data shows holding_quantity values (20000.0, 15000.0, 12000.0) while NBIM shows these as nan', 'fx_rate field shows nan in NBIM but 1.0 in Custody across all accounts', 'total_tax_rate shows 35.0 in NBIM but nan in Custody across all accounts'], 'hypothesis': "This coac event exhibits multiple systematic discrepancies suggesting fundamental differences in data processing or source systems between NBIM and Custody. The custodian naming convention difference ('UBS_SWITZERLAND' vs 'CUST/UBSCH') indicates potential system mapping or reference data misalignment, which could be a consistent issue affecting all UBS Switzerland positions. The quantity discrepancy in account 823456790 where Custody shows double the NBIM quantity (30000 vs 15000) could indicate a securities lending scenario where Custody is reporting total entitled quantity while NBIM reports only the held portion, supported by Custody's populated holding_quantity field showing the actual held amount matching NBIM's quantity. The financial amount discrepancies in account 823456791 (gross_amount 37200 vs 31000, resulting in proportional differences in net amounts and withholding tax) suggest either different calculation methodologies or the inclusion of additional dividend components in Custody data. The presence of restitution amounts in Custody data (4500-6000 CHF across accounts) while absent in NBIM could indicate that Custody is reflecting anticipated tax reclaims or treaty benefits that NBIM hasn't yet incorporated, possibly due to different processing timelines or approval workflows for Swiss withholding tax optimization. The portfolio currency conversion fields being populated only in NBIM suggests different reporting requirements, with NBIM maintaining NOK portfolio reporting while Custody focuses on local currency settlement. The fx_rate differences (nan vs 1.0) and total_tax_rate inconsistencies may reflect different system defaults or calculation stages, where Custody uses explicit 1.0 for same-currency transactions while NBIM leaves cross-currency fields unpopulated. These patterns suggest either a timing difference in data processing stages, different interpretations of securities lending impacts on dividend entitlements, or systematic differences in how Swiss dividend tax optimization is handled between the systems."}

    The critic's feedback to address is:
    • Evidence item claiming 'quantity field mismatch in account 823456790' is incorrect - the data shows NBIM quantity 15000.0 vs Custody quantity 30000.0, which matches your claim, but you failed to note that account 823456791 shows matching quantities (10000.0 in both systems)
    • Evidence item claiming 'holding_quantity shows (20000.0, 15000.0, 12000.0) while NBIM shows these as nan' contains an error - account 823456791 shows holding_quantity of 12000.0 in Custody vs quantity of 10000.0, not matching as your hypothesis suggests
    • Your hypothesis incorrectly states that 'Custody's populated holding_quantity field showing the actual held amount matching NBIM's quantity' - this is only true for account 823456790, not for 823456791 where holding_quantity (12000.0) exceeds both systems' quantity values
    • You missed documenting the most significant discrepancy: account 823456791 shows identical quantities (10000.0) but different gross amounts, which contradicts the securities lending explanation and suggests a calculation methodology difference
    • Evidence correctly identifies the custodian naming mismatch and restitution payment differences
    • Evidence correctly identifies portfolio conversion fields populated only in NBIM
    • Hypothesis needs revision to address why account 823456791 has identical quantities but different financial amounts, and why holding_quantity exceeds quantity in that account

        Please revise your analysis to address the critic's feedback above.

    The return format of your output should be JSON matching this pattern:
    
    {
        "evidence": ["string"],
        "hypothesis": "string"
    }
    

    The coac event you are analyzing is:
    {'coac_event_key': 970456789, 'accounts': {'823456789': {'NBIM': {'row_id': 2, 'isin': 'CH0038863350', 'sedol': 7196907, 'ticker': 'NESN SW', 'ex_date': '2025-04-25', 'pay_date': '2025-04-29', 'currency': 'CHF', 'settlement_currency': 'CHF', 'custodian': 'UBS_SWITZERLAND', 'company_name': 'Nestle SA', 'instrument_description': 'NESTLE SA', 'organisation_name': 'Nestle SA', 'dividend_rate': 3.1, 'gross_amount': 62000.0, 'net_amount': 40300.0, 'settlement_net_amount': 40300.0, 'withholding_tax': 21700.0, 'withholding_rate': 35.0, 'total_tax_rate': 35.0, 'quantity': 20000.0, 'holding_quantity': nan, 'loan_quantity': nan, 'lending_percentage': nan, 'fx_rate': nan, 'fx_rate_to_portfolio': 12.4567, 'is_cross_currency_reversal': None, 'local_tax': 0.0, 'local_tax_settlement': 0.0, 'restitution_payment': nan, 'restitution_amount': nan, 'restitution_rate': 0.0, 'portfolio_gross_amount': 772559.84, 'portfolio_net_amount': 502163.9, 'portfolio_withholding_tax': 270395.94}, 'Custody': {'row_id': 2, 'isin': 'CH0038863350', 'sedol': 7196907, 'ticker': None, 'ex_date': '2025-04-25', 'pay_date': '2025-04-29', 'currency': 'CHF', 'settlement_currency': 'CHF', 'custodian': 'CUST/UBSCH', 'company_name': None, 'instrument_description': None, 'organisation_name': None, 'dividend_rate': 3.1, 'gross_amount': 62000.0, 'net_amount': 40300.0, 'settlement_net_amount': 40300.0, 'withholding_tax': 21700.0, 'withholding_rate': 35.0, 'total_tax_rate': nan, 'quantity': 20000.0, 'holding_quantity': 20000.0, 'loan_quantity': 0.0, 'lending_percentage': 0.0, 'fx_rate': 1.0, 'fx_rate_to_portfolio': nan, 'is_cross_currency_reversal': False, 'local_tax': nan, 'local_tax_settlement': nan, 'restitution_payment': 6000.0, 'restitution_amount': 6000.0, 'restitution_rate': nan, 'portfolio_gross_amount': nan, 'portfolio_net_amount': nan, 'portfolio_withholding_tax': nan}, 'mismatches': [{'field': 'custodian', 'nbim_value': 'UBS_SWITZERLAND', 'custody_value': 'CUST/UBSCH'}]}, '823456790': {'NBIM': {'row_id': 3, 'isin': 'CH0038863350', 'sedol': 7196907, 'ticker': 'NESN SW', 'ex_date': '2025-04-25', 'pay_date': '2025-04-29', 'currency': 'CHF', 'settlement_currency': 'CHF', 'custodian': 'UBS_SWITZERLAND', 'company_name': 'Nestle SA', 'instrument_description': 'NESTLE SA', 'organisation_name': 'Nestle SA', 'dividend_rate': 3.1, 'gross_amount': 46500.0, 'net_amount': 30225.0, 'settlement_net_amount': 30225.0, 'withholding_tax': 16275.0, 'withholding_rate': 35.0, 'total_tax_rate': 35.0, 'quantity': 15000.0, 'holding_quantity': nan, 'loan_quantity': nan, 'lending_percentage': nan, 'fx_rate': nan, 'fx_rate_to_portfolio': 12.4567, 'is_cross_currency_reversal': None, 'local_tax': 0.0, 'local_tax_settlement': 0.0, 'restitution_payment': nan, 'restitution_amount': nan, 'restitution_rate': 0.0, 'portfolio_gross_amount': 579419.88, 'portfolio_net_amount': 376622.92, 'portfolio_withholding_tax': 202796.96}, 'Custody': {'row_id': 3, 'isin': 'CH0038863350', 'sedol': 7196907, 'ticker': None, 'ex_date': '2025-04-25', 'pay_date': '2025-04-29', 'currency': 'CHF', 'settlement_currency': 'CHF', 'custodian': 'CUST/UBSCH', 'company_name': None, 'instrument_description': None, 'organisation_name': None, 'dividend_rate': 3.1, 'gross_amount': 46500.0, 'net_amount': 30225.0, 'settlement_net_amount': 30225.0, 'withholding_tax': 16275.0, 'withholding_rate': 35.0, 'total_tax_rate': nan, 'quantity': 30000.0, 'holding_quantity': 15000.0, 'loan_quantity': 0.0, 'lending_percentage': 0.0, 'fx_rate': 1.0, 'fx_rate_to_portfolio': nan, 'is_cross_currency_reversal': False, 'local_tax': nan, 'local_tax_settlement': nan, 'restitution_payment': 4500.0, 'restitution_amount': 4500.0, 'restitution_rate': nan, 'portfolio_gross_amount': nan, 'portfolio_net_amount': nan, 'portfolio_withholding_tax': nan}, 'mismatches': [{'field': 'custodian', 'nbim_value': 'UBS_SWITZERLAND', 'custody_value': 'CUST/UBSCH'}, {'field': 'quantity', 'nbim_value': 15000.0, 'custody_value': 30000.0}]}, '823456791': {'NBIM': {'row_id': 4, 'isin': 'CH0038863350', 'sedol': 7196907, 'ticker': 'NESN SW', 'ex_date': '2025-04-25', 'pay_date': '2025-04-29', 'currency': 'CHF', 'settlement_currency': 'CHF', 'custodian': 'UBS_SWITZERLAND', 'company_name': 'Nestle SA', 'instrument_description': 'NESTLE SA', 'organisation_name': 'Nestle SA', 'dividend_rate': 3.1, 'gross_amount': 31000.0, 'net_amount': 20150.0, 'settlement_net_amount': 20150.0, 'withholding_tax': 10850.0, 'withholding_rate': 35.0, 'total_tax_rate': 35.0, 'quantity': 10000.0, 'holding_quantity': nan, 'loan_quantity': nan, 'lending_percentage': nan, 'fx_rate': nan, 'fx_rate_to_portfolio': 12.4567, 'is_cross_currency_reversal': None, 'local_tax': 0.0, 'local_tax_settlement': 0.0, 'restitution_payment': nan, 'restitution_amount': nan, 'restitution_rate': 0.0, 'portfolio_gross_amount': 386279.92, 'portfolio_net_amount': 251081.95, 'portfolio_withholding_tax': 135197.97}, 'Custody': {'row_id': 4, 'isin': 'CH0038863350', 'sedol': 7196907, 'ticker': None, 'ex_date': '2025-04-25', 'pay_date': '2025-04-29', 'currency': 'CHF', 'settlement_currency': 'CHF', 'custodian': 'CUST/UBSCH', 'company_name': None, 'instrument_description': None, 'organisation_name': None, 'dividend_rate': 3.1, 'gross_amount': 37200.0, 'net_amount': 24180.0, 'settlement_net_amount': 24180.0, 'withholding_tax': 13020.0, 'withholding_rate': 35.0, 'total_tax_rate': nan, 'quantity': 10000.0, 'holding_quantity': 12000.0, 'loan_quantity': 0.0, 'lending_percentage': 0.0, 'fx_rate': 1.0, 'fx_rate_to_portfolio': nan, 'is_cross_currency_reversal': False, 'local_tax': nan, 'local_tax_settlement': nan, 'restitution_payment': 4500.0, 'restitution_amount': 4500.0, 'restitution_rate': nan, 'portfolio_gross_amount': nan, 'portfolio_net_amount': nan, 'portfolio_withholding_tax': nan}, 'mismatches': [{'field': 'custodian', 'nbim_value': 'UBS_SWITZERLAND', 'custody_value': 'CUST/UBSCH'}, {'field': 'gross_amount', 'nbim_value': 31000.0, 'custody_value': 37200.0}, {'field': 'net_amount', 'nbim_value': 20150.0, 'custody_value': 24180.0}, {'field': 'settlement_net_amount', 'nbim_value': 20150.0, 'custody_value': 24180.0}, {'field': 'withholding_tax', 'nbim_value': 10850.0, 'custody_value': 13020.0}]}}}
        


## CriticAgent:
        
    You are an evaluator critic agent supervising an Evidence Analyst agent. The Evidence Analyst agent is trying to find reconciliation breaks in dividend events.
    Your input is the output of the other agent and the processed event data that the analyst used as input.
    Your goal is to approve the evidence/conclusions and give concise feedback to the Evidence Analyst agent, making sure it makes correct analysis, and does not hallucinate.

    Your responsibilities include:
    - Make sure the other Analyst's presented evidence aligns with the data. There is no hallucination.
    - Make sure the Analyst's assumptions and conclusions are reasonable with the given data, and in the given domain.
    - Make sure all the relevant information has been captured.
    - Make sure no irrelevant information or false leads has been included.
    - Approve the evidence and conclusions if they are valid and reasonable.

    Your feedback string should be in bullet point format, and is passed to the analyst for its next iteration.

    DO NOT approve unless you are completely satisfied with all evidence and analysis.

    After you have approved the evidence, we accept the evidence, and the next agent acting after you in the process will draw conclusions on whether this is a reconciliation break or not, and summarize it.

    Your output should be strict JSON format:
    
    {
        "feedback_string_to_evidence_analyst_agent": "string",
        "approved": "boolean"
    }
    

    The agent output you are going to evaluate had output:
    {'evidence': ["custodian field mismatch: NBIM shows 'JPMORGAN_CHASE' while Custody shows 'CUST/JPMORGANUS'", "ticker field: NBIM has 'AAPL' while Custody has None/null value", "company_name field: NBIM has 'Apple Inc' while Custody has None/null value", "instrument_description field: NBIM has 'APPLE INC' while Custody has None/null value", "organisation_name field: NBIM has 'Apple Inc' while Custody has None/null value", 'total_tax_rate field: NBIM has 15.0 while Custody has nan/null value', 'holding_quantity field: NBIM has nan/null while Custody has 1500000.0', 'loan_quantity field: NBIM has nan/null while Custody has 0.0', 'lending_percentage field: NBIM has nan/null while Custody has 0.0', 'fx_rate field: NBIM has nan/null while Custody has 1.0', 'fx_rate_to_portfolio field: NBIM has 11.2345 while Custody has nan/null', 'is_cross_currency_reversal field: NBIM has None while Custody has False', 'local_tax field: NBIM has 0.0 while Custody has nan/null', 'local_tax_settlement field: NBIM has 0.0 while Custody has nan/null', 'restitution_payment field: NBIM has nan/null while Custody has 0.0', 'restitution_amount field: NBIM has nan/null while Custody has 0.0', 'restitution_rate field: NBIM has 0.0 while Custody has nan/null', 'portfolio_gross_amount field: NBIM has 4212937.5 while Custody has nan/null', 'portfolio_net_amount field: NBIM has 3580996.88 while Custody has nan/null', 'portfolio_withholding_tax field: NBIM has 631940.63 while Custody has nan/null'], 'hypothesis': "This appears to be a case where the core dividend event details are aligned between both systems, but there are significant differences in data completeness and field population strategies. The custodian name discrepancy ('JPMORGAN_CHASE' vs 'CUST/JPMORGANUS') suggests different naming conventions or data source mappings between the systems, which could indicate a configuration issue or different reference data sources. The extensive pattern of complementary null/populated fields suggests the systems may have different data responsibilities or acquisition methods - NBIM appears to focus more on descriptive information (company names, tickers) and portfolio-level calculations, while Custody emphasizes operational details like holdings breakdown and FX rates. The fx_rate difference is particularly notable: Custody shows 1.0 (suggesting USD-to-USD) while NBIM shows nan, but NBIM has fx_rate_to_portfolio of 11.2345, indicating NBIM may be performing portfolio currency conversion (possibly to NOK) while Custody maintains base currency rates. This could represent different stages in the processing pipeline or different functional responsibilities. The holding_quantity, loan_quantity, and lending_percentage being populated only in Custody suggests this system maintains the securities lending details, while NBIM may receive net position information. The portfolio amounts being exclusive to NBIM (4.2M gross, 3.6M net) with the fx_rate_to_portfolio suggests NBIM performs the final portfolio currency conversion calculations. This pattern could indicate normal system division of labor, but the custodian naming discrepancy and some inconsistencies in null handling (like total_tax_rate) might suggest integration or mapping issues that could lead to reconciliation challenges."}

    The data you are cross checking it against is:
    {'coac_event_key': 950123456, 'accounts': {'501234567': {'NBIM': {'row_id': 0, 'isin': 'US0378331005', 'sedol': 2046251, 'ticker': 'AAPL', 'ex_date': '2025-02-07', 'pay_date': '2025-02-14', 'currency': 'USD', 'settlement_currency': 'USD', 'custodian': 'JPMORGAN_CHASE', 'company_name': 'Apple Inc', 'instrument_description': 'APPLE INC', 'organisation_name': 'Apple Inc', 'dividend_rate': 0.25, 'gross_amount': 375000.0, 'net_amount': 318750.0, 'settlement_net_amount': 318750.0, 'withholding_tax': 56250.0, 'withholding_rate': 15.0, 'total_tax_rate': 15.0, 'quantity': 1500000.0, 'holding_quantity': nan, 'loan_quantity': nan, 'lending_percentage': nan, 'fx_rate': nan, 'fx_rate_to_portfolio': 11.2345, 'is_cross_currency_reversal': None, 'local_tax': 0.0, 'local_tax_settlement': 0.0, 'restitution_payment': nan, 'restitution_amount': nan, 'restitution_rate': 0.0, 'portfolio_gross_amount': 4212937.5, 'portfolio_net_amount': 3580996.88, 'portfolio_withholding_tax': 631940.63}, 'Custody': {'row_id': 0, 'isin': 'US0378331005', 'sedol': 2046251, 'ticker': None, 'ex_date': '2025-02-07', 'pay_date': '2025-02-14', 'currency': 'USD', 'settlement_currency': 'USD', 'custodian': 'CUST/JPMORGANUS', 'company_name': None, 'instrument_description': None, 'organisation_name': None, 'dividend_rate': 0.25, 'gross_amount': 375000.0, 'net_amount': 318750.0, 'settlement_net_amount': 318750.0, 'withholding_tax': 56250.0, 'withholding_rate': 15.0, 'total_tax_rate': nan, 'quantity': 1500000.0, 'holding_quantity': 1500000.0, 'loan_quantity': 0.0, 'lending_percentage': 0.0, 'fx_rate': 1.0, 'fx_rate_to_portfolio': nan, 'is_cross_currency_reversal': False, 'local_tax': nan, 'local_tax_settlement': nan, 'restitution_payment': 0.0, 'restitution_amount': 0.0, 'restitution_rate': nan, 'portfolio_gross_amount': nan, 'portfolio_net_amount': nan, 'portfolio_withholding_tax': nan}, 'mismatches': [{'field': 'custodian', 'nbim_value': 'JPMORGAN_CHASE', 'custody_value': 'CUST/JPMORGANUS'}]}}}

## ConclusionAgent:

    You are a reconciliation analyst for dividend events, in the conclusion phase. You have been provided with detailed evidence analysis from a colleague.
    The overall goal is to thoroughly analyze a coac event and identify all potential discrepancies between NBIM and Custody data sources.
    You are the judge that is supposed to make the final call on whether this is a break or not.

    Based on the evidence and hypothesis provided, make a definitive classification:
    - is_break: true if this represents a genuine reconciliation break, false if not
    - classification: brief category of the issue (e.g., "Tax Discrepancy", "Data Quality", "Timing Difference")
    - brief_summary_of_root_cause: concise explanation of what caused the issue

    Important: If data is consistent in actual meaning but naming conventions differ, this is NOT a break.
    You should base your classification on whether the evidence and hypothesis is enough to make a conclusion that there has been a break.
    Make sure the conclusion is reasonable, and consitutes a real issue.
    Only include the evidence that is relevant to the classification.

    Pass through the evidence list exactly as provided by the evidence analyst.

    Output strictly valid JSON matching the provided schema. Do not restate inputs.

    The return format of your output should be JSON matching this pattern:

    {
        "evidence": ["string"],
        "is_break": true,
        "classification": "string",
        "brief_summary_of_root_cause": "string"
    }


    Evidence Analysis from colleague:
    Evidence: ["Custodian name mismatch: NBIM has custodian='JPMORGAN_CHASE' while Custody has custodian='CUST/JPMORGANUS'", 'FX rate discrepancy: NBIM has fx_rate=nan and fx_rate_to_portfolio=11.2345, while Custody has fx_rate=1.0 and fx_rate_to_portfolio=nan', 'Portfolio amount calculations: NBIM shows portfolio_gross_amount=4212937.5, portfolio_net_amount=3580996.88, portfolio_withholding_tax=631940.63, while Custody shows nan for all portfolio fields', 'Core dividend amounts reconcile: gross_amount (375000.0), net_amount (318750.0), withholding_tax (56250.0), and quantity (1500000.0) match exactly', "Currency fields match: both systems show currency='USD' and settlement_currency='USD'"]
    Hypothesis: This event shows a custodian name format difference and FX rate handling discrepancy, but core dividend calculations reconcile. The custodian mismatch appears to be a naming convention difference for the same entity (JPMorgan Chase). The FX rate difference is notable: Custody correctly shows fx_rate=1.0 for this USD-to-USD transaction, while NBIM has fx_rate_to_portfolio=11.2345, suggesting NBIM applies portfolio-level currency conversion that Custody does not perform. This explains why NBIM has calculated portfolio amounts (4.2M+ gross) while Custody shows nan for all portfolio fields. The core reconciliation break is the custodian naming discrepancy, while the FX and portfolio calculation differences appear to reflect different system architectures - NBIM performing portfolio currency conversion versus Custody operating at transaction level only. Given that the fundamental dividend amounts reconcile exactly, this represents a data format/system design difference rather than a calculation error.

    Original coac event for reference:
    {'coac_event_key': 950123456, 'accounts': {'501234567': {'NBIM': {'row_id': 0, 'isin': 'US0378331005', 'sedol': 2046251, 'ticker': 'AAPL', 'ex_date': '2025-02-07', 'pay_date': '2025-02-14', 'currency': 'USD', 'settlement_currency': 'USD', 'custodian': 'JPMORGAN_CHASE', 'company_name': 'Apple Inc', 'instrument_description': 'APPLE INC', 'organisation_name': 'Apple Inc', 'dividend_rate': 0.25, 'gross_amount': 375000.0, 'net_amount': 318750.0, 'settlement_net_amount': 318750.0, 'withholding_tax': 56250.0, 'withholding_rate': 15.0, 'total_tax_rate': 15.0, 'quantity': 1500000.0, 'holding_quantity': nan, 'loan_quantity': nan, 'lending_percentage': nan, 'fx_rate': nan, 'fx_rate_to_portfolio': 11.2345, 'is_cross_currency_reversal': None, 'local_tax': 0.0, 'local_tax_settlement': 0.0, 'restitution_payment': nan, 'restitution_amount': nan, 'restitution_rate': 0.0, 'portfolio_gross_amount': 4212937.5, 'portfolio_net_amount': 3580996.88, 'portfolio_withholding_tax': 631940.63}, 'Custody': {'row_id': 0, 'isin': 'US0378331005', 'sedol': 2046251, 'ticker': None, 'ex_date': '2025-02-07', 'pay_date': '2025-02-14', 'currency': 'USD', 'settlement_currency': 'USD', 'custodian': 'CUST/JPMORGANUS', 'company_name': None, 'instrument_description': None, 'organisation_name': None, 'dividend_rate': 0.25, 'gross_amount': 375000.0, 'net_amount': 318750.0, 'settlement_net_amount': 318750.0, 'withholding_tax': 56250.0, 'withholding_rate': 15.0, 'total_tax_rate': nan, 'quantity': 1500000.0, 'holding_quantity': 1500000.0, 'loan_quantity': 0.0, 'lending_percentage': 0.0, 'fx_rate': 1.0, 'fx_rate_to_portfolio': nan, 'is_cross_currency_reversal': False, 'local_tax': nan, 'local_tax_settlement': nan, 'restitution_payment': 0.0, 'restitution_amount': 0.0, 'restitution_rate': nan, 'portfolio_gross_amount': nan, 'portfolio_net_amount': nan, 'portfolio_withholding_tax': nan}, 'mismatches': [{'field': 'custodian', 'nbim_value': 'JPMORGAN_CHASE', 'custody_value': 'CUST/JPMORGANUS'}]}}}


## PrioritizationAgent:

    You are a reconciliation analyst for dividend events, comparing Custody data to internal data from NBIM. You are tasked with prioritizing break events based on their impact and urgency.

    Given a reconciliation break event, analyze its materiality, potential consequences, and assign a priority level.
    Output strictly valid JSON matching the provided schema. Do not restate inputs.

    For materiality, consider:
    - Financial impact (amounts, rates, quantities involved)
    - Scope of the issue (single account vs. multiple accounts)
    - Complexity of the mismatch (simple data difference vs. systematic issue)
    - Make the materiality consice, ideally a number with a unit.
    - You can have multiple of these numbers with units, but limit to three.

    For consequence, consider:
    - Financial impact. Is the materiality going to be a costly problem? Is the issue a data issue, or systematic faliure with tangible consequences?
    - Regulatory/compliance implications
    - Operational impact on downstream processes
    - Risk of issue spreading or recurring
    - Impact on reporting accuracy

    For priority, assign exactly one of: "High", "Medium", "Low"
    - High: Urgent financial impact, regulatory risk, or systematic issues
    - Medium: Smaller financial or systematic impact requiring timely attention
    - Low: Minor discrepancies with low immediate impact

    The return format of your output should be JSON matching this pattern:

    {
        "materiality": "string",
        "consequence": "string",
        "priority": "string"
    }


    The break event you are prioritizing:
    Event Key: 960789012
    Classification: Tax Discrepancy
    Root Cause: Fundamental disagreement on Korean withholding tax treatment: NBIM applies 22% withholding tax plus local tax for 25% total tax rate, while Custody applies only 20% withholding tax with no local tax component. This results in material differences in net amounts (KRW 450,050 difference) and settlement amounts. The discrepancy suggests different interpretations of Korean tax regulations or one system applying outdated tax rates.
    Event Details: {'coac_event_key': 960789012, 'accounts': {'712345678': {'NBIM': {'row_id': 1, 'isin': 'KR7005930003', 'sedol': 6771720, 'ticker': '005930 KS', 'ex_date': '2025-03-31', 'pay_date': '2025-05-20', 'currency': 'KRW', 'settlement_currency': 'USD', 'custodian': 'HSBC_KOREA', 'company_name': 'Samsung Electronics Co Ltd', 'instrument_description': 'SAMSUNG ELECTRONICS CO LTD', 'organisation_name': 'Samsung Electronics Co Ltd', 'dividend_rate': 361.0, 'gross_amount': 9025000.0, 'net_amount': 6769950.0, 'settlement_net_amount': 5181.5, 'withholding_tax': 1985500.0, 'withholding_rate': 22.0, 'total_tax_rate': 25.0, 'quantity': 25000.0, 'holding_quantity': nan, 'loan_quantity': nan, 'lending_percentage': nan, 'fx_rate': nan, 'fx_rate_to_portfolio': 0.008234, 'is_cross_currency_reversal': None, 'local_tax': 269550.0, 'local_tax_settlement': 206.26, 'restitution_payment': nan, 'restitution_amount': nan, 'restitution_rate': 0.0, 'portfolio_gross_amount': 74311.85, 'portfolio_net_amount': 55738.63, 'portfolio_withholding_tax': 16348.61}, 'Custody': {'row_id': 1, 'isin': 'KR7005930003', 'sedol': 6771720, 'ticker': None, 'ex_date': '2025-03-31', 'pay_date': '2025-05-25', 'currency': 'KRW USD', 'settlement_currency': 'USD', 'custodian': 'CUST/HSBCKR', 'company_name': None, 'instrument_description': None, 'organisation_name': None, 'dividend_rate': 361.0, 'gross_amount': 9025000.0, 'net_amount': 7220000.0, 'settlement_net_amount': 5524.27, 'withholding_tax': 1805000.0, 'withholding_rate': 20.0, 'total_tax_rate': nan, 'quantity': 25000.0, 'holding_quantity': 23000.0, 'loan_quantity': 2000.0, 'lending_percentage': 8.0, 'fx_rate': 1307.25, 'fx_rate_to_portfolio': nan, 'is_cross_currency_reversal': True, 'local_tax': nan, 'local_tax_settlement': nan, 'restitution_payment': 0.0, 'restitution_amount': 0.0, 'restitution_rate': nan, 'portfolio_gross_amount': nan, 'portfolio_net_amount': nan, 'portfolio_withholding_tax': nan}, 'mismatches': [{'field': 'pay_date', 'nbim_value': '2025-05-20', 'custody_value': '2025-05-25'}, {'field': 'currency', 'nbim_value': 'KRW', 'custody_value': 'KRW USD'}, {'field': 'custodian', 'nbim_value': 'HSBC_KOREA', 'custody_value': 'CUST/HSBCKR'}, {'field': 'net_amount', 'nbim_value': 6769950.0, 'custody_value': 7220000.0}, {'field': 'settlement_net_amount', 'nbim_value': 5181.5, 'custody_value': 5524.27}, {'field': 'withholding_tax', 'nbim_value': 1985500.0, 'custody_value': 1805000.0}, {'field': 'withholding_rate', 'nbim_value': 22.0, 'custody_value': 20.0}]}}}

