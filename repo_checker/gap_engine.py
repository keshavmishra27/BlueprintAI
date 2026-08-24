from typing import List, Dict, Set
from decision_engine.api.artifact import ArchitectureDecisionArtifact
from repo_checker.schemas import RepositoryArchitectureArtifact, GapReport, GapFinding, GapCategory, Evidence

class GapEngine:
    def evaluate(self, expected: ArchitectureDecisionArtifact, actual: RepositoryArchitectureArtifact) -> GapReport:
        findings = []
        
        expected_comps = set(expected.databases)
        for c in expected.components:
            expected_comps.add(c)
            
        actual_comps = set(actual.components)
        
        def norm(s): return s.lower().strip()
        
        # Sort keys to ensure deterministic matching
        exp_norm_map = {norm(c): c for c in sorted(list(expected_comps))}
        act_norm_map = {norm(c): c for c in sorted(list(actual_comps))}
        
        # Keep track of which actuals have been used as mismatches
        used_mismatches = set()
        
        for e_norm, e_raw in exp_norm_map.items():
            if e_norm in act_norm_map:
                evidences = [ev for ev in actual.evidence if norm(ev.observed_entity) == e_norm or e_norm in norm(ev.observed_entity)]
                findings.append(GapFinding(
                    category=GapCategory.MATCH,
                    expected=e_raw,
                    observed=act_norm_map[e_norm],
                    evidence=evidences
                ))
            else:
                is_db = e_raw in expected.databases
                is_framework = not is_db # Simplified for M6: if it's not a DB, assume it's a framework or other component
                
                mismatched_db = None
                
                if is_db:
                    for a_norm, a_raw in act_norm_map.items():
                        if a_raw in actual.databases and a_norm not in exp_norm_map and a_norm not in used_mismatches:
                            mismatched_db = a_raw
                            used_mismatches.add(a_norm)
                            break
                elif is_framework:
                    for a_norm, a_raw in act_norm_map.items():
                        if a_raw in actual.frameworks and a_norm not in exp_norm_map and a_norm not in used_mismatches:
                            mismatched_db = a_raw
                            used_mismatches.add(a_norm)
                            break
                            
                if mismatched_db:
                    evidences = [ev for ev in actual.evidence if norm(ev.observed_entity) == norm(mismatched_db) or norm(mismatched_db) in norm(ev.observed_entity)]
                    findings.append(GapFinding(
                        category=GapCategory.MISMATCH,
                        expected=e_raw,
                        observed=mismatched_db,
                        evidence=evidences
                    ))
                else:
                    if not actual.manifests_found:
                        findings.append(GapFinding(
                            category=GapCategory.UNKNOWN,
                            expected=e_raw,
                            observed="insufficient evidence (no manifests)",
                            evidence=[]
                        ))
                    else:
                        findings.append(GapFinding(
                            category=GapCategory.MISSING,
                            expected=e_raw,
                            observed="absent",
                            evidence=[]
                        ))
                        
        used_actuals = set()
        for f in findings:
            if f.observed and f.category in [GapCategory.MATCH, GapCategory.MISMATCH, GapCategory.CONFLICT]:
                used_actuals.add(norm(f.observed))
                
        for a_norm, a_raw in act_norm_map.items():
            if a_norm not in used_actuals:
                evidences = [ev for ev in actual.evidence if norm(ev.observed_entity) == a_norm or a_norm in norm(ev.observed_entity)]
                findings.append(GapFinding(
                    category=GapCategory.EXTRA,
                    expected="absent",
                    observed=a_raw,
                    evidence=evidences
                ))
                
        db_actuals = [a for a in actual_comps if a in actual.databases]
        if len(db_actuals) > 1 and len(expected.databases) == 1:
            e_db = expected.databases[0]
            for f in findings:
                if f.expected == e_db:
                    f.category = GapCategory.CONFLICT
                    f.observed = " + ".join(db_actuals)
                    f.evidence = [ev for ev in actual.evidence if ev.observed_entity in db_actuals]
                    
        matches = len([f for f in findings if f.category == GapCategory.MATCH])
        mismatches = len([f for f in findings if f.category == GapCategory.MISMATCH])
        unknowns = len([f for f in findings if f.category == GapCategory.UNKNOWN])
        conflicts = len([f for f in findings if f.category == GapCategory.CONFLICT])
        
        total_expected = len(expected_comps)
        known_reqs = total_expected - unknowns
        
        if known_reqs <= 0:
            score = 100.0 if total_expected == 0 else 0.0
        else:
            score_val = matches - mismatches - conflicts
            score = max(0.0, (score_val / known_reqs) * 100.0)
            
        import hashlib
        req_str = ",".join(sorted(list(expected_comps)))
        req_fingerprint = hashlib.md5(req_str.encode()).hexdigest()
        
        return GapReport(
            findings=findings,
            coverage_score=score,
            requirement_set_fingerprint=req_fingerprint
        )
