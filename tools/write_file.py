from pathlib import Path

def write_file(path: str, new_content: str, overwrite: bool = False) -> dict:

    try:
        file_path = Path(path)

        if file_path.exists() and not overwrite:
            return {"success": False, "error": f"path {path} already exists and to replace it pass overwrite = True"}

        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(new_content, encoding="utf-8")

        return {"success": True, "error": None}

    except Exception as e:
        return {"success": False, "error": str(e)}
