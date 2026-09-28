from langchain_core.tools import tool
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent

@tool
def run_shell(commands: list[str], cwd: str, timeout: int = 60) -> dict:
    """Run a command in a directory and return its output.

    Pass the command as a list of strings with no shell features, e.g.
    ["python", "main.py"]. Do not pass one combined string, and do not use
    pipes or &&. The program gets no keyboard input, so anything calling
    input() fails immediately with EOFError. A crash shows up as a traceback
    in stderr. Returns success, stdout, stderr and exit_code.

    Args:
        commands: The command and its arguments as a list of strings.
        cwd: Directory to run in. Use "target_repo" to run the original code,
            or your worktree path to test a fix.
        timeout: Seconds before the command is killed.
    """
    try:
        cwd_path = Path(cwd)
        if not cwd_path.is_absolute():
            cwd_path = root/cwd_path

        if commands and commands[0] in ("python", "python3"):
            commands = [sys.executable] + commands[1:]
        result = subprocess.run(
            commands,
            cwd = cwd_path,
            capture_output= True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL 
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": None,
            "stderr": f"command timed out after {timeout} secs",
            "exit_code": None
        }

    except FileNotFoundError as e:
        return {
            "success": False,
            "stdout": None,
            "stderr": str(e),
            "exit_code": None
        }