from langchain_core.tools import tool

@tool(parse_docstring=True)
def submit_verdict(verdict: str, bug_summary: str, fix_summary: str,
                   verification_evidence: str, remaining_concerns: str,
                   suggested_improvements: str, needs_human_review: bool) -> str:
    """Submit your final verdict and end your turn. Call this once, alone, after checking the fix.

    Args:
        verdict: One of "fixed", "partially fixed" or "not fixed".
        bug_summary: What the bug was and its root cause, in plain language.
        fix_summary: What was changed and why it addresses the root cause.
        verification_evidence: Output before and after the fix, and how you compared them.
        remaining_concerns: Anything still risky or unverified, or "none".
        suggested_improvements: Optional follow-ups for the human reviewer.
        needs_human_review: True if a person should look at this before merging.
    """
    return "submitted"