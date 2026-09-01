import json
import sys

def ask_controller(filepath, question):
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    hidden_facts = data.get('hidden_facts_to_reveal', {})
    
    for fact_key, answer in hidden_facts.items():
        if fact_key.lower() in question.lower() or any(word in question.lower() for word in fact_key.lower().split() if len(word) > 4):
            print(f"CONTROLLER POLICY ANSWER: {answer}")
            return
            
    print("CONTROLLER POLICY ANSWER: I don't have a specific policy on that. Proceed with your best judgment.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ask_controller.py <path_to_json> <question_text>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    question = " ".join(sys.argv[2:])
    ask_controller(filepath, question)
