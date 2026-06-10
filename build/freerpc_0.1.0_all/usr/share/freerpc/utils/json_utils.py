import json


def format_json(text):
    try:
        obj = json.loads(text)
        return json.dumps(obj, indent=2)
    except Exception:
        return text
