import pandas as pd
from manager_agent import ManagerAgent
from parse_data import parse_data

def main():
    # Read data
    custody_df = pd.read_csv("./data/CUSTODY_Dividend_bookings 1.csv", sep=";")
    nbim_df = pd.read_csv("./data/NBIM_Dividend_bookings 1.csv", sep=";")
    event_data = parse_data(custody_df, nbim_df)
    print("---Data loaded and parsed---")

    # Classify reconciliation breaks
    for event in event_data:
        event_key = event.get("coac_event_key")
        print(f"---Examining event key: {event_key}---")
        
        manager_agent = ManagerAgent(event)
        is_break, classification, brief_summary_of_root_cause = manager_agent.run()
        print(f"---Finished event key: {event_key}---")

    # Prioritize events
    pass

if __name__ == "__main__":
    main()