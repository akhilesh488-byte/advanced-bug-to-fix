from langchain_core.tools import tool
from pathlib import Path

root = Path(__file__).resolve().parent.parent

@tool
def list_files(relative_path: str = "target_repo") -> dict:
    """List every file inside a folder, including subfolders.

    Returns file paths relative to the project root, not folders.

    Args:
        relative_path: Folder to list, relative to the project root.
    """
    try:
        clean_path = relative_path.lstrip("/\\")
        repo_path = (root/clean_path).resolve()

        if not repo_path.exists():
            return {"success": False, "error": "directory does not exists"}

        files = []
        for path in repo_path.rglob("*"):
            if path.is_file(): #this also avoids empty directories in the target_repo
                files.append(str(path.relative_to(repo_path)))

        return {"success": True, "files": files, "error": None} 

    except Exception as e:
        return {"success": False, "error": str(e)}
