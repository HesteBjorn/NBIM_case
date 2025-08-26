import pandas as pd

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
        self.system_prompt = self._get_system_prompt(self.return_format)

    def _get_system_prompt(self, return_format: str):
        try:
            with open("src/manager_prompt.txt", "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except (OSError, IOError) as e:
            system_prompt = ""
        system_prompt += f"\n\nThe return format of your output should be JSON like this: {return_format}"
        return system_prompt

    def run(self):
        pass
        # Explore calculations
