from typing import Any, Dict


def task_event(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a task event message for websocket broadcast.
    """
    return {"type": "task." + action, "payload": payload}
