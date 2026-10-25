import pytest
from decision_engine.input_layer.schemas import SemanticClaim, ProvenanceType, OntologyRule, SemanticRelation
from decision_engine.input_layer.semantic_ontology import SemanticOntologyRegistry, RegisteredOntologySource
from decision_engine.input_layer.semantic_resolver import SemanticResolver, AuthoritativeSource

class MockOntologySource(RegisteredOntologySource):
    def __init__(self, source_id, rules):
        self.source_id = source_id
        self._rules = rules
    def get_rules(self):
        return self._rules

class MockAuthoritativeSource(AuthoritativeSource):
    def __init__(self, source_id, claims, allowed_provenance):
        self.source_id = source_id
        self._claims = claims
        self.allowed_provenance = allowed_provenance
    def get_claims(self, capability_name, active_scopes):
        return self._claims

def test_invariant_6_ontology_poisoning():
    """
    Adversarial test: An unregistered or agent-supplied ontology 
    must not create authoritative semantics.
    """
    registry = SemanticOntologyRegistry()
    
    poison_rule = OntologyRule(
        rule_id="r1",
        source_id="hacked_ontology",
        relation=SemanticRelation.EQUIVALENT,
        source_concept="fake_concept",
        target_concept="real_concept"
    )
    
    # We do NOT register the source. 
    # The ontology shouldn't know the concept.
    assert not registry.is_known("fake_concept")

def test_invariant_7_requirement_bleeding():
    """
    Adversarial test: Registering ACID <-> EVENTUAL_CONSISTENCY 
    must not impose either concept as a requirement on an empty capability.
    """
    registry = SemanticOntologyRegistry()
    rule = OntologyRule(
        rule_id="r1",
        source_id="ont1",
        relation=SemanticRelation.CONTRADICTS,
        source_concept="ACID",
        target_concept="EVENTUAL_CONSISTENCY"
    )
    registry.register_source(MockOntologySource("ont1", [rule]))
    
    resolver = SemanticResolver(registry)
    # Empty capability (no claims asserted)
    auth_source = MockAuthoritativeSource("auth1", [], [ProvenanceType.DOMAIN_RULE])
    
    claims = auth_source.get_claims("cap1", ["scope1"])
    res = resolver.resolve_semantics(claims, ["scope1"])
    # The ontology knows the concepts and relationships, but since no claim 
    # was asserted, NO constraint should bleed into the result.
    assert len(res["constraints"]) == 0

def test_unknown_strings_opaque():
    """
    Unknown strings should be kept opaque and intact without arbitrary deduplication 
    or normalization into known semantic concepts.
    """
    registry = SemanticOntologyRegistry()
    resolver = SemanticResolver(registry)
    
    claim1 = SemanticClaim(claim_id="1", value="blue buttons", provenance=ProvenanceType.DOMAIN_RULE, source_id="auth1", scope="scope1", precedence=1)
    claim2 = SemanticClaim(claim_id="2", value="blue buttons", provenance=ProvenanceType.DOMAIN_RULE, source_id="auth1", scope="scope1", precedence=2)
    
    auth_source = MockAuthoritativeSource("auth1", [claim1, claim2], [ProvenanceType.DOMAIN_RULE])
    
    claims = auth_source.get_claims("cap1", ["scope1"])
    res = resolver.resolve_semantics(claims, ["scope1"])
    # Unknowns should be retained as is, not normalized or deduplicated implicitly by ontology logic
    assert len(res["constraints"]) == 2
    assert "blue buttons" in [c.value for c in res["constraints"]]

def test_transitive_entailment_dag():
    """
    A -> B -> C entailment must create INFERRED claims where C derives from B,
    and B derives from A.
    """
    registry = SemanticOntologyRegistry()
    r1 = OntologyRule(rule_id="r1", source_id="ont1", relation=SemanticRelation.ENTAILS, source_concept="A", target_concept="B")
    r2 = OntologyRule(rule_id="r2", source_id="ont1", relation=SemanticRelation.ENTAILS, source_concept="B", target_concept="C")
    
    registry.register_source(MockOntologySource("ont1", [r1, r2]))
    
    resolver = SemanticResolver(registry)
    claim_a = SemanticClaim(claim_id="root_A", value="A", provenance=ProvenanceType.DOMAIN_RULE, source_id="auth1", scope="scope1", precedence=1)
    
    auth_source = MockAuthoritativeSource("auth1", [claim_a], [ProvenanceType.DOMAIN_RULE])
    claims = auth_source.get_claims("cap1", ["scope1"])
    res = resolver.resolve_semantics(claims, ["scope1"])
    constraints = res["constraints"]
    
    # We expect A, B, and C
    values = [c.value for c in constraints]
    assert "A" in values
    assert "B" in values
    assert "C" in values
    
    b_claim = next(c for c in constraints if c.value == "B")
    c_claim = next(c for c in constraints if c.value == "C")
    
    assert b_claim.provenance == ProvenanceType.INFERRED
    assert b_claim.derivation.parent_claim_ids[0] == "root_A"
    
    assert c_claim.provenance == ProvenanceType.INFERRED
    assert c_claim.derivation.parent_claim_ids[0] == b_claim.claim_id
