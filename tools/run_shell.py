import subprocess

def run_shell(commands: list[str], cwd: str, timeout: int = 60) -> dict:

    try:
        result = subprocess.run(
            commands,
            cwd = cwd,
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

print(run_shell(["python3 graph/agent.py"], "."))