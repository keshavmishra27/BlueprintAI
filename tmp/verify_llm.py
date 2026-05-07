import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the project root to sys.path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.services.llm_factory import check_llm_availability

class TestLLMAvailability(unittest.TestCase):

    @patch("os.getenv")
    def test_openrouter_key_bypasses_ollama(self, mock_getenv):
        # Setup: OPENROUTER_API_KEY is set, GOOGLE_API_KEY is not
        def side_effect(key, default=None):
            if key == "OPENROUTER_API_KEY":
                return "sk-or-v1-testkey"
            if key == "GOOGLE_API_KEY":
                return None
            return default
        
        mock_getenv.side_effect = side_effect
        
        # This should not raise any exception even if requests.get (Ollama) would fail
        try:
            check_llm_availability()
            passed = True
        except Exception as e:
            passed = False
            print(f"Failed with error: {e}")
        
        self.assertTrue(passed, "Check should have passed with OpenRouter key")

    @patch("os.getenv")
    def test_google_key_bypasses_ollama(self, mock_getenv):
        # Setup: GOOGLE_API_KEY is set
        def side_effect(key, default=None):
            if key == "GOOGLE_API_KEY":
                return "test-google-key"
            if key == "OPENROUTER_API_KEY":
                return None
            return default
            
        mock_getenv.side_effect = side_effect
        
        try:
            check_llm_availability()
            passed = True
        except Exception as e:
            passed = False
            print(f"Failed with error: {e}")
            
        self.assertTrue(passed, "Check should have passed with Google key")

    @patch("os.getenv")
    @patch("requests.get")
    def test_no_keys_fails_if_ollama_down(self, mock_get, mock_getenv):
        # Setup: No cloud keys
        mock_getenv.return_value = None
        
        # Mock requests.get to simulate Ollama down
        mock_get.side_effect = Exception("Connection refused")
        
        with self.assertRaises(Exception) as cm:
             check_llm_availability()
        
        self.assertIn("Ollama is not running", str(cm.exception.detail))

if __name__ == "__main__":
    unittest.main()
