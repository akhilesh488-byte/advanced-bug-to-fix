from pathlib import Path

root = Path(__file__).resolve().parent.parent
target_repo = root / "target_repo"

def list_files(target_repo: str = target_repo) -> dict:
    try:
        repo_path = Path(target_repo)

        if not repo_path.exists():
            return {"success": False, "error": "directory does not exists"}

        files = []
        for path in repo_path.rglob("*"):
            if path.is_file(): #this also avoids empty directories in the target_repo
                files.append(str(path.relative_to(repo_path)))

        return {"success": True, "files": files, "error": None} 

    except Exception as e:
        return {"success": False, "error": str(e)}
