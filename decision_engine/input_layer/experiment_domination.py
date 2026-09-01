import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from decision_engine.input_layer.schemas import ArchitectureNode, Requirement
from decision_engine.input_layer.evaluator import evaluate_battle

def print_battle(name: str, constraints: list, requirements: list, user_arch: ArchitectureNode, player_b_arch: ArchitectureNode):
    print(f"\n{'='*50}")
    print(f" {name.upper()} ")
    print(f"{'='*50}")
    print("\nENVIRONMENT:")
    print(f"  Constraints: {constraints}")
    print(f"  Requirements: {[r.name for r in requirements]}")
    
    result = evaluate_battle(user_arch, player_b_arch, constraints, requirements)
    
    print(f"\nRESULTS:")
    print(f"  User Feasible: {result.a_feasible}")
    if result.a_constraint_violations:
        for v in result.a_constraint_violations:
            print(f"    - Violation: {v}")
            
    print(f"  Player B Feasible: {result.b_feasible}")
    if result.b_constraint_violations:
        for v in result.b_constraint_violations:
            print(f"    - Violation: {v}")
            
    print(f"\nREQUIREMENT EVALUATIONS:")
    for ev in result.requirement_evaluations:
        print(f"  [{ev.requirement}]")
        print(f"    User: {ev.user_satisfies} ({ev.user_reason})")
        print(f"    Player B: {ev.player_b_satisfies} ({ev.player_b_reason})")
        
    print(f"\nWINNER: {result.winner.value.upper()}")
    print(f"REASONING: {result.reasoning}\n")

def main():
    print("Initializing Domination Experiment...")

    user_arch = ArchitectureNode(
        inputs=["Patient appointment requests"],
        processing=["Maintain queue"],
        decision=["Simple rules for appointment time"],
        output=["Appointment schedule"],
        data_required=["Patient requests"],
        resources_required=["Local queue service", "Simple rules engine"],
        constraints=["Basic prediction limits"],
        capabilities=["queue management", "appointment prediction"]
    )

    player_b_arch = ArchitectureNode(
        inputs=["Patient demand", "Hospital resource state"],
        processing=["Demand prediction", "Bottleneck prediction"],
        decision=["Proactive resource allocation"],
        output=["Dynamic patient routing"],
        data_required=["Historical patient arrival data", "Hospital resource data"],
        resources_required=["ML model", "Hospital database", "Prediction service"],
        constraints=["Requires reliable operational data"],
        capabilities=["demand prediction", "bottleneck prediction", "proactive routing"]
    )
    
    req_wait = Requirement(name="Reduce waiting time", required=True)
    req_bottleneck = Requirement(name="Handle resource bottlenecks", required=True)

    print_battle(
        name="Battle 1: B Clearly Wins",
        constraints=["Historical data available"],
        requirements=[req_wait, req_bottleneck],
        user_arch=user_arch,
        player_b_arch=player_b_arch
    )
    
    print_battle(
        name="Battle 2: B Clearly Loses",
        constraints=["No historical data", "No external APIs", "Must run on a basic laptop"],
        requirements=[req_wait, req_bottleneck],
        user_arch=user_arch,
        player_b_arch=player_b_arch
    )
    
    print_battle(
        name="Battle 3: Tie / Neither Dominates",
        constraints=["Historical data available", "Very small prototype", "Only 48 hours"],
        requirements=[req_wait],
        user_arch=user_arch,
        player_b_arch=player_b_arch
    )

if __name__ == "__main__":
    main()
