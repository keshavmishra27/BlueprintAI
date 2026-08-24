import os
import requests
import json
from typing import Dict, Any
from .base import BaseLLMProvider

class GroqProvider(BaseLLMProvider):
    def __init__(self, model: str = "openai/gpt-oss-120b", api_key: str = None):
        self.model = model
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY must be provided")

    def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        system_prompt = f"You are a strict JSON outputting agent. Output valid JSON matching this schema: {json.dumps(schema)}"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(url, headers=headers, json=payload)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"Groq API Error: {response.status_code} - {response.text}")
            raise e
        
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)
