from git import Repo, GitCommandError
from pathlib import Path

root = Path(__file__).resolve().parent.parent

def clone_repo(repo_url: str, relative_path: str = "target_repo") -> dict:

    try:
        clean_path = relative_path.lstrip("/\\")
        target_repo = (root/clean_path).resolve()

        if target_repo.exists() and any(target_repo.iterdir()):
            return {"success": False, "relative_path": None, "error": f"repository {target_repo} already exists"}

        Repo.clone_from(repo_url, target_repo)
        return {"success": True, "relative_path": str(target_repo.relative_to(root)), "error": None}

    except GitCommandError as e:
        return {"success": False, "relative_path": None, "error": str(e)}

