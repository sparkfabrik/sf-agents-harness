import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Prompt, Reply } from '../types'

const PANE = 'prompts'
const COLORS_PANE = 'prompt-colors'
// The theme's named colors (ThemeKey) the highlightColor option offers; they
// follow the theme the person picked.
const THEME_COLORS = ["text","inactive","subtle","suggestion","remember","success","error","warning","merged","claude","permission","planMode","autoAccept","promptBorder","bashBorder","ide"] as const
// One store key per summarized prompt, so two sessions never overwrite each
// other's; the oldest are dropped past MAX_SUMMARIES.
const SUMMARY_PREFIX = 'summary:'
const LEGACY_SUMMARIES_KEY = 'summaries'
const MAX_SUMMARIES = 2000
const SUMMARIES_PER_PASS = 40
const MAX_PROMPT_LINES = 8
const MAX_REPLY_LINES = 2
const GUTTER = 5
// What the list keeps of each text: enough for its rows at any pane width.
const MAX_PROMPT_CHARS = 4000
const MAX_REPLY_CHARS = 1000
const PAGE = 4096
// The tags the engine wraps a user row in (slash-command echoes, shell mode,
// notifications, reminders): such a row is not a prompt.
const WRAPPER = /^<(command-name|command-message|command-args|local-command-stdout|local-command-stderr|local-command-caveat|bash-input|bash-stdout|bash-stderr|task-notification|system-reminder|user-prompt-submit-hook|tools-used-before-summary|stored_memory|artifact-content-authored-by-others)[\s>]/

const prompts = atom({ plugin: 'prompt-navigator', key: 'prompts' } as const, [], {
  shape: 'prompts-3',
})
const lastId = atom({ plugin: 'prompt-navigator', key: 'lastId' } as const, '')
const offsetAtom = atom({ plugin: 'prompt-navigator', key: 'offset' } as const, -1)
const showReplies = atom({ plugin: 'prompt-navigator', key: 'showReplies' } as const, false)
// The topmost row on screen, written only to redraw the pane when it changes.
const topAtom = atom({ plugin: 'prompt-navigator', key: 'top' } as const, '')

type Row = {
  role: string
  text: string
  toolResults?: unknown[]
  toolUses?: readonly { tool_use_id: string }[]
  uuid?: string
}
type Exchange = { id: string; prompt: string; before: string; after: string }

// One entry of the list as drawn: a prompt with its decorations, or a reply.
type Item = {
  key: string
  id: string
  kind: 'prompt' | 'reply'
  number?: number
  lines: string[]
  notes: string[]
}

// What the last drawing measured, read by the scroll hook; a reload resets it,
// and the next drawing measures again.
let layout = { maxOffset: 0, rows: 20 }
let isSummarizing = false
// Set while the pane is drawn, cleared when it closes: the transcript's rows
// redraw the pane only while it is open.
let isPaneOpen = false

// What the reads so far built, so each refresh reads only the rows after the
// last one seen. Empty after a reload, which reads the session again.
type Feed = { seen: string; count: number; before: string; list: Prompt[]; exchanges: Exchange[] }
const emptyFeed = (): Feed => ({ seen: '', count: 0, before: '', list: [], exchanges: [] })
let feed = emptyFeed()

// Where the conversation is scrolled: the rows the transcript reports on screen,
// each row's place in the conversation, and the pane entry each row belongs to.
// Module values: the drawing of a message cannot write $.state, and a reload
// rebuilds them at the next refresh and scroll.
const visible = new Set<string>()
let orderOf = new Map<string, number>()
let ownerOf = new Map<string, string>()
let current = ''

// A drawn message's id is the stored row's uuid with its last group zeroed
// (`ab187cfd-…-000000000000`): match on the groups before it.
const rowKey = (id: string) => id.slice(0, 23)

type Shown = { first: number; last: number; of: number } | null | undefined

// The key of the topmost row on screen, in conversation order.
function topVisible(): string {
  let top = ''
  let topAt = Infinity
  for (const id of visible) {
    const at = orderOf.get(id)
    if (at !== undefined && at < topAt) (top = id), (topAt = at)
  }
  return top
}

