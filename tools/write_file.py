from pathlib import Path

root = Path(__file__).resolve().parent.parent

def write_file(relative_path: str, new_content: str, overwrite: bool = False) -> dict:

    try:
        file_path = root / relative_path

        if not file_path.is_relative_to(root):
            return {"success": False, "error": f"path {file_path} is out of working directory"}

        if file_path.exists() and not overwrite:
            return {"success": False, "error": f"path {relative_path} already exists and to replace it pass overwrite = True"}

        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(new_content, encoding="utf-8")

        return {"success": True, "error": None}

    except Exception as e:
        return {"success": False, "error": str(e)}
