import pandas as pd
from evidence_analyst_agent import EvidenceAnalystAgent
from conclusion_agent import ConclusionAgent
from prioritization_agent import PrioritizationAgent
from parse_data import parse_data

def run_reconciliation_pipeline(custody_df: pd.DataFrame, nbim_df: pd.DataFrame):
    event_data = parse_data(custody_df, nbim_df)
    print("---Data loaded and parsed---")

    breaks = []

    # Classify reconciliation breaks using two-stage analysis
    for event in event_data:
        event_key = event.get("coac_event_key")
        print(f"---Examining event key: {event_key}---")
        
        # Stage 1: Evidence Analysis
        evidence_agent = EvidenceAnalystAgent(event)
        evidence_analysis = evidence_agent.run()
        
        if evidence_analysis.get("status") == "failed":
            print(f"Failed to analyze evidence for event key: {event_key}")
            print(f"Response: {evidence_analysis}")
            continue
        
        # Stage 2: Conclusion
        conclusion_agent = ConclusionAgent(event, evidence_analysis)
        classification_conclusion_dict = conclusion_agent.run()

        if classification_conclusion_dict.get("status") == "failed":
            print(f"Failed to make conclusion for event key: {event_key}")
            print(f"Response: {classification_conclusion_dict}")
            continue

        # If the event is a break, add it to the list of breaks
        if classification_conclusion_dict.get("is_break"):
            classification_conclusion_dict["coac_event_key"] = event_key
            classification_conclusion_dict["event"] = event
            breaks.append(classification_conclusion_dict)
            print(f"Break detected: {classification_conclusion_dict['classification']}")
        
        print(f"---Finished event key: {event_key}---")

    # Stage 3:Prioritize break events
    prioritized_breaks = []
    for break_event in breaks:
        event_key = break_event.get("coac_event_key")
        print(f"---Prioritizing event key: {event_key}---")
        
        prioritization_agent = PrioritizationAgent(break_event)
        priority_response = prioritization_agent.run()
        
        if priority_response.get("status") == "failed":
            print(f"Failed to prioritize event key: {event_key}")
            print(f"Response: {priority_response}")
            # Continue with default priority if prioritization fails
            priority_response = {
                "materiality": "Unknown",
                "consequence": "Unknown", 
                "priority": "Medium"
            }
        
        # Add prioritization fields to the break event
        break_event.update(priority_response)
        prioritized_breaks.append(break_event)
        print(f"Priority assigned: {priority_response.get('priority')}")
        print(f"---Finished prioritizing event key: {event_key}---")

    # Sort breaks by priority (High -> Medium -> Low)
    priority_order = {"High": 1, "Medium": 2, "Low": 3}
    sorted_breaks = sorted(prioritized_breaks, 
                          key=lambda x: priority_order.get(x.get("priority", "Medium"), 2))

    # Return sorted list of breaks with priority field, sorted from high priority to low.
    return sorted_breaks

def wrap_field(label, text, indent=4, width=100):
    """Print a field with proper wrapping and indentation."""
    if not text:
        text = "Unknown"
    text = str(text)
    
    # Print first line with label
    available_width = width - len(label) - 2  # -2 for ": "
    if len(text) <= available_width:
        print(f"{' ' * indent}{label}: {text}")
    else:
        # Find last space before width limit
        split_pos = text.rfind(' ', 0, available_width)
        if split_pos == -1:  # No space found, force break
            split_pos = available_width
        print(f"{' ' * indent}{label}: {text[:split_pos]}")
        text = text[split_pos:].lstrip()
        
        # Print continuation lines with proper indentation
        label_indent = indent + len(label) + 2
        while text:
            available_width = width - label_indent
            if len(text) <= available_width:
                print(f"{' ' * label_indent}{text}")
                break
            split_pos = text.rfind(' ', 0, available_width)
            if split_pos == -1:
                split_pos = available_width
            print(f"{' ' * label_indent}{text[:split_pos]}")
            text = text[split_pos:].lstrip()

def print_final_result(result):
    print("-" * 100)
    print("---Discovered reconciliation breaks---")
    
    if not result:
        print("No breaks detected.")
        return
    
    for break_event in result:
        print(f"Event Key: {break_event.get('coac_event_key', 'Unknown')}")
        wrap_field("Classification", break_event.get('classification'))
        wrap_field("Materiality", break_event.get('materiality'))
        wrap_field("Priority", break_event.get('priority'))
        wrap_field("Root Cause", break_event.get('brief_summary_of_root_cause'))
        wrap_field("Evidence", '; '.join(break_event.get('evidence')))
        wrap_field("Consequence", break_event.get('consequence'))
        print("---")

def main():
    # Read data
    custody_df = pd.read_csv("./data/CUSTODY_Dividend_bookings 1.csv", sep=";")
    nbim_df = pd.read_csv("./data/NBIM_Dividend_bookings 1.csv", sep=";")
    result = run_reconciliation_pipeline(custody_df, nbim_df)
    print_final_result(result)

if __name__ == "__main__":
    main()