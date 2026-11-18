import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location(
        "new_thread_plugin", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["new_thread_plugin"] = mod
    spec.loader.exec_module(mod)
    return mod


plugin = _load()
tools = sys.modules["new_thread_plugin.tools"]


class FakeCtx:
    def __init__(self):
        self.tools, self.commands = {}, {}

    def register_tool(self, name, toolset, schema, handler, **kw):
        self.tools[name] = (toolset, schema, handler)

    def register_command(self, name, handler, description="", args_hint="", **kw):
        self.commands[name] = (handler, description, args_hint)


def _capture(monkeypatch):
    calls = []
    monkeypatch.setattr(tools, "broadcast_plugin_event", lambda *a, **k: calls.append(a))
    return calls


def test_register():
    ctx = FakeCtx()
    plugin.register(ctx)
    toolset, schema, _ = ctx.tools["open_thread"]
    assert toolset == "new_thread"
    assert schema["parameters"]["required"] == ["prompt"]
    assert ctx.commands["thread"][2] == "[--pin] <prompt>"


def test_tool_broadcasts(monkeypatch):
    calls = _capture(monkeypatch)
    out = json.loads(tools.open_thread({"prompt": "do x", "pinned": True, "title": "T"}, session_id="s1"))
    assert out["success"] and out["pinned"] is True
    plugin_id, event, payload = calls[0]
    assert (plugin_id, event) == ("new-thread", "open")
    assert payload["prompt"] == "do x" and payload["pinned"] is True and payload["title"] == "T"
    assert payload["origin_session_id"] == "s1"
    assert payload["request_id"] == out["request_id"] and len(payload["request_id"]) == 32
    assert isinstance(payload["created_at"], float)


def test_tool_validation(monkeypatch):
    calls = _capture(monkeypatch)
    assert json.loads(tools.open_thread({"prompt": "  "}))["success"] is False
    assert json.loads(tools.open_thread({"prompt": "x" * 20001}))["success"] is False
    assert not calls


def test_tool_failure(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("nope")
    monkeypatch.setattr(tools, "broadcast_plugin_event", boom)
    out = json.loads(tools.open_thread({"prompt": "hi"}))
    assert out == {"success": False, "error": "nope"}


def test_command_parsing(monkeypatch):
    calls = _capture(monkeypatch)
    assert tools.thread_command("") .startswith("Usage")
    assert tools.thread_command("--pin").startswith("Usage")
    assert not calls
    tools.thread_command("--pin write tests", session_id="abc")
    tools.thread_command("-p short flag")
    tools.thread_command("plain prompt --pin")
    p = [c[2] for c in calls]
    assert (p[0]["pinned"], p[0]["prompt"], p[0]["origin_session_id"]) == (True, "write tests", "abc")
    assert (p[1]["pinned"], p[1]["prompt"]) == (True, "short flag")
    assert (p[2]["pinned"], p[2]["prompt"]) == (False, "plain prompt --pin")
