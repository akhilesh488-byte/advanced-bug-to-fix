from git import Repo, GitCommandError
from pathlib import Path

root = Path(__file__).resolve().parent.parent
target_repo_default = str(root/"target_repo")

def clone_repo(repo_url: str, clone_dir: str = target_repo_default) -> dict:

    try:
        target_repo = Path(clone_dir)

        if target_repo.exists() and any(target_repo.iterdir()):
            return {"success": False, "path": None, "error": f"repository {target_repo} isn't empty"}

        Repo.clone_from(repo_url, clone_dir)
        return {"success": True, "path": clone_dir, "error": None}

    except GitCommandError as e:
        return {"success": False, "path": None, "error": str(e)}

