import json, requests

payload = {
    'session_id': 'manual_opt_baseline2',
    'project_state': {
        'user_idea': {'what':'Dashboard', 'why':'Need to see data', 'how_raw':'Query DB', 'how_structured': {'inputs':[],'processing':[],'decision':[],'output':[],'capabilities':[],'data_required':[],'resources_required':[],'constraints':[]}},
        'current_constraints': ['budget <= $1000/month', 'reliable internet'],
        'current_requirements': [{'name': 'fast query', 'required': True}]
    },
    'initial_architecture': {
        'inputs': ['User queries'],
        'processing': ['Cloud DB Engine'],
        'decision': ['Query Execution'],
        'output': ['Web Dashboard'],
        'capabilities': ['fast query'],
        'data_required': [],
        'resources_required': [],
        'constraints': ['budget <= $1000/month', 'reliable internet'],
        'evidence_provenance': [],
        'historical_decisions': [],
        'architectural_decisions': {'db': 'Cloud DB Engine'}
    },
    'candidate_uncertainties': []
}

res = requests.post('http://127.0.0.1:8000/api/journey/start', json=payload).json()
print(json.dumps(res, indent=2))
