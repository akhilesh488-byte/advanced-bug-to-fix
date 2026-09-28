from langchain_core.tools import tool

@tool
def submit_fix_result(branch_name: str, fix_summary: str, attempts_made: str,
                      fix_verified: bool, theory_held: bool) -> str:
    """Call this once you have finished attempting a fix, whether or not it succeeded.
    This ends your turn."""
    return "submitted"