from pathlib import Path


def search_code(query: str, ext: str = ".py") -> dict:

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
                            "file": str(file_path),
                            "line": i,
                            "text": line.strip()
                        }
                    )

            return {"success": True, "matches": matches, "error": None}

    except Exception as e:
        return {"success": False, "matches": [], "error": str(e)}

