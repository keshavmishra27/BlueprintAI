from decision_engine.input_layer.schemas import (
    UnvalidatedArchitectureHypothesis,
    ArchitectureNode,
    CapabilityNode
)

class ArchitectureTranslationError(Exception):
    """Raised when an unvalidated hypothesis cannot be deterministically translated."""
    pass

class ArchitectureFactory:
    """
    A strict translation boundary that deterministically converts an 
    UnvalidatedArchitectureHypothesis into an ArchitectureNode.
    
    It rejects malformed, ambiguous, or authority-bearing data, and 
    strictly avoids sanitizing, inferring, or minting capabilities.
    """
    
    @staticmethod
    def translate(hypothesis: UnvalidatedArchitectureHypothesis) -> ArchitectureNode:
        if not isinstance(hypothesis, UnvalidatedArchitectureHypothesis):
            raise ArchitectureTranslationError("Input must be an UnvalidatedArchitectureHypothesis")

        capabilities = []
        for cap_prop in hypothesis.capabilities:
            # We cannot infer SemanticClaims from raw strings. If a proposal
            # contains raw strings for properties or constraints, it is ambiguous.
            if cap_prop.proposed_functional_properties or cap_prop.proposed_constraints:
                raise ArchitectureTranslationError(
                    f"Ambiguous capabilities in proposal '{cap_prop.name}': "
                    "Cannot infer SemanticClaims from raw strings."
                )
                
            capabilities.append(
                CapabilityNode(
                    capability_id=cap_prop.proposal_id,
                    name=cap_prop.name,
                    functional_properties=[],
                    constraints=[],
                    reference_implementation=cap_prop.proposed_implementation
                )
            )

        # Deterministic structural translation
        return ArchitectureNode(
            inputs=list(hypothesis.inputs),
            processing=list(hypothesis.processing),
            decision=list(hypothesis.decision),
            output=list(hypothesis.output),
            capabilities=capabilities,
            semantic_dependencies=list(hypothesis.semantic_dependencies),
            data_required=list(hypothesis.data_required),
            resources_required=list(hypothesis.resources_required),
            constraints=list(hypothesis.constraints),
            architectural_decisions=dict(hypothesis.architectural_decisions)
        )
