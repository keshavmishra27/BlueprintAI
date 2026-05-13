import sys
import os
import json
import re
def extract_json_from_text(text: str) -> dict:
    if not text:
        return {}
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    start = text.find("{")
    if start != -1:
        end = text.rfind("}")
        if end != -1 and end > start:
            json_str = text[start:end+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                open_braces = json_str.count("{")
                close_braces = json_str.count("}")
                if open_braces > close_braces:
                    fixed_json = json_str + ("}" * (open_braces - close_braces))
                    try:
                        return json.loads(fixed_json)
                    except:
                        pass
                for suffix in ["}", "]}", "}}", "}]}", "}]}}"]:
                    try:
                        return json.loads(json_str + suffix)
                    except:
                        continue
    return {}
def test_recovery():
    log_path = r"c:\Users\hp\Desktop\kfiles\group_maker\llm_raw_debug.log"
    if not os.path.exists(log_path):
        print("Log file not found.")
        return
    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()
    print("--- TESTING RECOVERY LOGIC ---")
    result = extract_json_from_text(content)
    if result and "scores" in result and isinstance(result["scores"], dict):
        potential_misplaced_keys = ["total_score", "mentor_notes", "strengths", "top_issues", "security_warnings", "reproducibility"]
        for key in potential_misplaced_keys:
            if key not in result and key in result["scores"]:
                print(f"RECOVERED: key '{key}'")
                result[key] = result["scores"].pop(key)
    if result:
        print("Success! Final Top-level Keys:", list(result.keys()))
        required_keys = {"total_score", "scores", "mentor_notes"}
        missing = required_keys - set(result.keys())
        if not missing:
            print("PASSED: All required keys present at top level.")
        else:
            print(f"FAILED: Still missing {missing}")
    else:
        print("FAILED: No JSON extracted.")
if __name__ == "__main__":
    test_recovery()