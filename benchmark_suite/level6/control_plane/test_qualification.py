import json
import os
import sys
import time
import shutil
import tempfile
from pathlib import Path
import pytest

from benchmark_suite.level6.control_plane.handshake import (
    InstructionType,
    ExecutionStatus,
    PromptPacket,
    ResponsePacket,
    create_prompt_packet,
    validate_identity,
    PROMPT_PACKET_FILE,
    RESPONSE_PACKET_FILE,
    READY_FILE,
    HUMAN_PROMPT_FILE,
)
from benchmark_suite.level6.control_plane.invoker import BoundedInvoker
from benchmark_suite.level6.control_plane.watcher import HardenedWatcher

def test_gate1_stale_isolation_and_valid_dispatch():
    """
    Gate 1: Stale Isolation + Valid Dispatch
    Proves that a stale prompt from a prior run is ignored, and a subsequent valid prompt is executed exactly once.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace = Path(tmp_dir)
        log_dir = workspace / "logs"
        
        # 1. Write stale prompt packet
        stale_packet = create_prompt_packet(
            run_id="v3.1_pilot_01_stale",
            scenario_id="stale_scenario",
            step_id=0,
            instruction_type=InstructionType.QUALIFICATION,
            target_artifacts=["dummy.json"],
            prompt_text="Stale prompt content",
        )
        stale_path = workspace / PROMPT_PACKET_FILE
        with open(stale_path, "w", encoding="utf-8") as f:
            f.write(stale_packet.model_dump_json())

        # 2. Mock command that writes requested dummy.json
        def mock_cmd(packet: PromptPacket):
            dummy_target = workspace / "dummy.json"
            py_code = f"import json; open(r'{dummy_target}', 'w').write(json.dumps({{'status': 'ok'}}))"
            return [sys.executable, "-c", py_code]

        # 3. Start watcher with active run_id
        active_run_id = "v3.1_pilot_03_active"
        watcher = HardenedWatcher(
            active_run_id=active_run_id,
            workspace_dir=workspace,
            log_dir=log_dir,
            custom_command_builder=mock_cmd,
        )

        # Step 3a: Verify stale packet is ignored
        resp_stale = watcher.process_pending_packet()
        assert resp_stale is None, "Gate 1 Failure: Watcher executed a stale prompt packet!"
        assert watcher.total_invocations == 0, "Gate 1 Failure: Invocations count incremented on stale prompt!"

        # 4. Dispatch valid prompt packet
        valid_packet = create_prompt_packet(
            run_id=active_run_id,
            scenario_id="test_scenario",
            step_id=1,
            instruction_type=InstructionType.QUALIFICATION,
            target_artifacts=["dummy.json"],
            prompt_text="Valid prompt content",
        )
        with open(stale_path, "w", encoding="utf-8") as f:
            f.write(valid_packet.model_dump_json())

        # Step 4a: Verify valid packet is processed exactly once
        resp_valid = watcher.process_pending_packet()
        assert resp_valid is not None, "Gate 1 Failure: Watcher failed to process valid prompt packet!"
        assert resp_valid.status == ExecutionStatus.SUCCESS, f"Gate 1 Failure: Execution failed with {resp_valid.status}"
        assert watcher.total_invocations == 1, f"Gate 1 Failure: Expected 1 invocation, got {watcher.total_invocations}"

        # Subsequent check on empty queue must return None
        resp_empty = watcher.process_pending_packet()
        assert resp_empty is None
        assert watcher.total_invocations == 1

        print("Gate 1 Passed: Stale prompt ignored, valid prompt executed exactly once.")

def test_gate2_single_invocation_bounded_execution():
    """
    Gate 2: Single Invocation (Bounded Execution)
    Proves that the invoker executes a command, captures stdout/stderr, and returns within timeout.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace = Path(tmp_dir)
        log_dir = workspace / "logs"
        invoker = BoundedInvoker(log_dir=log_dir)

        # Command that prints stdout and stderr
        py_code = "import sys; sys.stdout.write('OUT_MSG\\n'); sys.stderr.write('ERR_MSG\\n'); sys.exit(0)"
        cmd = [sys.executable, "-c", py_code]

        result = invoker.execute(
            command=cmd,
            timeout_seconds=10.0,
            log_prefix="gate2_test",
            cwd=workspace,
        )

        assert result.status == ExecutionStatus.SUCCESS, f"Gate 2 Failure: Status={result.status}"
        assert result.exit_code == 0, f"Gate 2 Failure: Exit code={result.exit_code}"
        assert result.duration_seconds < 5.0, f"Gate 2 Failure: Duration {result.duration_seconds}s too slow"
        assert result.stdout_log and os.path.exists(result.stdout_log), "Gate 2 Failure: stdout log not written"
        assert result.stderr_log and os.path.exists(result.stderr_log), "Gate 2 Failure: stderr log not written"

        with open(result.stdout_log, "r", encoding="utf-8") as f:
            assert "OUT_MSG" in f.read()
        with open(result.stderr_log, "r", encoding="utf-8") as f:
            assert "ERR_MSG" in f.read()

        print("Gate 2 Passed: Bounded execution completed, streams captured.")

