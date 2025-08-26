import pandas as pd
from manager_agent import ManagerAgent
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
    pass
    sorted_breaks = []

    # Return sorted list of breaks with priority field, sorted from high priority to low.
    return sorted_breaks

def main():
    # Read data
    custody_df = pd.read_csv("./data/CUSTODY_Dividend_bookings 1.csv", sep=";")
    nbim_df = pd.read_csv("./data/NBIM_Dividend_bookings 1.csv", sep=";")
    result = run_reconciliation_pipeline(custody_df, nbim_df)

if __name__ == "__main__":
    main()