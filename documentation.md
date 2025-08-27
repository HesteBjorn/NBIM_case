# Documentation

## Agent architecture and Approach

This solution was focused on issue detection and prioritization. Automated remediation (automatically fixing the tables) was left a low priority for the prototype as I assumed this process required more domain knowledge to know which data source to trust and to fix the error, and that the unpredictability of LLMs may cover up the problems and being harder to detect. See section `Possible approaches for automatic remediation` below for how I would approach this under different assumptions.

Step-wise-process of classification and prioritization:

4 agents:
- EvidenceAnalyst. Scans for mismatches, recieves feedback from critic.
- Critic. Evaluates EvidenceAnalyst against the underlying data to look for hallucinations or missed details, and gives feedback. This evaluation goes in a loop until the critic is satisfied.
- Conclusion. Concludes the evidence to a simple "true/false", 
- Prioritization. First summarizes materiality. Then sets "High", "Medium", "Low" priority to each event.

**Step 1, Rule-based matching of table columns:**  Map corresponding columns to the same name based on pre-defined rules/mappings (assumes we know the table format, which can be found by humans or using LLMs). Add this mismatch-field to the data.

**Step 2, Evidence Analyst Agent and Critic agent loop:**
Each event is processed individually and sent to an agent with only purpose to gather evidence of mismatching, and create a hypothesis based on this.

**Step 3: CriticAgent evaluates EvidenceAnalyst:** The output from EvidenceAnalyst is sent to a CriticAgent, which provides feedback based on if it finds hallucinations, missed details, or poor structure.

The critic also outputs and approval field. If the critic overall approves the output, we proceed in the process. If not, we go back to **Step 2** and add the feedback to the new EvidenceAnalyst.

**Step 4: ConclusionAgent:** The ConclusionAgent takes the final approved output from the EvidenceAgent and summarizes it down to three fields: "is_break" (true/false), "classification" (A few words), "brief_summary_of_root_cause": (Short summary description).

If the is_break is False, no issues has been found, and the event is taken out of the process. If is_break is True, we proceed in the process to the Prioritization Agent.


**Step 5: The PrioritizationAgent:** The prioritization agent first summarizes the Materiality in up to three units. Then it evaluates Financial or Operational consequence. Finally it assigns the event a priority label "High", "Medium" or "Low".

**The final output** is the list output from the Prioritization agent, which is a prioritied list of events categorized as a reconciliation break, with fields for materiality, classification of break-type, short description of issue, and the raw list of evidence.

All "high" and "medium" classifications should raise an alert for human intervention.

Any Remediation process to automatically fix the discrepancy may swiftly be built on top of the architechture after this step.

### Possible approaches for automatic remediation: 

As I did not focus on remediation in this prototype, there are a few approaches I would have taken, based on different assumtions.

- *Assumption:* Custody is the proper provider and treated as ground truth. *Remediation strategy:* Simply map back the missing values from custody to the NBIM database. We have the rule-based mapping in our data-preprocessing already
- *Assumption:* Human intervention is necessary. *Remediation strategy:* Alert humans with domain knowledge to inspect the issues detected.
- *Assumption:* LLM's can do this job automatically. *Rematiation Strategy:* Then I assume we need documentation and more information that is either provided in prompts, or document access through tool-calling. This is in order to avoid making wrong calls, by looking at how things should be, and explainations of the domain of the two data sources Custody and NBIM. We can then add more agents to the end of the pipeline to discover what is the most likely truth, and then fix it. I suggest this sequential agent structure for this:
    - Agent 1: Based on classification, evidence and description of most likely cause from the previous agents, output  explaination of what each data field is likely to come from which source, or what the real value should be such that the tables match. It should be an option to not be able to conclue, which will make Agent 2 alert humans for intervention.
    - Agent 2: Transfer the Agent 1 output to an exact JSON representation of which field should be changed to what. It should be an option to be inconclusive and followingly alert humans.
    - Then, through code (or agent with write permission), execute the table update specified in the exact JSON from Agent 2.


## Example prompts

EvidenceAnalystAgent (with critic feedback):

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
        


Critic agent:
        
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


