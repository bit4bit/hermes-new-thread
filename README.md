[Jovany Digital 🤖]

# new-thread

Hermes plugin (agent half + Desktop half) that continues work in a fresh chat. From the current
thread it opens a NEW session in Hermes Desktop, optionally pins it in the sidebar, and submits a
prompt there.

## Install

```sh
hermes plugins install bit4bit/hermes-new-thread --enable
```

Or from Hermes Desktop: Capabilities -> Plugins -> Install from Git, `bit4bit/hermes-new-thread`.

Then restart Hermes Desktop and make sure the plugin's Desktop half is on (Capabilities -> Plugins).
Check it loaded: press Cmd+K and look for "New thread from draft".

For development, clone it and link it once (re-running `ln -s` on an existing link creates a
self-referencing symlink inside the repo):

```sh
git clone git@github.com:bit4bit/hermes-new-thread.git
ln -s "$PWD/hermes-new-thread" ~/.hermes/plugins/new-thread
hermes plugins enable new-thread
```

## Usage

- Slash command: `/thread [--pin] <prompt>` (`-p` also works). Without a prompt it prints usage.
- Agent tool: `open_thread(prompt, pinned=false, title=None)`. Ask the agent to "continue this in a
  new thread" (add "and pin it" to pin). The agent writes a self-contained prompt.
- Command palette: "New thread from draft" and "New pinned thread from draft" take the text in the
  composer, clear it, and open it in a new thread. No backend involved.

## How it works

The agent half broadcasts `plugin.new-thread.open` to connected Desktop windows. The Desktop half
dedupes by `request_id`, ignores events older than 2 minutes, lets one window claim the request,
calls `host.newChat()`, retries `host.composer.submit('new', prompt)` for up to 8 s, and pins the new
session when requested.

## Limitations

- Needs Hermes Desktop connected. With no Desktop window the broadcast is a no-op.
- The new thread has no history of the old one; the prompt must carry all context.
- If the prompt can't be submitted, it is copied to the clipboard instead.
- Prompts are capped at 20000 characters.

## Tests

```sh
PYTHONPATH=$HOME/.hermes/hermes-agent uvx --python $HOME/.hermes/hermes-agent/venv/bin/python --with pytest pytest tests -q -p no:cacheprovider
node --check desktop/plugin.js
```

## License

MIT
