"""Tool schema for open_thread."""

OPEN_THREAD = {
    "name": "open_thread",
    "description": (
        "Open a NEW chat thread (session) in Hermes Desktop and submit a prompt there so the work "
        "continues in the new thread. Use when the user asks to continue or move work to a new "
        "thread, session or chat. The prompt runs in a fresh session with NO access to this "
        "conversation's history, so it must be fully self-contained: the goal, relevant context, "
        "decisions made, file paths, and concrete next steps. Only set pinned=true when the user "
        "asked for the thread to be pinned."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Self-contained prompt submitted in the new thread.",
            },
            "pinned": {
                "type": "boolean",
                "description": "Pin the new thread in the sidebar. Only when the user asked.",
                "default": False,
            },
            "title": {
                "type": "string",
                "description": "Short label for logs/toast only.",
            },
        },
        "required": ["prompt"],
    },
}
