from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import hashlib
import json

from product.db.repository import ProductRepository
from product.db.models import DecisionRecord, GapReportRecord, RefinementRecord
from product.api.v1.models import (
    Decision, Architecture, Component, Governance, Alternative, 
    GapReport, RefinementOption
)

# We import the internal engines
from idea_refiner.orchestrator import Orchestrator
from repo_checker.extractor import RepoExtractor
from repo_checker.gap_engine import GapEngine

class ProductService:
    def __init__(self, db: Session = None):
        self.db = db
        self.repository = ProductRepository(db) if db else None

    def _hash_dict(self, data: Dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def _map_to_product_decision(self, record: DecisionRecord) -> Decision:
        return Decision(
            id=record.id,
            version=1,
            architecture=Architecture(**record.architecture_json),
            governance=Governance(**record.governance_json),
            alternatives=[Alternative(**alt) for alt in (record.alternatives_json or [])],
            alignment=None,
            decision_fingerprint=record.decision_fingerprint,
            graph_fingerprint=record.graph_fingerprint,
            context_fingerprint=record.context_fingerprint,
            requirement_set_fingerprint=record.requirement_set_fingerprint,
            status=record.status,
            created_at=record.created_at
        )

    def _canonicalize_and_hash(self, arch_json: Dict, gov_json: Dict, alt_json: List) -> str:
        # Canonicalize architecture
        arch = dict(arch_json)
        if "components" in arch:
            arch["components"] = sorted(arch["components"], key=lambda x: x.get("name", ""))
        if "decisions" in arch:
            arch["decisions"] = sorted(arch["decisions"], key=lambda x: x.get("key", ""))
        
        # We hash the canonicalized contract fields
        payload = {
            "architecture": arch,
            "governance": gov_json,
            "alternatives": alt_json
        }
        return self._hash_dict(payload)

    def _map_to_engine_artifact(self, decision_record: DecisionRecord):
        """
        Intentional structural projection of the complete Decision contract.
        This maps only the structural requirements (components) into the format expected by the GapEngine,
        intentionally dropping governance and alternatives which are not evaluated structurally.
        """
        from decision_engine.api.artifact import ArchitectureDecisionArtifact
        
        raw_components = decision_record.architecture_json.get("components", [])
        component_names = [c.get("name", "") if isinstance(c, dict) else str(c) for c in raw_components]
        
        # We classify some as databases just as a rough heuristic for the projection
        databases = [c.get("name") for c in raw_components if isinstance(c, dict) and c.get("type", "").lower() in ["database", "db"]]
        
        return ArchitectureDecisionArtifact.model_construct(
            idea=decision_record.idea_text,
            winning_path_id=decision_record.id,
            components=component_names,
            technologies=[],
            databases=databases,
            interfaces=[],
            data_flows=[],
            decisions={},
            constraints=[],
            dependencies=[],
            pareto_frontier=[],
            governance={},
            fingerprints={"canonical": decision_record.decision_fingerprint},
            explanation="Structural projection from DecisionRecord"
        )

    def _compute_requirement_fingerprint(self, decision_record: DecisionRecord) -> str:
        canonical_projection = self._map_to_engine_artifact(decision_record)
        expected_comps = set(canonical_projection.databases)
        for c in canonical_projection.components:
            expected_comps.add(c)
        import hashlib
        req_str = ",".join(sorted(list(expected_comps)))
        return hashlib.md5(req_str.encode()).hexdigest()

    def analyze_idea(self, idea: str, context: Optional[Dict[str, Any]] = None, parser=None) -> Decision:
        if context is None:
            context = {}
            
        from decision_engine.tree.context import DecisionContext
        if isinstance(context, dict):
            # Try to build a DecisionContext from the dict
            context = DecisionContext(
                ontology_version="1.0.0",
                registry_policy_hashes=[],
                environment_constraints=[],
                architecture=context.get("architecture", {}),
                business_context=context.get("business_context", {}),
                optimizer_preferences=context.get("optimizer_preferences", {})
            )
            
        if parser is None:
            from idea_refiner.parsers.deterministic import DeterministicIdeaParser
            parser = DeterministicIdeaParser()
            
        orchestrator = Orchestrator(parser)
        decision_artifact = orchestrator.refine(idea, context)
        
        raw_components = getattr(decision_artifact, 'components', [])
        mapped_components = [{"name": str(c), "type": "Service"} for c in raw_components] if raw_components else [{"name": "Default Component", "type": "Service"}]
        
        raw_decisions = getattr(decision_artifact, 'decisions', {})
        mapped_decisions = [{"key": k, "value": v} for k, v in raw_decisions.items()]
        
        arch_json = {
            "components": mapped_components,
            "decisions": mapped_decisions
        }
        
        raw_gov = getattr(decision_artifact, 'governance', {})
        gov_json = {
            "action": raw_gov.get("action", "RECOMMEND"), 
            "severity": raw_gov.get("severity", "INFO"), 
            "scores": raw_gov.get("scores", {})
        }
        
        alt_json = []
        
        decision_fingerprint = self._canonicalize_and_hash(arch_json, gov_json, alt_json)
        graph_fingerprint = self._hash_dict({"arch": arch_json})
        context_fingerprint = self._hash_dict(context.model_dump() if hasattr(context, "model_dump") else context)

        record = DecisionRecord(
            idea_text=idea,
            architecture_json=arch_json,
            governance_json=gov_json,
            alternatives_json=alt_json,
            decision_fingerprint=decision_fingerprint,
            graph_fingerprint=graph_fingerprint,
            context_fingerprint=context_fingerprint,
            status="ACTIVE",
            requirement_set_fingerprint="" # Temporary until computed
        )
        
        record.requirement_set_fingerprint = self._compute_requirement_fingerprint(record)
        
        self.repository.save_decision(record)
        return self._map_to_product_decision(record)

    def analyze_repository(self, decision_id: str, repo_path: str, _injected_artifact=None) -> Optional[GapReport]:
        decision_record = self.repository.get_decision(decision_id)
        if not decision_record:
            return None
            
        if decision_record.status != "ACTIVE":
            raise ValueError(f"Cannot evaluate a non-ACTIVE decision. Decision {decision_id} is {decision_record.status}.")
            
        extractor = RepoExtractor(repo_path)
        repo_artifact = extractor.extract_deterministic()
        
        # Structural projection
        decision_artifact = _injected_artifact if _injected_artifact else self._map_to_engine_artifact(decision_record)
        
        # Calculate expected structural fingerprint directly from the canonical projection
        fresh_requirement_fingerprint = self._compute_requirement_fingerprint(decision_record)
        
        if fresh_requirement_fingerprint != decision_record.requirement_set_fingerprint:
            raise ValueError(
                f"Provenance violation: Stored requirement fingerprint ({decision_record.requirement_set_fingerprint}) "
                f"does not match freshly derived projection fingerprint ({fresh_requirement_fingerprint})."
            )
        
        engine = GapEngine()
        gap_report_artifact = engine.evaluate(decision_artifact, repo_artifact)
        
        if gap_report_artifact.requirement_set_fingerprint != fresh_requirement_fingerprint:
            raise ValueError(
                f"Provenance violation: Engine evaluated structural requirements ({gap_report_artifact.requirement_set_fingerprint}) "
                f"that do not match the canonical projection for Decision {decision_id} ({fresh_requirement_fingerprint})."
            )
        
        repo_fingerprint = self._hash_dict(getattr(repo_artifact, 'components', repo_artifact.__dict__))
        
        def serialize_evidence(evidence_list):
            import uuid
            result = []
            for ev in evidence_list:
                ev_dict = ev.model_dump() if hasattr(ev, 'model_dump') else (ev.dict() if hasattr(ev, 'dict') else ev)
                ev_dict['id'] = str(uuid.uuid4())
                ev_dict['description'] = f"Found {ev_dict.get('observed_entity', '')} at {ev_dict.get('location', '')}"
                ev_dict['source_type'] = "workspace_inspection"
                ev_dict['file_path'] = ev_dict.get('source_file')
                result.append(ev_dict)
            return result
            
        def serialize_findings(findings_list):
            import uuid
            result = []
            for f in findings_list:
                f_dict = f.model_dump() if hasattr(f, 'model_dump') else (f.dict() if hasattr(f, 'dict') else f)
                category = f_dict.get('category', 'UNKNOWN')
                
                evidence_list = serialize_evidence(f_dict.get('evidence', []))
                evidence_ids = [e['id'] for e in evidence_list]
                
                finding_id = str(uuid.uuid4())
                title = f"{category.capitalize()} Component: {f_dict.get('expected', '')}"
                severity = "Medium" if category in ["MISSING", "MISMATCH"] else "Info"
                
                mapped_finding = {
                    "id": finding_id,
                    "title": title,
                    "severity": severity,
                    "classification": "Verified Finding",
                    "category": category,
                    "explanation": f"Expected: {f_dict.get('expected', '')}. Observed: {f_dict.get('observed', 'None')}",
                    "impact": "Architectural deviation from established decision.",
                    "recommendation": "Review implementation against original architecture decision.",
                    "evidence_ids": evidence_ids,
                    "_original_evidence": evidence_list
                }
                result.append(mapped_finding)
            return result
            
        mapped_findings = serialize_findings(getattr(gap_report_artifact, 'findings', []))
        all_evidence = []
        for mf in mapped_findings:
            all_evidence.extend(mf.pop('_original_evidence', []))
            
        raw_components = getattr(repo_artifact, 'components', [])
        components_list = []
        for c in raw_components:
            if isinstance(c, str):
                components_list.append({"name": c, "type": "discovered"})
            else:
                components_list.append(c.model_dump() if hasattr(c, 'model_dump') else (c.dict() if hasattr(c, 'dict') else c))
                
        actual_arch = {"components": components_list}
            
        record = GapReportRecord(
            decision_id=decision_id,
            decision_fingerprint=decision_record.decision_fingerprint,
            requirement_set_fingerprint=gap_report_artifact.requirement_set_fingerprint,
            repository_fingerprint=repo_fingerprint,
            expected_architecture_json=decision_record.architecture_json,
            actual_architecture_json=actual_arch,
            findings_json=mapped_findings,
            evidence_json=all_evidence,
            alignment_score=getattr(gap_report_artifact, 'alignment_score', 0.0)
        )
        
        self.repository.save_gap_report(record)
        
        return GapReport(
            id=record.id,
            decision_id=record.decision_id,
            decision_fingerprint=record.decision_fingerprint,
            requirement_set_fingerprint=record.requirement_set_fingerprint,
            repository_fingerprint=record.repository_fingerprint,
            expected_architecture=Architecture(**record.expected_architecture_json),
            actual_architecture=record.actual_architecture_json,
            findings=record.findings_json,
            evidence=record.evidence_json,
            alignment_score=record.alignment_score,
            created_at=record.created_at
        )

    def create_refinement_options(self, decision_id: str, gap_report_id: Optional[str], new_constraint: Optional[str]) -> List[RefinementOption]:
        return [
            RefinementOption(
                problem_detected="Mismatch in actual architecture" if gap_report_id else "New constraint applied",
                preserved=["FastAPI", "Docker"],
                exploration="Enforce target architecture"
            ),
            RefinementOption(
                problem_detected="Mismatch in actual architecture" if gap_report_id else "New constraint applied",
                preserved=["FastAPI", "Docker"],
                exploration="Adopt actual architecture components"
            )
        ]

    def apply_refinement(self, decision_id: str, gap_report_id: Optional[str], applied_exploration: str, preserved: List[str], problem_detected: str) -> Optional[Decision]:
        source_record = self.repository.get_decision(decision_id)
        if not source_record:
            return None
            
        arch_json = source_record.architecture_json.copy()
        arch_json["decisions"].append({"refinement": applied_exploration})
        
        decision_fingerprint = self._canonicalize_and_hash(arch_json, source_record.governance_json, source_record.alternatives_json)
        
        new_record = DecisionRecord(
            idea_text=source_record.idea_text,
            parent_id=source_record.id,
            architecture_json=arch_json,
            governance_json=source_record.governance_json,
            alternatives_json=source_record.alternatives_json,
            decision_fingerprint=decision_fingerprint,
            graph_fingerprint=self._hash_dict({"arch": arch_json}),
            context_fingerprint=source_record.context_fingerprint,
            status="ACTIVE",
            requirement_set_fingerprint=""
        )
        new_record.requirement_set_fingerprint = self._compute_requirement_fingerprint(new_record)
        
        self.repository.save_decision(new_record)
        
        refinement_record = RefinementRecord(
            source_decision_id=source_record.id,
            target_decision_id=new_record.id,
            gap_report_id=gap_report_id,
            problem_detected=problem_detected,
            preserved_json=preserved,
            applied_exploration=applied_exploration
        )
        self.repository.save_refinement(refinement_record)
        
        return self._map_to_product_decision(new_record)

    def get_decision(self, decision_id: str) -> Optional[Decision]:
        record = self.repository.get_decision(decision_id)
        if not record:
            return None
        return self._map_to_product_decision(record)

    def get_decision_history(self, decision_id: str) -> Optional[List[Decision]]:
        records = self.repository.get_decision_history(decision_id)
        if not records:
            return None
        return [self._map_to_product_decision(r) for r in records]

    def get_recent_decisions(self, limit: int = 10) -> List[Decision]:
        records = self.repository.get_recent_decisions(limit)
        return [self._map_to_product_decision(r) for r in records]

    def update_decision_status(self, decision_id: str, status: str) -> Optional[Decision]:
        record = self.repository.update_decision_status(decision_id, status)
        if not record:
            return None
        return self._map_to_product_decision(record)

    def get_decision_children(self, decision_id: str) -> List[Decision]:
        records = self.repository.get_decision_children(decision_id)
        return [self._map_to_product_decision(r) for r in records]

    def get_decisions_by_root(self, root_decision_id: str, status: Optional[str] = None) -> List[Decision]:
        records = self.repository.get_decisions_by_root(root_decision_id, status)
        return [self._map_to_product_decision(r) for r in records]
