import json
import hashlib
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

PROMPT_PACKET_FILE = "prompt_packet.json"
RESPONSE_PACKET_FILE = "response_packet.json"
READY_FILE = "ready.txt"
HUMAN_PROMPT_FILE = "current_prompt.md"

class InstructionType(str, Enum):
    START = "START"
    BRANCH = "BRANCH"
    QUALIFICATION = "QUALIFICATION"
    IMPLEMENT = "IMPLEMENT"
    FIX_GAPS = "FIX_GAPS"

class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    RUNTIME_FAILURE = "RUNTIME_FAILURE"
    TIMEOUT = "TIMEOUT"
    MALFORMED_OUTPUT = "MALFORMED_OUTPUT"

class PromptPacket(BaseModel):
    run_id: str
    scenario_id: str
    step_id: int
    invocation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt_id: str
    instruction_type: InstructionType
    target_artifacts: List[str]
    prompt_text: str
    timeout_seconds: float = 60.0
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    def compute_hash(self) -> str:
        content = f"{self.run_id}:{self.scenario_id}:{self.step_id}:{self.invocation_id}:{self.prompt_text}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

class ResponsePacket(BaseModel):
    run_id: str
    scenario_id: str
    step_id: int
    invocation_id: str
    prompt_id: str
    status: ExecutionStatus
    exit_code: Optional[int] = None
    duration_seconds: float = 0.0
    artifacts_produced: List[str] = Field(default_factory=list)
    stdout_log: Optional[str] = None
    stderr_log: Optional[str] = None
    error_message: Optional[str] = None
    bom_normalized: bool = False
    completed_at: str = Field(default_factory=lambda: datetime.now().isoformat())

def create_prompt_packet(
    run_id: str,
    scenario_id: str,
    step_id: int,
    instruction_type: InstructionType,
    target_artifacts: List[str],
    prompt_text: str,
    timeout_seconds: float = 60.0,
    invocation_id: Optional[str] = None,
) -> PromptPacket:
    inv_id = invocation_id or str(uuid.uuid4())
    raw_hash = hashlib.sha256(f"{run_id}:{scenario_id}:{step_id}:{inv_id}:{prompt_text}".encode("utf-8")).hexdigest()
    return PromptPacket(
        run_id=run_id,
        scenario_id=scenario_id,
        step_id=step_id,
        invocation_id=inv_id,
        prompt_id=raw_hash,
        instruction_type=instruction_type,
        target_artifacts=target_artifacts,
        prompt_text=prompt_text,
        timeout_seconds=timeout_seconds,
    )

def create_response_packet(
    prompt: PromptPacket,
    status: ExecutionStatus,
    exit_code: Optional[int] = None,
    duration_seconds: float = 0.0,
    artifacts_produced: Optional[List[str]] = None,
    stdout_log: Optional[str] = None,
    stderr_log: Optional[str] = None,
    error_message: Optional[str] = None,
    bom_normalized: bool = False,
) -> ResponsePacket:
    return ResponsePacket(
        run_id=prompt.run_id,
        scenario_id=prompt.scenario_id,
        step_id=prompt.step_id,
        invocation_id=prompt.invocation_id,
        prompt_id=prompt.prompt_id,
        status=status,
        exit_code=exit_code,
        duration_seconds=duration_seconds,
        artifacts_produced=artifacts_produced or [],
        stdout_log=stdout_log,
        stderr_log=stderr_log,
        error_message=error_message,
        bom_normalized=bom_normalized,
    )

def validate_identity(prompt: PromptPacket, response: ResponsePacket) -> Dict[str, Any]:
    """
    Rigorously verifies all 5 identity dimensions:
    1. run_id
    2. scenario_id
    3. step_id
    4. invocation_id
    5. prompt_id
    """
    mismatches = []
    if response.run_id != prompt.run_id:
        mismatches.append(f"run_id mismatch: expected '{prompt.run_id}', got '{response.run_id}'")
    if response.scenario_id != prompt.scenario_id:
        mismatches.append(f"scenario_id mismatch: expected '{prompt.scenario_id}', got '{response.scenario_id}'")
    if response.step_id != prompt.step_id:
        mismatches.append(f"step_id mismatch: expected {prompt.step_id}, got {response.step_id}")
    if response.invocation_id != prompt.invocation_id:
        mismatches.append(f"invocation_id mismatch: expected '{prompt.invocation_id}', got '{response.invocation_id}'")
    if response.prompt_id != prompt.prompt_id:
        mismatches.append(f"prompt_id mismatch: expected '{prompt.prompt_id}', got '{response.prompt_id}'")
        
    return {
        "valid": len(mismatches) == 0,
        "mismatches": mismatches,
    }
