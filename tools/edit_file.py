from pathlib import Path

def edit_file(path: str, old_content: str, new_content: str) -> dict:

    try:

        file_path = Path(path)

        if not file_path.exists():
            return {"success": False, "error": f"the path {path} does not exist."}

        content = file_path.read_text("utf-8")
        count = content.count(old_content)

        if count == 0:
            return {"success": False, "error": "old_content not found in the file"}

        if count > 1:
            return {"success": False, "error": "old_content is ambiguous, it was found {count} number of times"}

        updated_content = content.replace(old_content, new_content)
        file_path.write_text(updated_content, encoding="utf-8")

        return {"success": True, "error": None}

    except Exception as e:
        return {"success": False, "error": str(e)}
