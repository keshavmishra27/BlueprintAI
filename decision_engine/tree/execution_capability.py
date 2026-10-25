from decision_engine.tree.context import AuthenticatedSemanticContext

class ExecutionCapability:
    def __init__(self, capability_id: str, context: AuthenticatedSemanticContext, authorized_architecture_fingerprint: str = ""):
        self.capability_id = capability_id
        self._context = context
        self.authorized_architecture_fingerprint = authorized_architecture_fingerprint
        
    def consume(self, arch) -> AuthenticatedSemanticContext:
        """
        Consumes the capability. Internally delegates to the verifier's secure boundary 
        to ensure the Optimizer remains completely unaware of authentication mechanics.
        """
        from decision_engine.input_layer.authority_verifier import _consume_capability
        return _consume_capability(self, arch)
