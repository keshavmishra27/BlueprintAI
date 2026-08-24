from typing import List, Dict
from .schemas import PlayerBResponse, CandidateApproach, DecisionEvidence, UserIdea

def generate_player_b_response(idea: UserIdea, retrieved_projects: List[Dict], retrieved_patterns: List[Dict]) -> PlayerBResponse:
    """
    Simulates Player B (the AI Architect) generating candidate approaches from KB evidence,
    and selecting/combining them into an alternative HOW.
    """
    print("--- PLAYER B: ANALYZING EVIDENCE AND GENERATING CANDIDATES ---")
    
    # In a real system, an LLM would construct this dynamically based on the retrieved_projects
    # Here we mock the precise output requested by the user's experiment constraints.
    
    candidate_1 = CandidateApproach(
        name="Predictive Bottleneck Detection",
        description="Forecast resource shortages before they impact the schedule.",
        evidence=[
            DecisionEvidence(
                decision="Predict resource bottlenecks before assigning patients.",
                source_project="sih_2022_hc_01",
                supporting_pattern="Proactive Routing",
                evidence="Project used predictive bed shortage information to route patients before bottlenecks occurred."
            )
        ]
    )
    
    candidate_2 = CandidateApproach(
        name="Proactive Resource Routing",
        description="Reroute resources and patients dynamically based on predictive data.",
        evidence=[
            DecisionEvidence(
                decision="Pre-emptively route requests to available resources.",
                source_project="sih_2020_dis_01",
                supporting_pattern="Proactive Routing",
                evidence="Pre-emptively routed rescue boats based on aggregated predictive map instead of reactive assignments."
            )
        ]
    )
    
    candidate_3 = CandidateApproach(
        name="Dynamic Queue Optimization",
        description="Adjust schedules dynamically ahead of congestion.",
        evidence=[
            DecisionEvidence(
                decision="Optimize the queue dynamically based on live conditions.",
                source_project="sih_2022_tr_01",
                supporting_pattern="Proactive Routing",
                evidence="Traffic lights scheduled dynamically ahead of congestion, preventing backlog buildup."
            )
        ]
    )
    
    candidates = [candidate_1, candidate_2, candidate_3]
    for i, c in enumerate(candidates, 1):
        print(f"Candidate {i}: {c.name}")
        for ev in c.evidence:
            print(f"  Evidence: SIH project {ev.source_project}")
            
    # Player B selects and combines
    selected_architecture = "Demand prediction + proactive resource routing + dynamic queue optimization."
    architectural_difference = "Where Player B gained an advantage: You predict individual appointment times using an LLM, but don't address the upstream resource bottlenecks. Player B addresses the root cause by forecasting resource shortages and routing proactively."
    
    advantages = [
        "Addresses upstream bottlenecks rather than merely predicting individual appointment times.",
        "Reduces reactive scheduling."
    ]
    
    tradeoffs = [
        "Requires historical operational hospital data.",
        "More complex data integration than a simple LLM wrapper."
    ]
    
    # Consolidate all evidence used in the final selection
    final_evidence = []
    for c in candidates:
        final_evidence.extend(c.evidence)
        
    return PlayerBResponse(
        user_approach=idea.how,
        candidate_approaches=candidates,
        selected_approach=selected_architecture,
        architectural_difference=architectural_difference,
        advantages=advantages,
        tradeoffs=tradeoffs,
        evidence=final_evidence,
        confidence="Medium - Approach relies on data availability which may vary per hospital."
    )
