import pandas as pd
from manager_agent import ManagerAgent
from prioritization_agent import PrioritizationAgent
from parse_data import parse_data

def run_reconciliation_pipeline(custody_df: pd.DataFrame, nbim_df: pd.DataFrame):
    event_data = parse_data(custody_df, nbim_df)
    print("---Data loaded and parsed---")

    breaks = []

    # Classify reconciliation breaks
    for event in event_data:
        event_key = event.get("coac_event_key")
        print(f"---Examining event key: {event_key}---")
        
        manager_agent = ManagerAgent(event)
        response_dict = manager_agent.run()

        if response_dict.get("status") == "failed":
            print(f"Failed to classify event key: {event_key}")
            print(f"Response: {response_dict}")
            continue
            # OR: throw error and exit program

        if response_dict.get("is_break"):
            response_dict["coac_event_key"] = event_key
            response_dict["event"] = event
            breaks.append(response_dict)
            print(f"Break detected: {response_dict['classification']}")
        
        print(f"---Finished event key: {event_key}---")

    # Prioritize break events
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

def print_final_result(result):
    print("--------------------------------------")
    print("---Discovered reconciliation breaks---")
    for break_event in result:
        print(f"Event Key: {break_event.get('coac_event_key')}")
        print(f"    Classification: {break_event.get('classification')}")
        print(f"    Materiality: {break_event.get('materiality')}")
        print(f"    Priority: {break_event.get('priority')}")
        print(f"    Root Cause: {break_event.get('brief_summary_of_root_cause')}")
        print(f"    Consequence: {break_event.get('consequence')}")
        print("---")

def main():
    # Read data
    custody_df = pd.read_csv("./data/CUSTODY_Dividend_bookings 1.csv", sep=";")
    nbim_df = pd.read_csv("./data/NBIM_Dividend_bookings 1.csv", sep=";")
    result = run_reconciliation_pipeline(custody_df, nbim_df)
    print_final_result(result)

if __name__ == "__main__":
    main()