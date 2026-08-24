import json
import os
import sys
import time
import shutil
from pathlib import Path
from typing import Optional, Callable, List, Union

from .handshake import (
    PromptPacket,
    ResponsePacket,
    ExecutionStatus,
    InstructionType,
    create_response_packet,
    PROMPT_PACKET_FILE,
    RESPONSE_PACKET_FILE,
    READY_FILE,
    HUMAN_PROMPT_FILE,
)
from .invoker import BoundedInvoker, InvocationResult

class HardenedWatcher:
    """
    State-machine daemon that monitors `prompt_packet.json` and executes
    agent prompts with identity validation, bounded timeouts, and atomic responses.
    """

    def __init__(
        self,
        active_run_id: str,
        workspace_dir: Optional[Path] = None,
        log_dir: Optional[Path] = None,
        custom_command_builder: Optional[Callable[[PromptPacket], Union[List[str], str]]] = None,
    ):
        self.active_run_id = active_run_id
        self.workspace_dir = (workspace_dir or Path(".")).resolve()
        self.log_dir = log_dir or (self.workspace_dir / "benchmark_suite" / "level6" / "results" / "logs")
        self.invoker = BoundedInvoker(log_dir=self.log_dir)
        self.custom_command_builder = custom_command_builder
        
        self.last_consumed_step_id: int = -1
        self.last_consumed_invocation_id: Optional[str] = None
        self.total_invocations: int = 0

    def default_agent_command(self, packet: PromptPacket) -> List[str]:
        """Constructs the standard CLI invocation command for Antigravity."""
        prompt_instruction = (
            f"Read the file './{HUMAN_PROMPT_FILE}' in the current working directory using a simple file read. Do NOT perform a system search. "
            f"Based on its instructions, generate the requested JSON payload "
            f"and write it to the target file(s): {', '.join(packet.target_artifacts)}. "
            "Do not use markdown blocks around the JSON in the file, just valid raw JSON."
        )
        return ["agy", "--print", prompt_instruction, "--dangerously-skip-permissions"]

    def process_pending_packet(self) -> Optional[ResponsePacket]:
        """
        Checks for an authoritative `prompt_packet.json`, validates identity,
        and triggers execution if and only if it matches the active run.
        """
        packet_path = self.workspace_dir / PROMPT_PACKET_FILE
        if not packet_path.exists():
            return None

        try:
            with open(packet_path, "r", encoding="utf-8") as f:
                packet_data = json.load(f)
            packet = PromptPacket(**packet_data)
        except Exception as e:
            print(f"[Watcher] Warning: Corrupted prompt packet on disk: {e}", file=sys.stderr)
            return None

        # 1. Identity Gate: Verify Run ID
        if packet.run_id != self.active_run_id:
            print(f"[Watcher] Ignoring stale prompt packet: packet run_id='{packet.run_id}' != active_run_id='{self.active_run_id}'", flush=True)
            return None

        # 2. Sequence Gate: Verify Invocation ID and Step ID
        if packet.invocation_id == self.last_consumed_invocation_id:
            return None

        print(f"[{time.strftime('%X')}] [Watcher] Accepted valid PromptPacket: "
              f"scenario='{packet.scenario_id}', step={packet.step_id}, inv='{packet.invocation_id[:8]}'", flush=True)

        # 3. Write human-readable projection
        human_prompt_path = self.workspace_dir / HUMAN_PROMPT_FILE
        with open(human_prompt_path, "w", encoding="utf-8") as f:
            f.write(f"# RUN: {packet.run_id} | SCENARIO: {packet.scenario_id} | STEP: {packet.step_id}\n")
            f.write(f"# INVOCATION: {packet.invocation_id}\n\n")
            f.write(packet.prompt_text)

        # 4. Determine command
        if self.custom_command_builder:
            cmd = self.custom_command_builder(packet)
        else:
            cmd = self.default_agent_command(packet)

        # 5. Execute with bounded timeout
        self.total_invocations += 1
        log_prefix = f"{packet.scenario_id}_step_{packet.step_id}_{packet.invocation_id[:8]}"
        is_shell = isinstance(cmd, str)
        
        inv_result = self.invoker.execute(
            command=cmd,
            timeout_seconds=packet.timeout_seconds,
            log_prefix=log_prefix,
            cwd=self.workspace_dir,
            shell=is_shell,
        )

        # 6. Verify Artifacts & JSON Integrity
        artifacts_produced = []
        status = inv_result.status
        bom_normalized = False

        if status == ExecutionStatus.SUCCESS:
            for art_name in packet.target_artifacts:
                art_path = self.workspace_dir / art_name
                if not art_path.exists():
                    status = ExecutionStatus.MALFORMED_OUTPUT
                    inv_result.error_message = f"Missing requested artifact '{art_name}'"
                    break
                try:
                    with open(art_path, "rb") as f:
                        raw = f.read()
                        if raw.startswith(b'\xef\xbb\xbf'):
                            bom_normalized = True
                            logger.info(f"Artifact '{art_name}' required UTF-8 BOM normalization.")
                            content = raw.decode("utf-8-sig")
                        else:
                            content = raw.decode("utf-8")
                        json.loads(content)
                    artifacts_produced.append(art_name)
                except Exception as je:
                    status = ExecutionStatus.MALFORMED_OUTPUT
                    inv_result.error_message = f"Artifact '{art_name}' contains invalid JSON: {je}"
                    break

        # 7. Construct ResponsePacket
        response = create_response_packet(
            prompt=packet,
            status=status,
            exit_code=inv_result.exit_code,
            duration_seconds=inv_result.duration_seconds,
            artifacts_produced=artifacts_produced,
            stdout_log=inv_result.stdout_log,
            stderr_log=inv_result.stderr_log,
            error_message=inv_result.error_message,
            bom_normalized=bom_normalized,
        )

        # 8. Write atomic response packet
        resp_path = self.workspace_dir / RESPONSE_PACKET_FILE
        with open(resp_path, "w", encoding="utf-8") as rf:
            rf.write(response.model_dump_json(indent=2))

        # Backward compatibility ready token
        ready_path = self.workspace_dir / READY_FILE
        with open(ready_path, "w", encoding="utf-8") as tf:
            tf.write(f"READY {packet.invocation_id}")

        # Update watcher state and remove consumed prompt packet
        self.last_consumed_step_id = packet.step_id
        self.last_consumed_invocation_id = packet.invocation_id
        
        try:
            if packet_path.exists():
                os.remove(packet_path)
        except Exception:
            pass

        print(f"[{time.strftime('%X')}] [Watcher] Finished invocation {packet.invocation_id[:8]} with status: {status.value}", flush=True)
        return response

    def run_loop(self, poll_interval: float = 1.0, stop_after_n: Optional[int] = None):
        """Runs the watcher polling loop."""
        print(f"[Watcher] Started watching '{self.workspace_dir}' for run_id='{self.active_run_id}'...", flush=True)
        processed = 0
        while True:
            resp = self.process_pending_packet()
            if resp:
                processed += 1
                if stop_after_n and processed >= stop_after_n:
                    break
            time.sleep(poll_interval)
