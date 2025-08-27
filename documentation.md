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

