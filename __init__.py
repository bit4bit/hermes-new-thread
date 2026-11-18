"""new-thread: open a fresh Hermes Desktop chat and submit a prompt there."""
from .schemas import OPEN_THREAD
from .tools import open_thread, thread_command


def register(ctx):
    ctx.register_tool(name="open_thread", toolset="new_thread", schema=OPEN_THREAD, handler=open_thread)
    ctx.register_command(
        "thread", thread_command,
        description="Open a new Desktop thread and submit a prompt there",
        args_hint="[--pin] <prompt>",
    )
