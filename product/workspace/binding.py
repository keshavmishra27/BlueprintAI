import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

class WorkspaceBinding(BaseModel):
    root_decision_id: str
    decision_id: str
    decision_fingerprint: str
    requirement_set_fingerprint: str

def get_binding_path(workspace_dir: Path) -> Path:
    return workspace_dir / ".blueprint" / "contract.json"

def write_binding(
    workspace_dir: Path,
    root_decision_id: str,
    decision_id: str,
    decision_fingerprint: str,
    requirement_set_fingerprint: str
) -> None:
    """
    Writes the minimal identity assertion to the workspace.
    This does NOT contain the full contract, only the identity claims.
    """
    binding_path = get_binding_path(workspace_dir)
    binding_path.parent.mkdir(parents=True, exist_ok=True)
    
    binding = WorkspaceBinding(
        root_decision_id=root_decision_id,
        decision_id=decision_id,
        decision_fingerprint=decision_fingerprint,
        requirement_set_fingerprint=requirement_set_fingerprint
    )
    
    with open(binding_path, "w", encoding="utf-8") as f:
        f.write(binding.model_dump_json(indent=2))

def read_binding(workspace_dir: Path) -> Optional[WorkspaceBinding]:
    """
    Reads the workspace identity assertion.
    """
    binding_path = get_binding_path(workspace_dir)
    if not binding_path.exists():
        return None
        
    try:
        with open(binding_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return WorkspaceBinding(**data)
    except Exception:
        return None
