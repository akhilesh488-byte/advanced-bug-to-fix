from pathlib import Path
from git import Repo, GitCommandError


def create_branch(job_id: str, attempt_no: int) -> dict:
    try:
        root = Path(__file__).resolve().parent.parent
        target_repo = str(root/"target_repo")
        branch_repo = str(root/"sandbox")
        repo = Repo(target_repo)

        branch_name = f"bugfix/{job_id}-attempt-{attempt_no}"
        worktree_path = str(Path(branch_repo)/f"{job_id}-attempt-{attempt_no}")

        repo.git.worktree("add", "-b", branch_name, worktree_path)

        return {
            "success": True,
            "branch_name": branch_name,
            "worktree_path": worktree_path,
            "error": None
        }

    except GitCommandError as g:
        return {"success": False, "branch_name": None, "worktree_path": None, "error": str(g)}

    except Exception as e:
        return {"success": False, "branch_name": None, "worktree_path": None, "error": str(e)}

def discard_attempt(worktree_path: str, branch_name: str, target_repo_path: str = target_repo_default) -> dict:
    try:
        repo = Repo(target_repo_path)

        repo.git.worktree("remove", worktree_path, "--force") #first delete the temporary folder

        failed_branch_name = f"{branch_name}-failed"
        repo.git.branch("-m", branch_name, failed_branch_name) #now rename the branch to indicate the failed attempt

        return {"success": True, "renamed_branch": failed_branch_name, "error": None}

    except GitCommandError as g:
        return {"success": False, "renamed_branch": None, "error": str(g)}

    except Exception as e:
        return {"success": False, "renamed_branch": None, "error": str(e)}

def commit_changes(worktree_path: str, commit_message: str) -> dict:
    try:
        repo = Repo(worktree_path)

        if not repo.is_dirty(untracked_files=True):
            return {"success": False, "error": "no changes to commit"}

        repo.git.add(A = True)
        repo.git.commit(m = commit_message)

        return {"success": True, "error": None}

    except GitCommandError as g:
        return {"success": False, "error": str(g)}

    except Exception as e:
        return {"success": False, "error": str(e)}

    