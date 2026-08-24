import hashlib
from decision_engine.api.artifact import ArchitectureDecisionArtifact
from repo_checker.schemas import GapReport, GapCategory
from idea_refiner.refinement import RefinementArtifact

class RefinementEngine:
    def translate_to_constraints(self, decision: ArchitectureDecisionArtifact, gap_report: GapReport) -> RefinementArtifact:
        preserved = []
        requested = []
        unresolved = []
        
        for f in gap_report.findings:
            if f.category == GapCategory.MATCH:
                preserved.append(f"Preserve {f.expected} because it is a MATCH in the repository.")
            elif f.category == GapCategory.MISSING:
                requested.append(f"Explore architectures containing {f.expected} because it is currently MISSING.")
            elif f.category == GapCategory.MISMATCH:
                requested.append(f"Explore alternatives between intended {f.expected} and observed {f.observed} because of a MISMATCH.")
            elif f.category == GapCategory.UNKNOWN:
                unresolved.append(f"Investigate requirement {f.expected} because it is currently UNKNOWN.")
            elif f.category == GapCategory.CONFLICT:
                requested.append(f"Resolve conflict: intended {f.expected} vs observed {f.observed}.")
                
        dec_str = str(decision.components)
        parent_decision_fingerprint = hashlib.md5(dec_str.encode()).hexdigest()
        
        return RefinementArtifact(
            parent_decision_fingerprint=parent_decision_fingerprint,
            parent_graph_fingerprint=decision.fingerprints.get("graph_id", "G0"),
            gap_report_fingerprint=str(gap_report.coverage_score),
            requirement_set_fingerprint=gap_report.requirement_set_fingerprint,
            preserved_decisions=preserved,
            requested_changes=requested,
            unresolved_questions=unresolved
        )