// Records whether a row is on screen. Rows report only as they reach the
// viewport's edges, so a row cut at the top (or bottom) edge also clears every
// row before (or after) it that scrolled away unreported. The bookkeeping runs
// with the pane closed too, so it is right when the pane opens; a changed top
// row redraws only the open pane, through a state write after the draw (a
// draw cannot write state).
function track($: EngineInterface, id: string, onScreen: Shown) {
  if (onScreen === undefined) return
  const before = topVisible()
  if (onScreen === null) visible.delete(id)
  else {
    visible.add(id)
    const at = orderOf.get(id)
    if (at !== undefined) {
      for (const other of [...visible]) {
        const otherAt = orderOf.get(other)
        if (otherAt === undefined) visible.delete(other)
        else if (onScreen.first > 0 && otherAt < at) visible.delete(other)
        else if (onScreen.last < onScreen.of - 1 && otherAt > at) visible.delete(other)
      }
    }
  }
  const top = topVisible()
  if (top !== before && isPaneOpen) $.clock.after(0, () => void update($, topAtom, () => top).catch(() => undefined))
}

// The entry for the topmost message on screen: a reply when replies are shown
// and it is one, else the prompt it belongs to.
function currentEntry(withReplies: boolean, replyIds: Set<string>): string {
  const top = topVisible()
  if (!top) return ''
  if (withReplies) {
    const reply = [...replyIds].find(id => rowKey(id) === top)
    if (reply) return reply
  }
  return ownerOf.get(top) ?? ''
}

// A user row is a prompt when it has text, carries no tool results and is not
// an engine wrapper (slash-command echoes, notifications, reminders).
const isPrompt = (m: Row) =>
  m.role === 'user' &&
  !(m.toolResults && m.toolResults.length > 0) &&
  m.text.trim() !== '' &&
  !WRAPPER.test(m.text.trimStart())

const flat = (text: string) => text.replace(/\s+/g, ' ').trim()
const isShort = (text: string) => flat(text).length <= 30
const cut = (text: string, width: number) =>
  text.length > width ? text.slice(0, Math.max(1, width - 1)) + '…' : text

// The last question of a reply, else its last sentence: what a "yes" answered.
function lastSentence(text: string): string {
  const sentences = flat(text.replace(/```[\s\S]*?```/g, ' '))
    .split(/(?<=[.?!])\s+/)
    .filter(s => s.length > 3)
  const question = [...sentences].reverse().find(s => s.endsWith('?'))
  return question ?? sentences.at(-1) ?? ''
}

// Hard-wraps text into rows of at most width cells, so the drawing's height is
// known: at most max rows, the last cut with an ellipsis.
function wrap(text: string, width: number, max: number): string[] {
  const out: string[] = []
  // A row holds at most width + 1 characters: this much text fills max + 1 rows.
  for (const para of text.slice(0, (width + 1) * (max + 1)).replace(/\r/g, '').split('\n')) {
    let line = ''
    for (const word of para.split(/\s+/).filter(Boolean)) {
      let w = word
      while (w.length > width) {
        if (line) out.push(line), (line = '')
        out.push(w.slice(0, width))
        w = w.slice(width)
      }
      if (!line) line = w
      else if (line.length + 1 + w.length <= width) line += ' ' + w
      else out.push(line), (line = w)
    }
    if (line) out.push(line)
  }
  if (out.length > max) {
    const kept = out.slice(0, max)
    kept[max - 1] = cut(kept[max - 1] + ' …', width)
    return kept
  }
  return out.length ? out : ['']
}

function itemsOf(list: readonly Prompt[], withReplies: boolean, width: number): Item[] {
  const room = Math.max(8, width - GUTTER)
  const items: Item[] = []
  list.forEach((p, i) => {
    const notes = [
      ...(p.context ? [cut('← ' + flat(p.context), room)] : []),
      ...(p.summary ? [cut('✦ ' + p.summary, room)] : []),
    ]
    items.push({ key: p.id, id: p.id, kind: 'prompt', number: i + 1, lines: wrap(p.text, room, MAX_PROMPT_LINES), notes })
    if (withReplies)
      p.replies.forEach((r: Reply) =>
        items.push({ key: 'r-' + r.id, id: r.id, kind: 'reply', lines: wrap('● ' + flat(r.text.slice(0, (room + 1) * (MAX_REPLY_LINES + 1))), room, MAX_REPLY_LINES), notes: [] }),
      )
  })
  return items
}

const heightOf = (item: Item) => item.lines.length + item.notes.length

// The first offset whose items fill the window to the end of the list.
function maxOffsetOf(items: Item[], rows: number): number {
  let used = 0
  for (let i = items.length - 1; i >= 0; i--) {
    used += heightOf(items[i]!)
    if (used > rows) return i + 1
  }
  return 0
}

