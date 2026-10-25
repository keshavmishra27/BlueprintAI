import uuid
from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel

class AuthenticatedDecisionEvidence(BaseModel):
    model_config = {"frozen": True, "arbitrary_types_allowed": True}
    
    architecture_fingerprint: str
    authorized_predicates: List[str]
    satisfied_predicates: List[Any]
    policy_version: str
    policy_hash: str

class EvaluationReceipt(BaseModel):
    model_config = {"frozen": True}
    
    receipt_id: str
    path_id: str
    architecture_fingerprint: str
    context_fingerprint: str
    evaluation_result: Literal["ACTIVE", "REJECTED", "TERMINAL", "UNRESOLVED"]
    evaluation_sequence: int
    evidence: Optional[AuthenticatedDecisionEvidence] = None

class EvaluationLedger:
    def __init__(self):
        # Append-only history of receipts (historical truth)
        self._history: List[EvaluationReceipt] = []
        # Index to lookup receipts by receipt_id
        self._receipts_by_id: Dict[str, EvaluationReceipt] = {}
        # Tracks the most recent evaluation sequence for each path_id
        self._current_sequence: Dict[str, int] = {}
        # Tracks the current authoritative receipt for each path_id (current authority)
        self._current_receipt: Dict[str, EvaluationReceipt] = {}
        # Stores the historical architecture snapshot for each receipt
        self._historical_snapshots: Dict[str, "ArchitectureNode"] = {}

    def record_evaluation_event(
        self, 
        path_id: str, 
        architecture_fingerprint: str, 
        context_fingerprint: str, 
        result: Literal["ACTIVE", "REJECTED", "TERMINAL", "UNRESOLVED"], 
        arch_snapshot: "ArchitectureNode",
        evidence: Optional[AuthenticatedDecisionEvidence] = None
    ) -> EvaluationReceipt:
        seq = self._current_sequence.get(path_id, 0) + 1
        receipt = EvaluationReceipt(
            receipt_id=str(uuid.uuid4()),
            path_id=path_id,
            architecture_fingerprint=architecture_fingerprint,
            context_fingerprint=context_fingerprint,
            evaluation_result=result,
            evaluation_sequence=seq,
            evidence=evidence
        )
        self._history.append(receipt)
        self._receipts_by_id[receipt.receipt_id] = receipt
        import copy
        self._historical_snapshots[receipt.receipt_id] = copy.deepcopy(arch_snapshot)
        self._current_sequence[path_id] = seq
        self._current_receipt[path_id] = receipt
        return receipt

    def get_receipt(self, receipt_id: str) -> Optional[EvaluationReceipt]:
        return self._receipts_by_id.get(receipt_id)

    def get_historical_architecture(self, receipt_id: str) -> Optional["ArchitectureNode"]:
        return self._historical_snapshots.get(receipt_id)

    def is_current(self, receipt: EvaluationReceipt) -> bool:
        if receipt.path_id not in self._current_receipt:
            return False
        return self._current_receipt[receipt.path_id].receipt_id == receipt.receipt_id

# Global ledger instance for engine runs
_global_ledger = EvaluationLedger()

def get_ledger() -> EvaluationLedger:
    return _global_ledger

def reset_ledger():
    global _global_ledger
    _global_ledger = EvaluationLedger()
