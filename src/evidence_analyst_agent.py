import pandas as pd
import anthropic
import os
import json

class EvidenceAnalystAgent:
    def __init__(self, event: dict, previous_response: dict = {}, critic_feedback: str = ""):
        self.event = event
        self.critic_feedback = critic_feedback
        self.return_format = """
        {
            "evidence": ["string"],
            "hypothesis": "string"
        }
        """
        self.system_prompt = self._get_system_prompt(self.event, previous_response, self.critic_feedback, return_format=self.return_format)

    def _get_system_prompt(self, event: dict, previous_response: dict, critic_feedback: str, return_format: str):
        feedback_section = ""
        if critic_feedback:
            feedback_section = f"""
        You have been evaluated by a critic agent. Your previous response was:
        {previous_response}

        The critic's feedback to address is:
        {critic_feedback}

        Please revise your analysis to address the critic's feedback above."""

        prompt = f"""
        You are a reconciliation analyst for dividend events, in the evidence-gathering phase. Your task is to thoroughly analyze a coac event and identify all potential discrepancies between NBIM and Custody data sources.

        Focus on:
        1. EVIDENCE: List all specific field mismatches you observe (be very specific about field names and values)
        2. HYPOTHESIS: Provide a detailed, comprehensive discussion of what might be wrong and what could have happened. Consider multiple scenarios, root causes, and systemic vs isolated issues.

        Do not make final conclusions about whether this is a break - focus on thorough analysis and evidence gathering.

        Evidence should be simple, factual observations. Each point should identify a specific mismatch.
        Hypothesis should be a detailed analytical discussion exploring possible explanations, implications, and scenarios. Make sure to structure this clearly.

        Output strictly valid JSON matching the provided schema. Do not restate inputs.
        
        {feedback_section}

        The return format of your output should be JSON matching this pattern:
        {return_format}

        The coac event you are analyzing is:
        {event}
        """
        return prompt

    def run(self)->dict:
        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                messages=[
                    {"role": "user", "content": self.system_prompt},
                    {"role": "assistant", "content": "{"}
                ],
            )
            response_text = "{"+response.content[0].text
            response_dict = json.loads(response_text)
            feedback_note = " (revision)" if self.critic_feedback else ""
            print(f"Evidence analysis for event {self.event['coac_event_key']}{feedback_note}: {len(response_dict.get('evidence', []))} evidence points gathered")

        except Exception as e:
            print(f"Error analyzing evidence for event {self.event['coac_event_key']}: {e}")
            return {"status": "failed", "error": str(e)}
        
        return response_dict
