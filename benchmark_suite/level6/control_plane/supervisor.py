import time
import json
from enum import Enum
from pathlib import Path
from typing import Optional
from .handshake import (
    InstructionType,
    ExecutionStatus,
    PromptPacket,
    ResponsePacket,
    create_prompt_packet,
    PROMPT_PACKET_FILE,
    RESPONSE_PACKET_FILE
)
from product.api.v1.models import GapReport

class SupervisorState(str, Enum):
    CONTRACT_BOUND = "CONTRACT_BOUND"
    IMPLEMENTING = "IMPLEMENTING"
    VERIFYING = "VERIFYING"
    FIXING = "FIXING"
    DONE = "DONE"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"

class SupervisorError(Exception):
    pass

class BoundedSupervisor:
    """
    State machine that orchestrates the M8.7 Agent workflow.
    It writes prompt packets and waits for response packets, enforcing state transitions.
    """
    def __init__(
        self,
        run_id: str,
        scenario_id: str,
        decision_id: str,
        workspace_dir: Path,
        max_retries: int = 5,
        poll_interval: float = 1.0,
        verify_callback=None
    ):
        self.run_id = run_id
        self.scenario_id = scenario_id
        self.decision_id = decision_id
        self.workspace_dir = workspace_dir
        self.max_retries = max_retries
        self.poll_interval = poll_interval
        
        self.verify_callback = verify_callback 
        
        self.state: SupervisorState = SupervisorState.CONTRACT_BOUND
        self.retry_count: int = 0
        self.step_counter: int = 1

    def _wait_for_response(self) -> ResponsePacket:
        """Polls for the response_packet.json"""
        resp_path = self.workspace_dir / RESPONSE_PACKET_FILE
        print(f"[Supervisor] Waiting for {resp_path} ...")
        while True:
            if resp_path.exists():
                print(f"[Supervisor] Found {resp_path}, reading...")
                try:
                    with open(resp_path, "r", encoding="utf-8") as rf:
                        data = json.loads(rf.read())
                    response = ResponsePacket(**data)
                    resp_path.unlink()
                    return response
                except Exception as e:
                    with open(self.workspace_dir / "supervisor_err.log", "a") as f:
                        import traceback
                        f.write(traceback.format_exc() + "\n")
                    time.sleep(self.poll_interval)
            else:
                time.sleep(self.poll_interval)

    def _issue_prompt(self, instruction_type: InstructionType, prompt_text: str, target_artifacts: list[str]) -> ResponsePacket:
        """Writes a prompt packet and waits for the response."""
        packet = create_prompt_packet(
            run_id=self.run_id,
            scenario_id=self.scenario_id,
            step_id=self.step_counter,
            instruction_type=instruction_type,
            target_artifacts=target_artifacts,
            prompt_text=prompt_text
        )
        self.step_counter += 1
        
        packet_path = self.workspace_dir / PROMPT_PACKET_FILE
        with open(packet_path, "w", encoding="utf-8") as f:
            f.write(packet.model_dump_json(indent=2))
            
        response = self._wait_for_response()
        
        ready_path = self.workspace_dir / "ready.txt"
        if ready_path.exists():
            ready_path.unlink()
            
        return response

    def transition(self, next_state: SupervisorState):
        """Enforce strict transitions."""
        valid_transitions = {
            SupervisorState.CONTRACT_BOUND: [SupervisorState.IMPLEMENTING],
            SupervisorState.IMPLEMENTING: [SupervisorState.VERIFYING, SupervisorState.HUMAN_REVIEW_REQUIRED],
            SupervisorState.VERIFYING: [SupervisorState.DONE, SupervisorState.FIXING, SupervisorState.HUMAN_REVIEW_REQUIRED],
            SupervisorState.FIXING: [SupervisorState.VERIFYING, SupervisorState.HUMAN_REVIEW_REQUIRED],
            SupervisorState.DONE: [],
            SupervisorState.HUMAN_REVIEW_REQUIRED: []
        }
        
        if next_state not in valid_transitions[self.state]:
            raise SupervisorError(f"Invalid transition from {self.state} to {next_state}")
            
        print(f"[Supervisor] Transitioning: {self.state.value} -> {next_state.value}")
        self.state = next_state

    def run_loop(self):
        """Runs the explicit state machine."""
        print(f"[Supervisor] Starting loop for decision {self.decision_id}")
        
        while self.state not in (SupervisorState.DONE, SupervisorState.HUMAN_REVIEW_REQUIRED):
            if self.state == SupervisorState.CONTRACT_BOUND:
                self.transition(SupervisorState.IMPLEMENTING)
                
            elif self.state == SupervisorState.IMPLEMENTING:
                print(f"[Supervisor] Issuing IMPLEMENT prompt...")
                prompt_text = f"Implement the requirements for Decision {self.decision_id}."
                
                resp = self._issue_prompt(
                    instruction_type=InstructionType.IMPLEMENT,
                    prompt_text=prompt_text,
                    target_artifacts=["status.json"]
                )
                
                if resp.status != ExecutionStatus.SUCCESS:
                    print(f"[Supervisor] Agent failed implementation: {resp.status}")
                    self.transition(SupervisorState.HUMAN_REVIEW_REQUIRED)
                else:
                    self.transition(SupervisorState.VERIFYING)
                    
            elif self.state == SupervisorState.VERIFYING:
                print(f"[Supervisor] Verifying repository against Decision {self.decision_id}...")
                if not self.verify_callback:
                    raise RuntimeError("verify_callback must be provided to run_loop")
                    
                gap_report: Optional[GapReport] = self.verify_callback(self.decision_id, self.workspace_dir)
                
                if not gap_report:
                    print("[Supervisor] Verification passed. No gaps.")
                    self.transition(SupervisorState.DONE)
                else:
                    actual_gaps = []
                    for f in gap_report.findings:
                        if isinstance(f, dict):
                            cat = f.get("category", "")
                        else:
                            cat = getattr(f, "category", "")
                        
                        if cat not in ["MATCH", "EXTRA", "GapCategory.MATCH", "GapCategory.EXTRA"]:
                            actual_gaps.append(f)
                            
                    if not actual_gaps:
                        print("[Supervisor] Verification passed. No gaps.")
                        self.transition(SupervisorState.DONE)
                    else:
                        print(f"[Supervisor] Found {len(actual_gaps)} gaps.")
                        self.transition(SupervisorState.FIXING)
                    
            elif self.state == SupervisorState.FIXING:
                if self.retry_count >= self.max_retries:
                    print(f"[Supervisor] Retry budget exhausted ({self.max_retries}). Escalating to HUMAN_REVIEW_REQUIRED.")
                    self.transition(SupervisorState.HUMAN_REVIEW_REQUIRED)
                    continue
                    
                self.retry_count += 1
                print(f"[Supervisor] Issuing FIX_GAPS prompt (Retry {self.retry_count}/{self.max_retries})...")
                
                prompt_text = "The repository verification failed. Please fix the following gaps:\n"
                prompt_text += "See gap report for details."
                
                resp = self._issue_prompt(
                    instruction_type=InstructionType.FIX_GAPS,
                    prompt_text=prompt_text,
                    target_artifacts=["status.json"]
                )
                
                if resp.status != ExecutionStatus.SUCCESS:
                    print(f"[Supervisor] Agent failed fixing turn: {resp.status}")
                    self.transition(SupervisorState.HUMAN_REVIEW_REQUIRED)
                else:
                    self.transition(SupervisorState.VERIFYING)
                    
        print(f"[Supervisor] Terminated in state: {self.state.value}")
        return self.state
