from langchain_core.tools import tool

@tool
def submit_context_report(program_summary: str, diagnosis: str, evidence: str,
                          fault_file_path: str, baseline_output: str, solution: str) -> str:
    """Call this once you have run the code, confirmed the bug, and gathered enough
    context to explain it and propose a fix. This ends your turn."""
    return "submitted"