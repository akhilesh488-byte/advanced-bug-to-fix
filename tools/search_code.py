from langchain_core.tools import tool
from pathlib import Path


@tool
def search_code(query: str, ext: str = ".py") -> dict:
    """Find which lines in target_repo contain an exact piece of text.

    This is a case-sensitive substring match on each line, so
    "def calculate_total" matches but "calculate total" does not, and even a
    stray space matters. Returns a list of matches with file, line number and
    the line's text. Use it to locate a function, variable or error string,
    then read_file the matching file.

    Args:
        query: The exact text to look for.
        ext: Only search files with this extension, e.g. ".py".
    """
    try:
        root = Path(__file__).resolve().parent.parent
        root_path = root/"target_repo"

        if not root_path.exists():
            return {"success": False, "matches": [], "error": f"path {root_path} doesnot exist"}

        matches = []

        for file_path in root_path.rglob(f"*{ext}"):
            try:
                content = file_path.read_text("utf-8")

            except UnicodeDecodeError:
                continue

            if query not in content:
                continue

            for i, line in enumerate(content.splitlines(), start=1):
                if query in line:
                    matches.append(
                        {
                            "file": str(file_path.relative_to(root)),
                            "line": i,
                            "text": line.strip()
                        }
                    )

        return {"success": True, "matches": matches, "error": None}

    except Exception as e:
        return {"success": False, "matches": [], "error": str(e)}

