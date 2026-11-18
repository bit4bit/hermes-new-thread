"""open_thread tool and /thread command."""
import json
import logging
import time
import uuid

logger = logging.getLogger(__name__)

PLUGIN_ID = "new-thread"
MAX_PROMPT_CHARS = 20000
NOTE = ("Hermes Desktop opens the new thread and submits the prompt; "
        "nothing happens if no Desktop window is connected.")
USAGE = "Usage: /thread [--pin] <prompt>"


def broadcast_plugin_event(*args, **kwargs):
    # Imported lazily so the plugin loads in processes without the gateway.
    from hermes_cli.plugin_events import broadcast_plugin_event as _broadcast
    return _broadcast(*args, **kwargs)


def _emit(prompt, pinned, title, origin):
    payload = {
        "request_id": uuid.uuid4().hex,
        "prompt": prompt,
        "pinned": bool(pinned),
        "title": title or "",
        "origin_session_id": origin or "",
        "created_at": time.time(),
    }
    broadcast_plugin_event(PLUGIN_ID, "open", payload)
    return payload


def open_thread(args: dict, **kwargs) -> str:
    try:
        prompt = (args.get("prompt") or "").strip()
        if not prompt:
            return json.dumps({"success": False, "error": "prompt is required"})
        if len(prompt) > MAX_PROMPT_CHARS:
            return json.dumps({"success": False,
                               "error": f"prompt too long ({len(prompt)} > {MAX_PROMPT_CHARS} chars)"})
        origin = kwargs.get("session_id") or kwargs.get("task_id") or ""
        payload = _emit(prompt, args.get("pinned", False), str(args.get("title") or "")[:120], origin)
        return json.dumps({"success": True, "request_id": payload["request_id"],
                           "pinned": payload["pinned"], "note": NOTE})
    except Exception as exc:
        logger.warning("open_thread failed", exc_info=True)
        return json.dumps({"success": False, "error": str(exc)})


def parse_thread_args(raw_args: str):
    """Return (pinned, prompt) from '[--pin|-p] <prompt>'."""
    text = (raw_args or "").strip()
    pinned = False
    head, _, rest = text.partition(" ")
    if head in ("--pin", "-p"):
        pinned, text = True, rest.strip()
    return pinned, text


def thread_command(raw_args: str, session_id: str = "", **_ignored) -> str:
    pinned, prompt = parse_thread_args(raw_args)
    if not prompt:
        return USAGE
    if len(prompt) > MAX_PROMPT_CHARS:
        return f"Prompt too long ({len(prompt)} > {MAX_PROMPT_CHARS} chars)."
    try:
        _emit(prompt, pinned, "", session_id)
    except Exception as exc:
        logger.warning("/thread failed", exc_info=True)
        return f"Could not open thread: {exc}"
    return "Opening a new pinned thread in Hermes Desktop..." if pinned else "Opening a new thread in Hermes Desktop..."
