from pathlib import Path

root = Path(__file__).resolve().parent.parent

def read_file(relative_path: str) -> dict:

    try:
        clean_path = relative_path.lstrip("/\\")
        file_path = (clean_path/relative_path).resolve()
        
        if not file_path.is_relative_to(root.resolve):
            return {"success": False, "error": f"access denied {relative_path} is outside the working directory"}

        if not file_path.exists():
            return {"success": False, "content": None, "error": f"file {file_path} does not exist"}

        if not file_path.is_file():
            return {"success": False, "content": None, "error": f"file {file_path} is not readable"}

        content = file_path.read_text(encoding="utf-8")
        return {"success": True, "content": content, "error": None}

    except UnicodeDecodeError:
        return {"success": False, "content": None, "error": f"file {file_path} is not in utf-8 format"}

    except Exception as e:
        return {"success": False, "content": None, "error": str(e)}

    