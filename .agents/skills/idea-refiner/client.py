import os
import requests
from typing import Dict, Any, Optional

class IdeaRefinerClient:
    """
    Client for interacting with the BlueprintAI API to drive the conversational Journey.
    """
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or os.environ.get("PRODUCT_API_URL", "http://localhost:8000/api/v1")
        self.api_key = api_key or os.environ.get("BLUEPRINT_API_KEY", "")
        
    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers
        
    def start_journey(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Starts an interactive architecture journey.
        """
        response = requests.post(
            f"{self.base_url}/journey/start",
            json=payload,
            headers=self._headers(),
            timeout=120
        )
        response.raise_for_status()
        return response.json()

    def answer_question(self, session_id: str, selected_option: str, new_arch: Optional[Dict] = None, new_unc: Optional[list] = None) -> Dict[str, Any]:
        """
        Answers a journey question.
        """
        payload = {
            "session_id": session_id,
            "selected_option": selected_option,
            "new_player_b_architecture": new_arch,
            "new_uncertainties": new_unc
        }
        
        response = requests.post(
            f"{self.base_url}/journey/answer",
            json=payload,
            headers=self._headers(),
            timeout=120
        )
        response.raise_for_status()
        return response.json()

    def get_journey(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieves a journey state.
        """
        response = requests.get(
            f"{self.base_url}/journey/{session_id}",
            headers=self._headers(),
            timeout=30
        )
        response.raise_for_status()
        return response.json()
        
    def refine_idea(self, idea: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Semantically aliases analyze_idea for agent-facing convenience.
        """
        payload = {
            "idea": idea,
            "context": context or {}
        }
        
        response = requests.post(
            f"{self.base_url}/ideas/analyze",
            json=payload,
            headers=self._headers(),
            timeout=120
        )
        response.raise_for_status()
        return response.json()
