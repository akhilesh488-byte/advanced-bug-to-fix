from langchain_core.tools import tool
from pathlib import Path

root = Path(__file__).resolve().parent.parent

@tool
def write_file(relative_path: str, new_content: str, overwrite: bool = False) -> dict:
    """Create a new file with the given content.

    Refuses to replace an existing file unless overwrite=True, so only set
    that when you really mean to replace it. To change part of an existing
    file use edit_file instead. Only write inside your own worktree
    (sandbox/...), never inside target_repo.

    Args:
        relative_path: Path relative to the project root, e.g. "sandbox/<job_id>-attempt-1/test_fix.py".
        new_content: The complete text to write into the file.
        overwrite: Set True to replace a file that already exists.
    """
    try:
        clean_path = relative_path.lstrip("/\\")
        file_path = (root / clean_path).resolve()

        if not file_path.is_relative_to(root):
            return {"success": False, "error": f"path {file_path} is out of working directory"}

        if file_path.exists() and not overwrite:
            return {"success": False, "error": f"path {file_path} already exists and to replace it pass overwrite = True"}

        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(new_content, encoding="utf-8")

        return {"success": True, "error": None}

    except Exception as e:
        return {"success": False, "error": str(e)}
