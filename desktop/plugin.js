import { host, PALETTE_AREA } from '@hermes/plugin-sdk'

const EVENT = 'plugin.new-thread.open'
const SEEN_KEY = 'seenRequestIds'
const CLAIM_PREFIX = 'claim:'
const MAX_SEEN = 100
const MAX_AGE_MS = 2 * 60 * 1000
const SUBMIT_RETRY_MS = 150
const SUBMIT_TIMEOUT_MS = 8000
const PIN_TIMEOUT_MS = 60000
const UNFOCUSED_CLAIM_DELAY_MS = 300

export default {
  id: 'new-thread',
  name: 'New Thread',

  register(ctx) {
    const seen = new Set(ctx.storage.get(SEEN_KEY, []))
    const windowToken = Math.random().toString(36).slice(2)

    const remember = id => {
      seen.add(id)
      while (seen.size > MAX_SEEN) {
        const oldest = seen.values().next().value
        seen.delete(oldest)
        ctx.storage.remove(CLAIM_PREFIX + oldest)
      }
      ctx.storage.set(SEEN_KEY, [...seen])
    }

    // Every connected window gets the broadcast. ctx.storage is shared across windows of the same
    // origin, so the first window to write its token for a request id wins; unfocused windows wait
    // a beat so the focused one normally takes it.
    const claim = id => {
      const key = CLAIM_PREFIX + id
      if (ctx.storage.get(key, null)) return false
      ctx.storage.set(key, windowToken)
      return ctx.storage.get(key, null) === windowToken
    }

    const fail = prompt => {
      host.notify({ kind: 'warning', message: 'Could not open new thread. The prompt was copied to the clipboard.' })
      void ctx.os.writeClipboard(prompt)
    }

    const submitWithRetry = prompt =>
      new Promise(resolve => {
        const started = Date.now()
        const attempt = () => {
          if (host.composer.submit('new', prompt)) return resolve(true)
          if (Date.now() - started >= SUBMIT_TIMEOUT_MS) return resolve(false)
          ctx.setTimeout(attempt, SUBMIT_RETRY_MS)
        }
        attempt()
      })

    // Resolve with the new stored session id once focus moves off `previous`, or null on timeout.
    const waitForNewSession = previous =>
      new Promise(resolve => {
        const atom = host.state.focusedStoredSessionId
        let done = false
        let unlisten = () => {}
        let cancelTimer = () => {}
        const finish = id => {
          if (done) return
          done = true
          unlisten()
          cancelTimer()
          resolve(id)
        }
        const check = () => {
          const id = atom.get()
          if (id && id !== previous) finish(id)
        }
        unlisten = atom.listen(check)
        ctx.onDispose(unlisten)
        cancelTimer = ctx.setTimeout(() => finish(null), PIN_TIMEOUT_MS)
        check()
      })

    const openThread = async (prompt, pinned) => {
      const previous = host.state.focusedStoredSessionId.get()
      host.newChat()
      const ok = await submitWithRetry(prompt)
      if (!ok) return fail(prompt)

      if (pinned) {
        const id = await waitForNewSession(previous)
        if (id) host.sessions.pin(id, true)
        else host.notify({ kind: 'warning', message: 'New thread opened, but it could not be pinned.' })
      }
      host.notify({ kind: 'info', message: pinned ? 'Opened new thread (pinned)' : 'Opened new thread' })
    }

    const handle = payload => {
      if (!payload || typeof payload.prompt !== 'string' || !payload.prompt.trim()) return
      const id = typeof payload.request_id === 'string' ? payload.request_id : ''
      if (!id || seen.has(id)) return
      const createdMs = Number(payload.created_at) * 1000
      if (Number.isFinite(createdMs) && Date.now() - createdMs > MAX_AGE_MS) return

      const run = () => {
        if (seen.has(id) || !claim(id)) return
        remember(id)
        void openThread(payload.prompt, payload.pinned === true)
      }
      if (document.hasFocus()) run()
      else ctx.setTimeout(run, UNFOCUSED_CLAIM_DELAY_MS)
    }

    ctx.onEvent(EVENT, evt => handle(evt.payload))

    const fromDraft = pinned => async () => {
      const draft = await host.composer.getDraft(null)
      if (!draft || !draft.trim()) {
        host.notify({ kind: 'info', message: 'Composer draft is empty' })
        return
      }
      await host.composer.setDraft(null, '')
      void openThread(draft, pinned)
    }

    ctx.registerMany([
      {
        id: 'from-draft',
        area: PALETTE_AREA,
        data: {
          id: 'new-thread.from-draft',
          label: 'New thread from draft',
          keywords: ['new', 'thread', 'chat', 'draft'],
          run: fromDraft(false)
        }
      },
      {
        id: 'from-draft-pinned',
        area: PALETTE_AREA,
        data: {
          id: 'new-thread.from-draft-pinned',
          label: 'New pinned thread from draft',
          keywords: ['new', 'thread', 'chat', 'draft', 'pin', 'pinned'],
          run: fromDraft(true)
        }
      }
    ])
  }
}
