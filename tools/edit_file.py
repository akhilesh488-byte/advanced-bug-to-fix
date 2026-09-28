from langchain_core.tools import tool
from pathlib import Path

root = Path(__file__).resolve().parent.parent

@tool
def edit_file(relative_path: str, old_content: str, new_content: str) -> dict:
    """Replace one exact block of text in an existing file with new text.

    old_content must match the file exactly, including indentation and
    whitespace, so copy it verbatim from read_file output. It must appear
    exactly once. If it is not found, or found more than once, nothing is
    changed and you get an error. Add a few surrounding lines to make a
    repeated snippet unique. Only edit files inside your own worktree
    (sandbox/...), never inside target_repo.

    Args:
        relative_path: Path relative to the project root, e.g. "sandbox/<job_id>-attempt-1/main.py".
        old_content: The exact existing text to replace.
        new_content: The text to put in its place.
    """
    try:

        clean_path = relative_path.lstrip("/\\")
        file_path = Path(root/clean_path).resolve()

        if not file_path.is_relative_to(root.resolve()):
            return {"success": False, "error": f"access denied {relative_path} is outside the working directory"}

        if not file_path.exists():
            return {"success": False, "error": f"the path {relative_path} does not exist."}

        content = file_path.read_text("utf-8")
        count = content.count(old_content)

        if count == 0:
            return {"success": False, "error": "old_content not found in the file"}

        if count > 1:
            return {"success": False, "error": f"old_content is ambiguous, it was found {count} number of times"}

        updated_content = content.replace(old_content, new_content)
        file_path.write_text(updated_content, encoding="utf-8")

        return {"success": True, "error": None}

    except Exception as e:
        return {"success": False, "error": str(e)}
