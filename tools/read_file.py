from pathlib import Path

def read_file(file_path: str) -> dict:

    try:
        path = Path(file_path)

        if not path.exists():
            return {"success": False, "content": None, "error": f"file {file_path} does not exist"}

        if not path.is_file():
            return {"success": False, "content": None, "error": f"file {file_path} is not readable"}

        content = path.read_text(encoding="utf-8")
        return {"success": True, "content": content, "error": None}

    except UnicodeDecodeError:
        return {"success": False, "content": None, "error": f"file {path} is not in utf-8 format"}

    except Exception as e:
        return {"success": False, "content": None, "error": str(e)}

    