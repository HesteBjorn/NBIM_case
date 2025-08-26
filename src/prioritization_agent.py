import pandas as pd
import anthropic
import os
import json

class PrioritizationAgent:
    def __init__(self, break_event: dict):
        self.break_event = break_event
        self.return_format = """
        {
            "materiality": "string",
            "consequence": "string", 
            "priority": "string"
        }
        """
        self.system_prompt = self._get_system_prompt(self.break_event, self.return_format)

    def _get_system_prompt(self, break_event: dict, return_format: str):
        prompt = f"""
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
        {return_format}

        The break event you are prioritizing:
        Event Key: {break_event.get('coac_event_key', 'Unknown')}
        Classification: {break_event.get('classification', 'Unknown')}
        Root Cause: {break_event.get('brief_summary_of_root_cause', 'Unknown')}
        Event Details: {break_event.get('event', {})}
        """
        return prompt

    def run(self):
        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": self.system_prompt},
                    {"role": "assistant", "content": "{"}  # Prefill first token of JSON format.
                ],
            )
            response_text = "{"+response.content[0].text
            response_dict = json.loads(response_text)
            print(f"Prioritization for event {self.break_event.get('coac_event_key')}: {response_text}")

        except Exception as e:
            print(f"Error prioritizing event {self.break_event.get('coac_event_key')}: {e}")
            return {"status": "failed", "error": str(e)}
        
        return response_dict