// Reads the rows after the last one seen (the whole session after a reload,
// or when that row is gone, as after a compaction) and adds their prompts.
async function refresh($: EngineInterface, wantsSummaries: boolean): Promise<Exchange[]> {
  let rows: Row[] = []
  for (;;) {
    const page = (await $.session.messages(feed.seen ? { after: feed.seen } : { last: PAGE })) as Row[] | { deny: string }
    if ('deny' in page) {
      if (!feed.seen) return feed.exchanges
      feed = emptyFeed()
      orderOf = new Map()
      ownerOf = new Map()
      rows = []
      continue
    }
    rows = rows.concat(page)
    const last = page.at(-1)?.uuid
    if (last) feed.seen = last
    if (page.length < PAGE || !last) break
  }
  if (rows.length === 0 && feed.list.length > 0) return feed.exchanges
  for (const m of rows) add(m)
  // Cached summaries stay in the store while summaries are off, but are shown
  // only while they are on.
  if (wantsSummaries) {
    await migrateSummaries($)
    for (const p of feed.list)
      if (!p.summary) {
        const cached = await $.store.get(SUMMARY_PREFIX + p.id).catch(() => undefined)
        if (typeof cached === 'string') p.summary = cached
      }
  }
  await update($, prompts, () => feed.list.slice())
  if (feed.seen) await update($, lastId, () => feed.seen)
  return feed.exchanges
}

// Adds one row to the feed: a prompt opens an entry, an assistant message is
// a reply of the open one. Each row's place in the conversation and the entry
// it belongs to are kept for the scroll tracking.
function add(m: Row) {
  const at = feed.count++
  const list = feed.list
  if (m.uuid) orderOf.set(rowKey(m.uuid), at)
  if (m.uuid && list.length > 0) ownerOf.set(rowKey(m.uuid), isPrompt(m) ? m.uuid : list.at(-1)!.id)
  // A tool call's row is drawn under its tool_use_id, just after its message.
  if (list.length > 0)
    for (const use of m.toolUses ?? []) {
      orderOf.set(use.tool_use_id, at + 0.5)
      ownerOf.set(use.tool_use_id, list.at(-1)!.id)
    }
  if (isPrompt(m) && m.uuid) {
    ownerOf.set(rowKey(m.uuid), m.uuid)
    feed.exchanges.push({ id: m.uuid, prompt: m.text.slice(0, 2000), before: feed.before.slice(-800), after: '' })
    list.push({
      id: m.uuid,
      text: m.text.slice(0, MAX_PROMPT_CHARS),
      replies: [],
      ...(isShort(m.text) && feed.before ? { context: cut(lastSentence(feed.before.slice(-4000)), 300) } : {}),
    })
  } else if (m.role === 'assistant' && m.text.trim() !== '') {
    feed.before = m.text.slice(-4000)
    const open = feed.exchanges.at(-1)
    if (open && open.after.length < 2500) open.after = (open.after + (open.after ? '\n' : '') + m.text).slice(0, 2500)
    if (m.uuid) list.at(-1)?.replies.push({ id: m.uuid, text: m.text.slice(0, MAX_REPLY_CHARS) })
  }
}

// Moves summaries cached by an older version, all under one key, to a key each.
async function migrateSummaries($: EngineInterface) {
  const legacy = (await $.store.get(LEGACY_SUMMARIES_KEY).catch(() => undefined)) as Record<string, string> | undefined
  if (!legacy) return
  for (const [id, summary] of Object.entries(legacy)) await $.store.set(SUMMARY_PREFIX + id, summary)
  await $.store.delete(LEGACY_SUMMARIES_KEY)
}

// Drops the oldest summaries past MAX_SUMMARIES; the store keeps insertion order.
async function pruneSummaries($: EngineInterface) {
  const keys = (await $.store.keys()).filter(key => key.startsWith(SUMMARY_PREFIX))
  for (const key of keys.slice(0, Math.max(0, keys.length - MAX_SUMMARIES))) await $.store.delete(key)
}

// Summarizes the newest finished exchanges that have no summary, one Haiku
// call apiece, cached in the store across sessions so an exchange is never
// summarized twice.
async function summarize($: EngineInterface, exchanges: Exchange[]) {
  if (isSummarizing) return
  isSummarizing = true
  try {
    const done = new Set(feed.list.filter(p => p.summary).map(p => p.id))
    const todo = exchanges.filter(x => x.after !== '' && !done.has(x.id)).slice(-SUMMARIES_PER_PASS)
    for (const x of todo) {
      // Another session may have summarized it since the list was read.
      const cached = await $.store.get(SUMMARY_PREFIX + x.id)
      const summary = typeof cached === 'string' ? cached : await summaryOf($, x)
      if (!summary) continue
      if (typeof cached !== 'string') await $.store.set(SUMMARY_PREFIX + x.id, summary)
      const entry = feed.list.find(p => p.id === x.id)
      if (entry) entry.summary = summary
      await update($, prompts, list => list.map(p => (p.id === x.id ? { ...p, summary } : p)))
    }
    if (todo.length > 0) await pruneSummaries($)
  } finally {
    isSummarizing = false
  }
}

