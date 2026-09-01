from pathlib import Path
from typing import Optional, List
from product.service import ProductService
from product.workspace.binding import read_binding
from product.api.v1.models import Decision, GapReport

class AgentTools:
    """
    Thin wrappers around the Product API for use by the agent.
    These tools enforce workspace identity validation BEFORE allowing the agent to evaluate or modify contracts.
    """
    def __init__(self, workspace_dir: Path, service: ProductService):
        self.workspace_dir = workspace_dir
        self.service = service
        
    def _validate_binding_and_get_decision_id(self, requested_decision_id: Optional[str] = None) -> str:
        """
        Validates the local workspace identity against the canonical Product API.
        """
        binding = read_binding(self.workspace_dir)
        if not binding:
            raise ValueError("Workspace is not bound to any decision. Missing .blueprint/contract.json")
            
        if requested_decision_id and binding.decision_id != requested_decision_id:
            raise ValueError(f"REJECTED: Workspace is bound to Decision {binding.decision_id}, but Agent attempted to use Decision {requested_decision_id}")
            
        canonical_decision = self.service.get_decision(binding.decision_id)
        if not canonical_decision:
            raise ValueError(f"REJECTED: Bound decision {binding.decision_id} not found in Canonical Product API.")
            
        if canonical_decision.decision_fingerprint != binding.decision_fingerprint:
            raise ValueError("REJECTED: Workspace binding decision_fingerprint does not match the canonical Decision.")
            
        if canonical_decision.requirement_set_fingerprint != binding.requirement_set_fingerprint:
            raise ValueError("REJECTED: Workspace binding requirement_set_fingerprint does not match the canonical Decision.")
            
        return binding.decision_id
        
    def get_active_contract(self, decision_id: Optional[str] = None) -> Decision:
        valid_decision_id = self._validate_binding_and_get_decision_id(decision_id)
        return self.service.get_decision(valid_decision_id)
        
    def get_contract(self, decision_id: Optional[str] = None) -> Decision:
        return self.get_active_contract(decision_id)
        
    def get_lineage(self, decision_id: Optional[str] = None) -> List[Decision]:
        valid_decision_id = self._validate_binding_and_get_decision_id(decision_id)
        lineage = self.service.get_decision_history(valid_decision_id)
        return lineage if lineage else []
        
    def verify_repository(self, decision_id: Optional[str] = None) -> GapReport:
        valid_decision_id = self._validate_binding_and_get_decision_id(decision_id)
        report = self.service.analyze_repository(valid_decision_id, str(self.workspace_dir))
        if not report:
            raise RuntimeError(f"Could not analyze repository for decision {valid_decision_id}")
        return report
        
    def propose_refinement(self, gap_report_id: Optional[str], applied_exploration: str, preserved: List[str], problem_detected: str, decision_id: Optional[str] = None) -> Decision:
        valid_decision_id = self._validate_binding_and_get_decision_id(decision_id)
        decision = self.service.apply_refinement(
            decision_id=valid_decision_id,
            gap_report_id=gap_report_id,
            applied_exploration=applied_exploration,
            preserved=preserved,
            problem_detected=problem_detected
        )
        if not decision:
            raise ValueError(f"Failed to propose refinement for decision {valid_decision_id}")
        return decision
