import pytest
import os
import json
import threading
import time
from pathlib import Path

from product.service import ProductService
from product.api.v1.models import GapReport
from benchmark_suite.level6.control_plane.supervisor import BoundedSupervisor, SupervisorState
from benchmark_suite.level6.control_plane.handshake import PROMPT_PACKET_FILE, RESPONSE_PACKET_FILE, ResponsePacket, ExecutionStatus
from product.workspace.binding import write_binding, read_binding
from product.agent.tools import AgentTools

from idea_refiner.parsers.base import BaseIdeaParser
from decision_engine.tree.optimizer import PathNode
from decision_engine.input_layer.schemas import ArchitectureNode

class M8_8_IdeaParser(BaseIdeaParser):
    def parse_idea_to_graph(self, idea: str) -> list[PathNode]:
        arch = ArchitectureNode(
            inputs=[], processing=[], decision=[], output=[], capabilities=[],
            data_required=[], resources_required=[], constraints=[],
            semantic_dependencies=[], evidence_provenance=[], architectural_decisions={}
        )
        arch.processing = ["FastAPI", "PostgreSQL"]
        return [PathNode(
            id="D0_Candidate", parent_id="root",
            architecture=arch,
            status="TERMINAL", path_score=100.0, path_cost=5.0, operational_complexity=2.0
        )]

def mock_agent_loop(workspace_dir: Path):
    """
    Mock agent that reads PROMPT packets and implements changes in the physical repository.
    """
    while True:
        prompt_path = workspace_dir / PROMPT_PACKET_FILE
        if prompt_path.exists():
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if not content:
                    continue
                data = json.loads(content)
                instruction_type = data.get("instruction_type")
                step_id = data.get("step_id")
                
                req_path = workspace_dir / "requirements.txt"
                
                if instruction_type == "IMPLEMENT":
                    req_path.write_text("fastapi\n")
                    
                elif instruction_type == "FIX_GAPS":
                    req_path.write_text("fastapi\npsycopg2\n")
                    
                resp = ResponsePacket(
                    run_id=data["run_id"],
                    scenario_id=data["scenario_id"],
                    step_id=step_id,
                    invocation_id=data["invocation_id"],
                    prompt_id=data["prompt_id"],
                    status=ExecutionStatus.SUCCESS,
                    error_message=None,
                    artifacts_produced=["status.json"]
                )
                
                resp_path = workspace_dir / RESPONSE_PACKET_FILE
                with open(resp_path, "w", encoding="utf-8") as f:
                    f.write(resp.model_dump_json(indent=2))
                    
                prompt_path.unlink()
                
                if instruction_type == "FIX_GAPS":
                    break
            except json.JSONDecodeError:
                pass
            except Exception as e:
                import traceback
                traceback.print_exc()
                os._exit(1)
        time.sleep(0.1)

def test_m8_8_integration(db_session, tmp_path):
    product_service = ProductService(db_session)
    
    decision = product_service.analyze_idea(
        "Build a hospital overcrowding prediction system",
        context={},
        parser=M8_8_IdeaParser()
    )
    
    recent = product_service.get_recent_decisions(limit=10)
    assert len(recent) > 0
    ui_d0 = recent[0]
    
    assert ui_d0.id == decision.id
    assert ui_d0.decision_fingerprint == decision.decision_fingerprint
    assert ui_d0.requirement_set_fingerprint == decision.requirement_set_fingerprint
    
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir(exist_ok=True)
    write_binding(
        workspace_dir, 
        root_decision_id=decision.id,
        decision_id=decision.id, 
        decision_fingerprint=decision.decision_fingerprint,
        requirement_set_fingerprint=decision.requirement_set_fingerprint
    )
    
    binding = read_binding(workspace_dir)
    assert binding.decision_id == ui_d0.id
    assert binding.decision_fingerprint == ui_d0.decision_fingerprint
    assert binding.requirement_set_fingerprint == ui_d0.requirement_set_fingerprint
    
    agent_tools = AgentTools(workspace_dir, product_service)
    
    def verify_callback(decision_id: str, ws_dir: Path):
        return agent_tools.verify_repository()

    supervisor = BoundedSupervisor(
        run_id="test_m88",
        scenario_id="scenario_1",
        decision_id=decision.id,
        workspace_dir=workspace_dir,
        verify_callback=verify_callback,
        poll_interval=0.1
    )
    
    t = threading.Thread(target=mock_agent_loop, args=(workspace_dir,))
    t.start()
    
    final_state = supervisor.run_loop()
    t.join(timeout=5.0)
    
    assert final_state == SupervisorState.DONE
    
    req_contents = (workspace_dir / "requirements.txt").read_text()
    assert "fastapi" in req_contents
    assert "psycopg2" in req_contents
    
    final_d0 = product_service.get_decision(decision.id)
    assert final_d0.decision_fingerprint == ui_d0.decision_fingerprint
    assert final_d0.requirement_set_fingerprint == ui_d0.requirement_set_fingerprint
