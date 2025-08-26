import pandas as pd
import anthropic
import os
import json

class ManagerAgent:
    def __init__(self, event: dict):
        self.event = event
        self.return_format = """
        {
            "is_break": "boolean",
            "classification": "string",
            "brief_summary_of_root_cause": "string",
        }
        """
        self.system_prompt = self._get_system_prompt(self.event, self.return_format)


    def _get_system_prompt(self, event: dict|list, return_format: str):
        prompt = f"""
        You are a reconciliation analyst. You are tasked with identifying issues in reconciliation.
        Given a single coac event with two data sources NBIM and Custody, output strictly valid JSON matching the provided schema. 
        Do not restate inputs.
        If there are mulitple root causes, return all of them.

        If the data is consistent in actual meaning but naming convensions differ, then it is not a break.

        The return format of your output should be JSON matching this pattern:
        {return_format}

        The coac event you are reconciling is:
        {event}
        """
        return prompt


    def run(self):
        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": self.system_prompt},  # System input.
                    {"role": "assistant", "content": "{"}  # Prefill first token of JSON format.
                ],
            )
            response_text = "{"+response.content[0].text
            response_dict = json.loads(response_text)
            print(f"Response for event {self.event['coac_event_key']}: {response_text}")

        except Exception as e:
            print(f"Error for event {self.event['coac_event_key']}: {e}")
            return {"status": "failed", "error": str(e)}
        
        return response_dict