## Output from final pipeline with critic:

    ---Discovered reconciliation breaks---
    Event Key: 960789012
        Classification: 
        - Tax Discrepancy
        Materiality: 
        - 450,000 KRW ($342 USD), 2% withholding rate difference, 25,000 shares affected
        Priority: 
        - High
        Root Cause: 
        - Fundamental disagreement in Korean withholding tax rate application (22% vs 20%) and local tax treatment, creating cascading differences in net amounts and settlement values totaling over 450,000 KRW difference
        Consequence: 
        - Systematic tax calculation disagreement between NBIM and custody creates regulatory compliance risk for Korean dividend tax reporting. The fundamental withholding rate discrepancy (22% vs 20%) indicates potential misapplication of tax treaties or local regulations, requiring immediate resolution to prevent recurring tax errors and ensure accurate settlement values for Samsung Electronics dividend distribution.
        Evidence: 
        - pay_date mismatch: NBIM shows '2025-05-20' while Custody shows '2025-05-25'
        - net_amount mismatch: NBIM shows 6769950.0 while Custody shows 7220000.0 KRW (difference of 450050.0 KRW)
        - settlement_net_amount mismatch: NBIM shows 5181.5 while Custody shows 5524.27 USD (difference of 342.77 USD)
        - withholding_tax mismatch: NBIM shows 1985500.0 while Custody shows 1805000.0 KRW (difference of 180500.0 KRW)
        - withholding_rate mismatch: NBIM shows 22.0% while Custody shows 20.0% (2 percentage point difference)
        - NBIM has local_tax of 269550.0 KRW while Custody shows local_tax as nan
    ---
    Event Key: 970456789
        Classification: 
        - Financial Amount Discrepancy
        Materiality: 
        - 6200 CHF gross amount difference, 4030 CHF net amount difference, 15000 quantity mismatch
        Priority: 
        - High
        Root Cause: 
        - Account 823456791 shows significant financial amount discrepancies (gross amount 37200 vs 31000, net amount 24180 vs 20150) despite identical quantities, and account 823456790 has quantity mismatches (30000 vs 15000) that cannot be explained by simple securities lending patterns, indicating fundamental calculation methodology differences between systems
        Consequence: 
        - Systematic calculation methodology differences between NBIM and custody systems create ongoing reconciliation risk and potential settlement errors. Financial discrepancies suggest underlying data integrity issues that could compound across multiple dividend events. Requires immediate investigation to prevent reporting inaccuracies and operational disruptions.
        Evidence: 
        - custodian field mismatch across all accounts: NBIM shows 'UBS_SWITZERLAND' while Custody  shows 'CUST/UBSCH'; 
        - quantity field mismatch in account 823456790: NBIM shows 15000.0 while Custody shows 30000.0; 
        - account 823456791 shows matching quantities (10000.0 in both systems) but different gross amounts: NBIM shows 31000.0 while Custody shows37200.0
        - net_amount field mismatch in account 823456791: NBIM shows 20150.0 whileCustody shows 24180.0 
        - settlement_net_amount field mismatch in account 823456791:NBIM shows 20150.0 while Custody shows 24180.0 
        - withholding_tax field mismatch inaccount 823456791: NBIM shows 10850.0 while Custody shows 13020.0
        - holding_quantity field in account 823456791: Custody shows 12000.0 while NBIM shows nan, whereholding_quantity exceeds both systems' quantity values of 10000.0; holding_quantity field in account 823456790: Custody shows 15000.0 (matching NBIM quantity) while NBIM shows nan
        - holding_quantity field in account 823456789: Custody shows 20000.0(matching both systems' quantity) while NBIM shows nan
        - NBIM data contains populated portfolio conversion fields (fx_rate_to_portfolio: 12.4567, portfolio_gross_amount, portfolio_net_amount, portfolio_withholding_tax) while Custody shows these as nan
        - Custody data contains restitution_payment and restitution_amount fields (6000.0,4500.0, 4500.0 across accounts) while NBIM shows these as nan or 0.0;- fx_rate field shows nan in NBIM but 1.0 in Custody across all accounts
        - total_tax_rate shows 35.0 in NBIM but nan in Custody across all accounts
    ---