async function summaryOf($: EngineInterface, x: Exchange): Promise<string> {
  const reply = await $.model.complete({
    model: 'haiku',
    effort: 'low',
    maxTokens: 300,
    timeoutMs: 20000,
    system:
      'You summarize one exchange of a coding session for a navigation list. ' +
      'Say what was asked and done, at most 12 words, no quotes, no trailing period.',
    prompt:
      '<assistant_before>' + x.before + '</assistant_before>\n' +
      '<user_prompt>' + x.prompt + '</user_prompt>\n' +
      '<assistant_after>' + x.after + '</assistant_after>',
  })
  if (!reply.isAnswered) return ''
  return cut(flat(reply.text.split('\n')[0] ?? '').replace(/^["'*]+|["'*.]+$/g, ''), 120)
}

async function sync($: EngineInterface, wantsSummaries: boolean) {
  const exchanges = await refresh($, wantsSummaries).catch(() => [] as Exchange[])
  if (wantsSummaries) void summarize($, exchanges).catch(() => undefined)
}

async function jumpTo($: EngineInterface, id: string, block: 'start' | 'end') {
  let moved = await $.ui.scroll({ to: { requestId: id }, block })
  // The drawn row may carry the id with its last group zeroed (see rowKey).
  if ('deny' in moved) moved = await $.ui.scroll({ to: { requestId: rowKey(id) + '-000000000000' }, block })
  if ('deny' in moved) $.ui.toast("Can't jump: " + moved.deny)
}

async function jumpToBottom($: EngineInterface) {
  await update($, offsetAtom, () => -1)
  const id = await read($, lastId)
  if (id) await jumpTo($, id, 'end')
}

async function toggleColors($: EngineInterface) {
  const panes = await $.ui.panes()
  if (panes.some(pane => pane.id === COLORS_PANE && pane.isPlaced)) {
    await $.ui.close({ id: COLORS_PANE })
    return { text: 'Colors pane closed.' }
  }
  await $.ui.open({ id: COLORS_PANE, title: 'Theme colors' })
  return { text: 'Colors pane opened. Pick one as Highlight color in /config.' }
}

export const register: Register = (on, options) => {
  const wantsSummaries = options.haikuSummaries === true
  const highlight = typeof options.highlightColor === 'string' ? options.highlightColor : 'suggestion'

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'prompts',
      description: 'Toggle a pane listing your prompts; press one to jump to it',
      argumentHint: '[colors]',
    })
    const ran = await next(e)
    // A settings change reloads the mod and runs this again: start the
    // summaries now instead of at the end of the next turn.
    if (wantsSummaries) void sync($, true).catch(() => undefined)
    else await refresh($, wantsSummaries).catch(() => undefined)
    return ran
  })

  on('command.run', { command: 'prompts' }, async ($, e) => {
    if (e.args.trim() === 'colors') return toggleColors($)
    const panes = await $.ui.panes()
    if (panes.some(pane => pane.id === PANE && pane.isPlaced)) {
      await $.ui.close({ id: PANE })
      return { text: 'Prompts pane closed.' }
    }
    await update($, offsetAtom, () => -1)
    await sync($, wantsSummaries)
    await $.ui.open({ id: PANE, title: 'Prompts' })
    return { text: 'Prompts pane opened.' }
  })

  on('ui.close', async ($, e, next) => {
    if (e.id === PANE) isPaneOpen = false
    return next(e)
  })

  on('ui.render', { component: 'Pane', requestId: COLORS_PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    return (
      <Box flexDirection="column">
        {THEME_COLORS.map(name => (
          <Box key={'c-' + name} flexDirection="row">
            <Text color={name}>{'██ ' + name.padEnd(18) + 'sample text '}</Text>
            <Text backgroundColor={name}>{' background '}</Text>
            {name === highlight ? <Text dimColor>{'  ← current'}</Text> : ''}
          </Box>
        ))}
      </Box>
    )
  })

  on('prompt.submit', async ($, e, next) => {
    const ran = await next(e)
    await refresh($, wantsSummaries).catch(() => undefined)
    return ran
  })

  on('turn.complete', async ($, e, next) => {
    const ran = await next(e)
    if (e.agentId === undefined) await sync($, wantsSummaries)
    return ran
  })

  // The conversation's messages say which of their lines are on screen as they
  // are drawn and scrolled; the pane colors the entry nearest the top.
  on('ui.render', { component: 'UserMessage' }, async ($, e, next) => {
    track($, rowKey(e.requestId), e.props.onScreen)
    return next(e)
  })
  on('ui.render', { component: 'AssistantMessage' }, async ($, e, next) => {
    track($, rowKey(e.requestId), e.props.onScreen)
    return next(e)
  })
  on('ui.render', { component: 'ToolUse' }, async ($, e, next) => {
    track($, e.requestId, e.props.onScreen)
    return next(e)
  })

  // The pane draws its own window so the header and the bottom button stay put:
  // the wheel and the scroll keys move it an item at a time, a page by a page.
  on('ui.scroll', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { maxOffset, rows } = layout
    await update($, offsetAtom, now => {
      const from = now < 0 ? maxOffset : now
      const step = Math.abs(e.by) > rows ? Math.sign(e.by) * 1e6 : Math.abs(e.by) >= rows - 2 ? Math.sign(e.by) * Math.max(1, rows / 3) : e.by
      const to = Math.round(from + step)
      return to >= maxOffset ? -1 : Math.max(0, to)
    })
    return {}
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Button } = $.ui.resolve(e)
    isPaneOpen = true
    // Read so that a changed top row redraws the pane; the module's own
    // tracking says which row it is.
    await read($, topAtom)
    const list = await read($, prompts)
    const withReplies = await read($, showReplies)
    const offset = await read($, offsetAtom)
    const width = Math.max(16, e.props.bodyColumns ?? 40)
    const rows = Math.max(3, (e.props.scroll?.bodyRows ?? 24) - 2)

    const items = itemsOf(list, withReplies, width)
    const maxOffset = maxOffsetOf(items, rows)
    layout = { maxOffset, rows }
    const first = offset < 0 ? maxOffset : Math.min(offset, maxOffset)
    const shown: Item[] = []
    let used = 0
    for (const item of items.slice(first)) {
      if (used + heightOf(item) > rows && shown.length > 0) break
      shown.push(item)
      used += heightOf(item)
    }
    const replyIds = new Set(list.flatMap(p => p.replies.map(r => r.id)))
    current = currentEntry(withReplies, replyIds)

    return (
      <Box flexDirection="column" height={rows + 2}>
        <Box flexDirection="row" justifyContent={list.length === 0 ? 'space-between' : 'flex-end'}>
          {list.length === 0 && <Text dimColor>No prompts yet.</Text>}
          <Button key="replies" plain dimColor={!withReplies} hotkey="r" onPress={() => update($, showReplies, isOn => !isOn)}>
            {(withReplies ? '◉' : '○') + ' replies (r)'}
          </Button>
        </Box>
        <Box flexDirection="column" flexGrow={1}>
          {shown.map(item => {
            // One Button per row, in a keyed Box: the Box is the hover scope,
            // so the whole entry lights wherever the pointer rests on it.
            const press = () => jumpTo($, item.id, 'start')
            const rows = [
              ...item.lines.map((line, i) => ({
                text: (i === 0 && item.number !== undefined ? String(item.number).padStart(GUTTER - 1) + ' ' : ' '.repeat(GUTTER)) + line,
                isNote: false,
              })),
              ...item.notes.map(note => ({ text: ' '.repeat(GUTTER) + note, isNote: true })),
            ]
            return (
              <Box key={'e-' + item.key} flexDirection="column">
                {rows.map((row, i) => (
                  <Button key={item.key + ':' + i} plain hover={{ inverse: true }} onPress={press}>
                    <Text
                      color={item.id === current && !row.isNote ? highlight : undefined}
                      dimColor={row.isNote || (item.kind === 'reply' && item.id !== current)}
                      bold={!row.isNote && item.kind === 'prompt'}
                    >
                      {row.text}
                    </Text>
                  </Button>
                ))}
              </Box>
            )
          })}
        </Box>
        <Box flexDirection="row" justifyContent="center">
          <Button key="bottom" plain hotkey="b" onPress={() => jumpToBottom($)}>
            ↓ bottom (b)
          </Button>
        </Box>
      </Box>
    )
  })
}
