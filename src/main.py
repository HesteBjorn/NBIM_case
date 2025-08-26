import pandas as pd
from manager_agent import ManagerAgent
from parse_data import parse_data

def main():
    # Read data
    custody_df = pd.read_csv("./data/CUSTODY_Dividend_bookings 1.csv", sep=";")
    nbim_df = pd.read_csv("./data/NBIM_Dividend_bookings 1.csv", sep=";")
    event_data = parse_data(custody_df, nbim_df)
    print("---Data loaded and parsed---")

    breaks = []

    # Classify reconciliation breaks
    for event in event_data:
        event_key = event.get("coac_event_key")
        print(f"---Examining event key: {event_key}---")
        
        manager_agent = ManagerAgent(event)
        response_dict = manager_agent.run()

        if response_dict.get("is_break"):
            response_dict["coac_event_key"] = event_key
            breaks.append(response_dict)
            print(f"Break detected: {response_dict['brief_summary_of_root_cause']}")
        
        print(f"---Finished event key: {event_key}---")

    # Prioritize break events
    pass

if __name__ == "__main__":
    main()