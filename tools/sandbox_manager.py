from langchain_core.tools import tool
from pathlib import Path
from git import Repo, GitCommandError

root = Path(__file__).resolve().parent.parent
target_repo_default = str(root/"target_repo")
branch_repo_default = str(root/"sandbox")

@tool
def create_branch(job_id: str, attempt_no: int, target_repo_path: str = target_repo_default, branch_repo_path: str = branch_repo_default) -> dict:
    """Start a new fix attempt in its own isolated working folder.

    Creates a git branch and a separate copy of the repo under sandbox/, so
    you can edit and test without touching target_repo. Call once per attempt
    before editing anything. Every new attempt, including a retry, needs a
    new attempt_no. Returns branch_name, worktree_path (use it as cwd for
    run_shell and for commit_changes / discard_attempt) and
    relative_worktree_path (use it as the prefix for file paths).

    Args:
        job_id: The job id given in your instructions.
        attempt_no: 1 for the first attempt, then 2, 3 and so on.
        target_repo_path: Leave unset.
        branch_repo_path: Leave unset.
    """
    try:
        repo = Repo(target_repo_path)

        branch_name = f"bugfix/{job_id}-attempt-{attempt_no}"
        worktree_path = str(Path(branch_repo_path)/f"{job_id}-attempt-{attempt_no}")

        repo.git.worktree("add", "-b", branch_name, worktree_path)

        return {
            "success": True,
            "branch_name": branch_name,
            "relative_worktree_path": str(Path(worktree_path).relative_to(root)),
            "error": None
        }

    except GitCommandError as g:
        return {"success": False, "branch_name": None, "worktree_path": None, "error": str(g)}

    except Exception as e:
        return {"success": False, "branch_name": None, "worktree_path": None, "error": str(e)}

@tool
def discard_attempt(worktree_path: str, branch_name: str, target_repo_path: str = target_repo_default) -> dict:
    """Throw away a failed attempt but keep its history.

    Removes the attempt's working folder and renames its branch with a
    "-failed" suffix so it can still be inspected later. Call commit_changes
    first, because uncommitted edits are deleted with the folder. Never use
    this on the attempt that worked.

    Args:
        worktree_path: The worktree_path returned by create_branch.
        branch_name: The branch_name returned by create_branch.
        target_repo_path: Leave unset.
    """
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
    """Save everything changed in a worktree as one commit.

    Call this when you are finished editing an attempt, whether or not the fix
    worked, and always before discard_attempt. Fails with "no changes to
    commit" if nothing was modified.

    Args:
        worktree_path: The worktree_path returned by create_branch.
        commit_message: One line describing what this attempt changed.
    """
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

    