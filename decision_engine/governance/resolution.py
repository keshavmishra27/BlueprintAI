from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Any
from decision_engine.input_layer.schemas import ArchitectureNode, Requirement
from decision_engine.input_layer.ontology import evaluate_ontology, get_known_dependencies, OntologyResult

class ResolutionRequest(BaseModel):
    id: str
    dependency: str
    original_provenance: dict
    requested_operational_property: dict
    required_constraints: List[str]
    evidence: List[str]
    resolver_identity: str
    curator_approved: bool
    confidence: float = 1.0  # Used as adversarial metadata, explicitly ignored in arbitration
    status: Literal["PENDING", "APPROVED", "REJECTED", "REVOKED"] = "PENDING"

class ConflictResolution(BaseModel):
    conflict_id: str
    conflicting_policy_ids: List[str]
    resolver_identity: str
    resolution_reason: str
    selected_policy_id: Optional[str]
    rejected_policy_ids: List[str]
    curator_authorized: bool

def process_resolution(req: ResolutionRequest) -> ResolutionRequest:
    if req.resolver_identity == req.original_provenance.get("origin"):
        req.status = "REJECTED"
        return req
    if not req.evidence or len(req.evidence) == 0:
        req.status = "REJECTED"
        return req
    if not req.required_constraints or len(req.required_constraints) == 0:
        req.status = "REJECTED"
        return req
    if req.curator_approved:
        req.status = "APPROVED"
        return req
    req.status = "REJECTED"
    return req

class PromotedPolicyRegistry:
    def __init__(self):
        self._policy_sets: Dict[str, List[ResolutionRequest]] = {}
        self._arbitrated: Dict[str, dict] = {}
        self._conflicts: Dict[str, dict] = {}
        
    def add_policy(self, req: ResolutionRequest):
        if req.status != "APPROVED":
            raise ValueError(f"Registry Integrity Violation: Only APPROVED policies can be promoted.")
        
        if req.dependency not in self._policy_sets:
            self._policy_sets[req.dependency] = []
            
        # Add or replace by ID
        existing = [p for p in self._policy_sets[req.dependency] if p.id == req.id]
        if existing:
            self._policy_sets[req.dependency].remove(existing[0])
            
        self._policy_sets[req.dependency].append(req)
        self._arbitrate(req.dependency)
        
    def resolve_conflict(self, resolution: ConflictResolution):
        if not resolution.curator_authorized:
            raise ValueError("ConflictResolution must be curator authorized")
            
        # Find the dependency this applies to
        target_dep = None
        for dep, conflict_info in self._conflicts.items():
            if conflict_info["conflict_id"] == resolution.conflict_id:
                target_dep = dep
                break
                
        if not target_dep:
            return
            
        # Remove rejected policies from the pool
        filtered_policies = [
            p for p in self._policy_sets[target_dep] 
            if p.id not in resolution.rejected_policy_ids
        ]
        self._policy_sets[target_dep] = filtered_policies
        self._arbitrate(target_dep)
            
    def _arbitrate(self, dependency: str):
        proposals = self._policy_sets[dependency]
        # Sort by deterministic property (id) to guarantee order independence
        # Explicitly ignoring 'confidence'
        proposals = sorted(proposals, key=lambda x: x.id)
        
        merged_props = {}
        merged_constraints = set()
        
        for p in proposals:
            # Check for contradiction in properties
            for k, v in p.requested_operational_property.items():
                if k in merged_props and merged_props[k] != v:
                    # CONTRADICTION
                    self._conflicts[dependency] = {
                        "conflict_id": f"conflict_{dependency}",
                        "reason": "POLICY_CONFLICT",
                        "conflicting_sources": [req.resolver_identity for req in proposals],
                        "conflicting_policy_ids": [req.id for req in proposals],
                        "conflicting_properties": {k: [merged_props[k], v]}
                    }
                    if dependency in self._arbitrated:
                        del self._arbitrated[dependency]
                    return
            
            merged_props.update(p.requested_operational_property)
            for c in p.required_constraints:
                merged_constraints.add(c)
                
        # If we reach here, it's composable or identical
        if dependency in self._conflicts:
            del self._conflicts[dependency]
            
        self._arbitrated[dependency] = {
            "properties": merged_props,
            "constraints": list(merged_constraints)
        }
            
    def revoke_policy(self, dependency: str):
        # We simulate revocation by setting status to REVOKED for all policies under this dep and re-arbitrating
        if dependency in self._policy_sets:
            for p in self._policy_sets[dependency]:
                p.status = "REVOKED"
            self._arbitrate(dependency)
            
    def get_promoted_dependencies(self) -> List[str]:
        return list(self._arbitrated.keys())
        
    def get_conflicted_dependencies(self) -> List[str]:
        return list(self._conflicts.keys())
        
    def get_conflict_info(self, dependency: str) -> dict:
        return self._conflicts.get(dependency, {})
        
    def evaluate(self, arch: ArchitectureNode, env_constraints: List[str]) -> List[str]:
        failures = []
        for dep in arch.semantic_dependencies:
            if dep in self._arbitrated:
                # First check if any policy is revoked
                is_revoked = any(p.status == "REVOKED" for p in self._policy_sets[dep])
                if is_revoked:
                    failures.append(f"{dep}_authorization_revoked")
                else:
                    for req_constraint in self._arbitrated[dep]["constraints"]:
                        if req_constraint not in env_constraints:
                            failures.append(f"{req_constraint}_missing")
        return failures

def evaluate_ontology_with_registry(arch: ArchitectureNode, env_constraints: List[str], env_requirements: List[Requirement], registry: PromotedPolicyRegistry) -> OntologyResult:
    base_result = evaluate_ontology(arch, env_constraints, env_requirements)
    registry_failures = registry.evaluate(arch, env_constraints)
    return OntologyResult(
        requirement_failures=base_result.requirement_failures,
        constraint_failures=base_result.constraint_failures + registry_failures
    )

def get_all_known_dependencies(registry: PromotedPolicyRegistry) -> List[str]:
    base_known = list(get_known_dependencies())
    promoted = registry.get_promoted_dependencies()
    return base_known + promoted
