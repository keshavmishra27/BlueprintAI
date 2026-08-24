import re

def detect_credential_leaks(text: str) -> bool:
    """
    Scans the provided text for likely accidentally leaked credentials.
    Returns True if a leak is suspected, False otherwise.
    Never logs or returns the actual suspected value.
    """
    if not text:
        return False
        
    # Basic heuristic patterns for common secrets.
    # We do not want to be overly aggressive and block valid JSON, 
    # but we want to catch raw tokens if the LLM pastes them in 'description' or 'explanation'.
    
    patterns = [
        r'ghp_[a-zA-Z0-9]{36}',                # GitHub Personal Access Token
        r'AKIA[0-9A-Z]{16}',                   # AWS Access Key ID
        r'xox[baprs]-[0-9a-zA-Z]{10,48}',      # Slack Token
        r'eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+' # JWT (often contains secrets)
    ]
    
    for pattern in patterns:
        if re.search(pattern, text):
            return True
            
    # We can also check for explicit assignments in text like api_key="sk-..."
    # A generic high-entropy checker or specific service prefix checker works best.
    if re.search(r'sk-[a-zA-Z0-9]{48}', text): # OpenAI Key pattern
        return True
        
    return False

def sanitize_payload(payload_dict: dict) -> bool:
    """
    Recursively scans all string values in a dictionary (from a Payload dump)
    to check for credential leaks.
    Returns True if a leak is found, False if clean.
    """
    for key, value in payload_dict.items():
        if isinstance(value, str):
            if detect_credential_leaks(value):
                return True
        elif isinstance(value, dict):
            if sanitize_payload(value):
                return True
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    if detect_credential_leaks(item):
                        return True
                elif isinstance(item, dict):
                    if sanitize_payload(item):
                        return True
    return False
