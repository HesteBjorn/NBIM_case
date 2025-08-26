import pandas as pd
import anthropic
import os
import json

class CriticAgent:
    def __init__(self, event: dict, evaluated_output: dict):
        self.event = event
        self.evaluated_output = evaluated_output
        self.return_format = """
        {
            "feedback_string_to_evidence_analyst_agent": "string",
            "approved": "boolean"
        }
        """
        self.system_prompt = self._get_system_prompt(self.event, self.evaluated_output, self.return_format)

    def _get_system_prompt(self, event: dict, evaluated_output: dict, return_format: str):
        prompt = f"""
        You are an evaluator critic agent supervising an Evidence Analyst agent. The Evidence Analyst agent is trying to find reconciliation breaks in dividend events.
        Your input is the output of the other agent and the processed event data that the analyst used as input.
        Your goal is to approve the evidence/conclusions and give concise feedback to the Evidence Analyst agent, making sure it makes correct analysis, and does not hallucinate.

        Your responsibilities include:
        - Make sure the other Analyst's presented evidence aligns with the data. There is no hallucination.
        - Make sure the Analyst's assumptions and conclusions are reasonable with the given data, and in the given domain.
        - Make sure all the relevant information has been captured. Only focus on information relevant to the reconciliation break or the hypothesis, keep as little redundant information as possible.
        - Make sure no irrelevant information or false leads has been included.
        - Approve the evidence and conclusions if they are valid and reasonable.

        Your feedback string should be in bullet point format, and is passed to the analyst for its next iteration.

        DO NOT approve unless you are completely satisfied with all evidence and analysis.

        After you have approved the evidence, we accept the evidence, and the next agent acting after you in the process will draw conclusions on whether this is a reconciliation break or not, and summarize it.

        Your output should be strict JSON format:
        {return_format}

        The agent output you are going to evaluate had output:
        {evaluated_output}

        The data you are cross checking it against is:
        {event}
        """
        return prompt

    def run(self):
        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            response = client.messages.create(
                model="claude-opus-4-1-20250805",  # Strong reasoning model.
                max_tokens=3000,
                messages=[
                    {"role": "user", "content": self.system_prompt},
                    {"role": "assistant", "content": "{"}
                ],
            )
            response_text = "{"+response.content[0].text
            response_dict = json.loads(response_text)
            approved = response_dict.get("approved", False)
            print(f"Critic evaluation: {'APPROVED' if approved else 'REJECTED'} - Feedback to analyst agent: {len(response_dict.get('feedback_string_to_evidence_analyst_agent', ''))} chars")

        except Exception as e:
            print(f"Error in critic evaluation: {e}")
            return {"status": "failed", "error": str(e)}
        
        return response_dict
