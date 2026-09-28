from langchain_core.tools import tool
from pathlib import Path

root = Path(__file__).resolve().parent.parent

@tool
def read_file(relative_path: str) -> dict:
    """Read the full text of one file and return its content.

    Always returns the whole file. If you don't know the path yet, use
    list_files or search_code first. Returns success, content and error.

    Args:
        relative_path: Path relative to the project root, exactly as shown by
            list_files or search_code, e.g. "target_repo/src/main.py".
    """
    try:
        clean_path = relative_path.lstrip("/\\")
        file_path = (root/clean_path).resolve()
        
        if not file_path.is_relative_to(root):
            return {"success": False, "error": f"access denied {relative_path} is outside the working directory"}

        if not file_path.exists():
            return {"success": False, "content": None, "error": f"file {file_path} does not exist"}

        if not file_path.is_file():
            return {"success": False, "content": None, "error": f"file {file_path} is not readable"}

        content = file_path.read_text(encoding="utf-8")
        return {"success": True, "content": content, "error": None}

    except UnicodeDecodeError:
        return {"success": False, "content": None, "error": f"file {file_path} is not in utf-8 format"}

    except Exception as e:
        return {"success": False, "content": None, "error": str(e)}

    