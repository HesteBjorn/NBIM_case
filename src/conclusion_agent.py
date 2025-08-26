import pandas as pd
import anthropic
import os
import json

class ConclusionAgent:
    def __init__(self, event: dict, evidence_analysis: dict):
        self.event = event
        self.evidence_analysis = evidence_analysis
        self.return_format = """
        {
            "evidence": ["string"],
            "is_break": true,
            "classification": "string",
            "brief_summary_of_root_cause": "string"
        }
        """
        self.system_prompt = self._get_system_prompt(self.event, self.evidence_analysis, self.return_format)

    def _get_system_prompt(self, event: dict, evidence_analysis: dict, return_format: str):
        prompt = f"""
        You are a reconciliation analyst in the conclusion phase. You have been provided with detailed evidence analysis from a colleague.

        Based on the evidence and hypothesis provided, make a definitive classification:
        - is_break: true if this represents a genuine reconciliation break, false if not
        - classification: brief category of the issue (e.g., "Tax Discrepancy", "Data Quality", "Timing Difference")
        - brief_summary_of_root_cause: concise explanation of what caused the issue

        Important: If data is consistent in actual meaning but naming conventions differ, this is NOT a break.
        Only include the evidence that is relevant to the classification.
        You are the judge that is supposed to make the final call on whether this is a break or not.

        Pass through the evidence list exactly as provided by the evidence analyst.

        Output strictly valid JSON matching the provided schema. Do not restate inputs.

        The return format of your output should be JSON matching this pattern:
        {return_format}

        Evidence Analysis from colleague:
        Evidence: {evidence_analysis.get('evidence', [])}
        Hypothesis: {evidence_analysis.get('hypothesis', 'No hypothesis provided')}

        Original coac event for reference:
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
                    {"role": "user", "content": self.system_prompt},
                    {"role": "assistant", "content": "{"}
                ],
            )
            response_text = "{"+response.content[0].text
            response_dict = json.loads(response_text)
            print(f"Conclusion for event {self.event['coac_event_key']}: {response_dict.get('is_break', 'Unknown')} - {response_dict.get('classification', 'Unknown')}")

        except Exception as e:
            print(f"Error making conclusion for event {self.event['coac_event_key']}: {e}")
            return {"status": "failed", "error": str(e)}
        
        return response_dict
