from typing import List, Protocol, Set, Dict, Tuple, Optional
from decision_engine.input_layer.schemas import OntologyRule, SemanticRelation

class RegisteredOntologySource(Protocol):
    source_id: str
    
    def get_rules(self) -> List[OntologyRule]:
        ...

class SemanticOntologyRegistry:
    def __init__(self):
        self.registered_sources: List[RegisteredOntologySource] = []
        self._rules: List[OntologyRule] = []
        
    def register_source(self, source: RegisteredOntologySource):
        self.registered_sources.append(source)
        # Load rules eagerly for simplicity
        self._rules.extend(source.get_rules())

    def is_known(self, concept: str) -> bool:
        """
        Returns True if the concept is part of the ontology's vocabulary.
        """
        for rule in self._rules:
            if rule.source_concept == concept or rule.target_concept == concept:
                return True
        return False

    def get_equivalents(self, concept: str) -> List[str]:
        """
        Returns all concepts equivalent to the given concept, including itself.
        Performs a simple transitive closure over EQUIVALENT rules.
        """
        equivalents = {concept}
        added = True
        while added:
            added = False
            for rule in self._rules:
                if rule.relation == SemanticRelation.EQUIVALENT:
                    if rule.source_concept in equivalents and rule.target_concept not in equivalents:
                        equivalents.add(rule.target_concept)
                        added = True
                    if rule.target_concept in equivalents and rule.source_concept not in equivalents:
                        equivalents.add(rule.source_concept)
                        added = True
        return list(equivalents)
        
    def get_canonical_concept(self, concept: str) -> str:
        """
        Returns a deterministic canonical representative for a concept.
        """
        if not self.is_known(concept):
            return concept
        equivs = self.get_equivalents(concept)
        # We sort them to always pick the same one
        return sorted(equivs)[0]
        
    def get_all_entailments(self, concept: str) -> Dict[str, Tuple[str, OntologyRule]]:
        """
        Returns all concepts entailed by the given concept (transitive closure over ENTAILS).
        Returns a dictionary mapping the entailed concept to a tuple of (parent_concept, rule)
        that produced it, for derivation provenance.
        Does not traverse CONTRADICTS.
        Treats EQUIVALENT as canonicalization, but EQUIVALENT is not bidirectional ENTAILS.
        """
        entailments: Dict[str, Tuple[str, OntologyRule]] = {}
        
        # Start with the equivalents of the root concept
        base_equivs = self.get_equivalents(concept)
        
        queue = list(base_equivs)
        visited = set(base_equivs)
        
        while queue:
            current = queue.pop(0)
            
            curr_equivs = self.get_equivalents(current)
            
            for rule in self._rules:
                if rule.relation == SemanticRelation.ENTAILS and rule.source_concept in curr_equivs:
                    target = rule.target_concept
                    target_equivs = self.get_equivalents(target)
                    
                    for eq in target_equivs:
                        if eq not in visited:
                            visited.add(eq)
                            queue.append(eq)
                            entailments[eq] = (current, rule)
                            
        return entailments

    def contradicts(self, concept_a: str, concept_b: str) -> Tuple[bool, Optional[str]]:
        """
        Checks if two concepts contradict each other strictly based on CONTRADICTS rules.
        Does NOT automatically propagate through entailment closures.
        Returns a tuple of (is_contradicting, rule_id).
        """
        equiv_a = self.get_equivalents(concept_a)
        equiv_b = self.get_equivalents(concept_b)
        
        for rule in self._rules:
            if rule.relation == SemanticRelation.CONTRADICTS:
                if (rule.source_concept in equiv_a and rule.target_concept in equiv_b) or \
                   (rule.target_concept in equiv_a and rule.source_concept in equiv_b):
                    return True, rule.rule_id
        return False, None
