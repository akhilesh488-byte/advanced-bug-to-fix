from pathlib import Path

root = Path(__file__).resolve().parent.parent

def submit_context(data: dict, format: str = "json"):

    return {"data": data, "format": format}


