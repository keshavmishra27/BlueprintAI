import pytest
from pathlib import Path
from product.workspace.binding import write_binding, read_binding, WorkspaceBinding

def test_write_and_read_binding(tmp_path: Path):
    write_binding(
        workspace_dir=tmp_path,
        root_decision_id="root-123",
        decision_id="dec-456",
        decision_fingerprint="fingerprint-abc",
        requirement_set_fingerprint="req-fingerprint-def"
    )
    
    binding = read_binding(tmp_path)
    assert binding is not None
    assert binding.root_decision_id == "root-123"
    assert binding.decision_id == "dec-456"
    assert binding.decision_fingerprint == "fingerprint-abc"
    assert binding.requirement_set_fingerprint == "req-fingerprint-def"

def test_read_missing_binding(tmp_path: Path):
    binding = read_binding(tmp_path)
    assert binding is None

def test_read_corrupt_binding(tmp_path: Path):
    binding_path = tmp_path / ".blueprint" / "contract.json"
    binding_path.parent.mkdir(parents=True, exist_ok=True)
    with open(binding_path, "w", encoding="utf-8") as f:
        f.write("{ invalid json }")
        
    binding = read_binding(tmp_path)
    assert binding is None
