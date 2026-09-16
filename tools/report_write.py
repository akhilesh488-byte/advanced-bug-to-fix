from pathlib import Path
from datetime import datetime
import json


def report_write(data: dict, file_name: str, format: str = "json") -> dict:

    try:
        root = Path(__file__).resolve().parent.parent
        report_path = root/"report"
        report_path.mkdir(parents = True, exist_ok = True)

        if format == "json":
            path = Path(f"{report_path}/{file_name}.json")

            if path.exists():
                return {"success": False, "relative_path": None, "error": f"file named {file_name}.json already exists"}
            
            with open(path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)

        elif format == "markdown":
            path = Path(f"{report_path}/{file_name}.md")
            if path.exists():
                return {"success": False, "relative_path": None, "error": f"file named {file_name}.md already exists"}
                        
            content = dict_to_markdown(data)
            with open(path, "w", encoding="utf-8") as file:
                file.write(content)

        else:
            return {"success": False, "relative_path": None, "error": f"unsupported format '{format}' - use json or markdown"}

        return {"success": True, "relative_path": str(path.relative_to(root)), "error": None}

    except Exception as e:
        return {"success": False, "relative_path": None, "error": str(e)}

def dict_to_markdown(data: dict) -> str:

    lines = [f"# {data.get('title', 'Bug Fix Report')}", ""]
    lines.append(f"*Generated: {data.get('timestamp', datetime.now().isoformat())}*")
    lines.append("")

    for key, value in data.items():
        if key in ("title", "timestamp"):
            continue
        heading = key.replace("_", " ").title()
        lines.append(f"## {heading}")
        lines.append(str(value))
        lines.append("")

    return "\n".join(lines)
