from langchain_core.tools import tool
from pathlib import Path
from git import Repo, GitCommandError

root = Path(__file__).resolve().parent.parent
target_repo_default = str(root/"target_repo")
branch_repo_default = str(root/"sandbox")

@tool
def create_branch(job_id: str, attempt_no: int, target_repo_path: str = target_repo_default, branch_repo_path: str = branch_repo_default) -> dict:
    """call this tool to create a new branch in the target_repo folder and add a worktree for it in the sandbox folder"""
    try:
        repo = Repo(target_repo_path)

        branch_name = f"bugfix/{job_id}-attempt-{attempt_no}"
        worktree_path = str(Path(branch_repo_path)/f"{job_id}-attempt-{attempt_no}")

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

@tool
def discard_attempt(worktree_path: str, branch_name: str, target_repo_path: str = target_repo_default) -> dict:
    """call this tool to discard a failed attempt by removing the worktree and renaming the branch in the target_repo folder"""
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

@tool
def commit_changes(worktree_path: str, commit_message: str) -> dict:
    """call this tool to commit changes in a worktree"""
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

    