def test_gate3_end_to_end_full_identity_matching():
    """
    Gate 3: End-to-End Handshake & Full Identity Matching
    Proves all 5 identity fields match identically, requested JSON artifact is validated, and response packet is emitted.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace = Path(tmp_dir)
        log_dir = workspace / "logs"
        
        run_id = "v3.1_pilot_03_ident"
        scenario_id = "scenario_alpha"
        step_id = 42
        target_art = "output_arch.json"

        # Mock command creating valid JSON artifact
        def mock_cmd(packet: PromptPacket):
            out_file = workspace / target_art
            data = {
                "architecture": {"name": "TestNode", "cost": 100},
                "uncertainties": [{"id": "U1", "question": "Test?"}],
            }
            py_code = f"import json; open(r'{out_file}', 'w').write(json.dumps({json.dumps(data)}))"
            return [sys.executable, "-c", py_code]

        watcher = HardenedWatcher(
            active_run_id=run_id,
            workspace_dir=workspace,
            log_dir=log_dir,
            custom_command_builder=mock_cmd,
        )

        # 1. Driver creates PromptPacket
        prompt = create_prompt_packet(
            run_id=run_id,
            scenario_id=scenario_id,
            step_id=step_id,
            instruction_type=InstructionType.START,
            target_artifacts=[target_art],
            prompt_text="Generate architecture payload",
        )

        # Write prompt packet
        prompt_path = workspace / PROMPT_PACKET_FILE
        with open(prompt_path, "w", encoding="utf-8") as pf:
            pf.write(prompt.model_dump_json())

        # 2. Watcher processes
        watcher.process_pending_packet()

        # 3. Driver consumes ResponsePacket
        resp_path = workspace / RESPONSE_PACKET_FILE
        assert resp_path.exists(), "Gate 3 Failure: response_packet.json was not created!"

        with open(resp_path, "r", encoding="utf-8") as rf:
            response_data = json.load(rf)
        response = ResponsePacket(**response_data)

        # 4. Identity validation
        id_check = validate_identity(prompt, response)
        assert id_check["valid"], f"Gate 3 Failure: Identity mismatch: {id_check['mismatches']}"
        assert response.run_id == prompt.run_id
        assert response.scenario_id == prompt.scenario_id
        assert response.step_id == prompt.step_id
        assert response.invocation_id == prompt.invocation_id
        assert response.prompt_id == prompt.prompt_id
        assert response.status == ExecutionStatus.SUCCESS
        assert target_art in response.artifacts_produced

        # 5. Artifact verification
        art_path = workspace / target_art
        assert art_path.exists()
        with open(art_path, "r", encoding="utf-8") as af:
            loaded_json = json.load(af)
            assert "architecture" in loaded_json

        print("Gate 3 Passed: 5-dimension identity validated, JSON artifact verified.")

def test_gate4_failure_containment_and_hung_process_kill():
    """
    Gate 4: Failure Containment (Hung Process Termination)
    Proves that a hung/frozen agent process is terminated cleanly at timeout,
    writes RUNTIME_FAILURE / TIMEOUT, and prevents any indefinite deadlock.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace = Path(tmp_dir)
        log_dir = workspace / "logs"
        
        run_id = "v3.1_pilot_03_timeout_test"

        # Mock hung command: sleeps for 60 seconds
        def mock_hung_cmd(packet: PromptPacket):
            py_code = "import time; time.sleep(60)"
            return [sys.executable, "-c", py_code]

        watcher = HardenedWatcher(
            active_run_id=run_id,
            workspace_dir=workspace,
            log_dir=log_dir,
            custom_command_builder=mock_hung_cmd,
        )

        # Driver dispatches prompt with short 1.5s timeout
        prompt = create_prompt_packet(
            run_id=run_id,
            scenario_id="hung_scenario",
            step_id=1,
            instruction_type=InstructionType.QUALIFICATION,
            target_artifacts=["unreachable.json"],
            prompt_text="This command will hang",
            timeout_seconds=1.5,
        )

        prompt_path = workspace / PROMPT_PACKET_FILE
        with open(prompt_path, "w", encoding="utf-8") as pf:
            pf.write(prompt.model_dump_json())

        # Process packet
        t0 = time.time()
        response = watcher.process_pending_packet()
        elapsed = time.time() - t0

        # Assertions
        assert response is not None, "Gate 4 Failure: No response packet emitted on timeout!"
        assert response.status in (ExecutionStatus.TIMEOUT, ExecutionStatus.RUNTIME_FAILURE), f"Gate 4 Failure: Unexpected status {response.status}"
        assert elapsed < 5.0, f"Gate 4 Failure: Hung process took {elapsed}s to terminate (expected ~1.5s)!"
        
        resp_path = workspace / RESPONSE_PACKET_FILE
        assert resp_path.exists()
        with open(resp_path, "r", encoding="utf-8") as rf:
            resp_on_disk = ResponsePacket(**json.load(rf))
            assert resp_on_disk.status in (ExecutionStatus.TIMEOUT, ExecutionStatus.RUNTIME_FAILURE)

        print(f"Gate 4 Passed: Hung process killed cleanly after {elapsed:.2f}s, emitted {response.status}.")

if __name__ == "__main__":
    test_gate1_stale_isolation_and_valid_dispatch()
    test_gate2_single_invocation_bounded_execution()
    test_gate3_end_to_end_full_identity_matching()
    test_gate4_failure_containment_and_hung_process_kill()
    print("\nALL 4 CONTROL-PLANE QUALIFICATION GATES PASSED SUCCESSFULLY!")
