import os
import sys
import time
import subprocess
from pathlib import Path
from typing import List, Optional, Union
from pydantic import BaseModel
import psutil

from .handshake import ExecutionStatus, PromptPacket

class InvocationResult(BaseModel):
    status: ExecutionStatus
    exit_code: Optional[int] = None
    duration_seconds: float = 0.0
    stdout_log: Optional[str] = None
    stderr_log: Optional[str] = None
    error_message: Optional[str] = None

class BoundedInvoker:
    """
    Executes an external command (e.g. `agy --print ...` or custom script) with
    strict timeout enforcement, process-tree termination, and persistent telemetry logging.
    """

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path("benchmark_suite/level6/results/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _kill_process_tree(self, pid: int):
        """Kills the target process and all of its spawned child processes cleanly."""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            parent.kill()
            psutil.wait_procs(children + [parent], timeout=3.0)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        except Exception as e:
            print(f"[BoundedInvoker] Warning killing process tree for PID {pid}: {e}", file=sys.stderr)

    def execute(
        self,
        command: Union[List[str], str],
        timeout_seconds: float,
        log_prefix: str = "inv",
        cwd: Optional[Path] = None,
        shell: bool = False,
    ) -> InvocationResult:
        """
        Executes command synchronously with bounded timeout and process tree killing.
        """
        stdout_path = self.log_dir / f"{log_prefix}.stdout.log"
        stderr_path = self.log_dir / f"{log_prefix}.stderr.log"

        start_time = time.time()
        
        try:
            with open(stdout_path, "w", encoding="utf-8", errors="replace") as out_f, \
                 open(stderr_path, "w", encoding="utf-8", errors="replace") as err_f:
                
                proc = subprocess.Popen(
                    command,
                    stdout=out_f,
                    stderr=err_f,
                    cwd=str(cwd) if cwd else None,
                    shell=shell,
                    universal_newlines=True,
                )

                try:
                    proc.wait(timeout=timeout_seconds)
                    duration = time.time() - start_time
                    exit_code = proc.returncode

                    if exit_code == 0:
                        return InvocationResult(
                            status=ExecutionStatus.SUCCESS,
                            exit_code=exit_code,
                            duration_seconds=duration,
                            stdout_log=str(stdout_path),
                            stderr_log=str(stderr_path),
                        )
                    else:
                        return InvocationResult(
                            status=ExecutionStatus.RUNTIME_FAILURE,
                            exit_code=exit_code,
                            duration_seconds=duration,
                            stdout_log=str(stdout_path),
                            stderr_log=str(stderr_path),
                            error_message=f"Process exited with non-zero code {exit_code}",
                        )

                except subprocess.TimeoutExpired:
                    duration = time.time() - start_time
                    print(f"[BoundedInvoker] Process timed out after {timeout_seconds}s. Terminating PID {proc.pid}...", flush=True)
                    self._kill_process_tree(proc.pid)
                    
                    return InvocationResult(
                        status=ExecutionStatus.TIMEOUT,
                        exit_code=None,
                        duration_seconds=duration,
                        stdout_log=str(stdout_path),
                        stderr_log=str(stderr_path),
                        error_message=f"Execution exceeded bounded timeout of {timeout_seconds}s",
                    )

        except Exception as e:
            duration = time.time() - start_time
            return InvocationResult(
                status=ExecutionStatus.RUNTIME_FAILURE,
                exit_code=None,
                duration_seconds=duration,
                stdout_log=str(stdout_path),
                stderr_log=str(stderr_path),
                error_message=f"Subprocess spawn exception: {str(e)}",
            )
