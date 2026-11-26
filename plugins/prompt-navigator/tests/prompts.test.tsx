import type { ModelUsage, SessionMessage, TurnCompleteInput } from 'claude-code'
import { expect, mock, test } from 'claude-code/testing'
import type { TestBody } from 'claude-code/testing'

const pane = (bodyRows: number) =>
  ({
    plugin: 'prompt-navigator',
    component: 'Pane',
    requestId: 'prompts',
    props: {
      title: 'Prompts',
      isFocused: false,
      bodyColumns: 60,
      placement: 'dock',
      scroll: { offset: 0, bodyRows },
      view: {},
    },
  }) as const

const TURN = { answer: '', durationMs: 1, isAborted: false, turnId: 't1', reason: 'answer' } as TurnCompleteInput
const USAGE = { input_tokens: 100, output_tokens: 8 } as unknown as ModelUsage

const ROWS: SessionMessage[] = [
  { role: 'user', text: 'Find me a prompt history plugin', toolUses: [], uuid: '11111111-1111-4111-8111-111111111111' },
  { role: 'assistant', text: 'None exists. Want me to build one?', toolUses: [], uuid: '22222222-2222-4222-8222-222222222222' },
  { role: 'user', text: '', toolUses: [], toolResults: [{ tool_use_id: 't', text: 'x', isError: false }] as never, uuid: '33333333-3333-4333-8333-333333333333' },
  { role: 'user', text: '<command-name>/model</command-name>', toolUses: [], uuid: '44444444-4444-4444-8444-444444444444' },
  { role: 'user', text: 'yes please', toolUses: [], uuid: '55555555-5555-4555-8555-555555555555' },
  { role: 'assistant', text: 'Built the prompt-navigator mod.', toolUses: [], uuid: '66666666-6666-4666-8666-666666666666' },
]

const start = async ($: Parameters<TestBody>[0], on: Parameters<TestBody>[1], rows = ROWS) => {
  on('command.register', (_, e) => ({ value: { command: e.name } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.messages', () => ({ value: rows }))
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
}

test('lists prompts with what a short reply answered; replies toggle', async ($, on) => {
  await start($, on)
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...pane(20), surface })
    const found = async () => ({
      first: Boolean(await ui.find({ text: /Find me a prompt history plugin/ })),
      context: Boolean(await ui.find({ text: /← Want me to build one\?/ })),
      wrapper: Boolean(await ui.find({ text: /command-name/ })),
      reply: Boolean(await ui.find({ key: 'e-r-66666666-6666-4666-8666-666666666666' })),
      bottom: Boolean(await ui.find({ key: 'bottom' })),
    })
    expect(await found()).toEqual({ first: true, context: true, wrapper: false, reply: false, bottom: true })
    await ui.press({ key: 'replies' })
    expect((await found()).reply).toBe(true)
    await ui.press({ key: 'replies' })
    await ui.unmount()
  }
})

test('a long prompt wraps instead of being cut to one row', async ($, on) => {
  const long = 'word '.repeat(40).trim()
  await start($, on, [{ role: 'user', text: long, toolUses: [], uuid: 'u1' }])
  const ui = await $.ui.mount({ ...pane(20), surface: 'terminal' })
  expect(await ui.find({ key: 'u1:2' })).toBeDefined()
  await ui.unmount()
})

test('the entry of the topmost message on screen is colored', async ($, on) => {
  await start($, on)
  await $.ui.mount({
    plugin: 'prompt-navigator', surface: 'terminal', component: 'AssistantMessage', requestId: '22222222-2222-4222-8222-000000000000',
    props: { text: 'None exists. Want me to build one?', isFirstOfReply: true, onScreen: { first: 0, last: 1, of: 2 } },
  } as never).catch(() => undefined)
  const ui = await $.ui.mount({ ...pane(20), surface: 'terminal' })
  const row = await ui.find({ key: '11111111-1111-4111-8111-111111111111:0' })
  expect(JSON.stringify(row)).toContain('suggestion')
  await ui.unmount()
})

test('a row cut at the top edge clears rows above it that scrolled away', async ($, on) => {
  await start($, on)
  const show = (requestId: string, onScreen: unknown) =>
    $.ui.mount({
      plugin: 'prompt-navigator', surface: 'terminal', component: 'AssistantMessage', requestId,
      props: { text: 'x', isFirstOfReply: true, onScreen },
    } as never).catch(() => undefined)
  await show('22222222-2222-4222-8222-000000000000', { first: 0, last: 1, of: 2 })
  await show('66666666-6666-4666-8666-000000000000', { first: 1, last: 2, of: 3 })
  const ui = await $.ui.mount({ ...pane(20), surface: 'terminal' })
  expect(JSON.stringify(await ui.find({ key: '55555555-5555-4555-8555-555555555555:0' }))).toContain('suggestion')
  expect(JSON.stringify(await ui.find({ key: '11111111-1111-4111-8111-111111111111:0' }))).not.toContain('suggestion')
  await ui.unmount()
})

test('a long list opens at the end and keeps the bottom button in view', async ($, on) => {
  const rows: SessionMessage[] = Array.from({ length: 50 }, (_, i) => ({
    role: 'user', text: 'prompt ' + (i + 1), toolUses: [], uuid: 'u' + (i + 1),
  }))
  await start($, on, rows)
  const ui = await $.ui.mount({ ...pane(12), surface: 'terminal' })
  expect(await ui.find({ key: 'e-u50' })).toBeDefined()
  expect(await ui.find({ key: 'e-u1' })).toBeUndefined()
  expect(await ui.find({ key: 'bottom' })).toBeDefined()
  expect(await ui.find({ text: /prompts/ })).toBeUndefined()
  await ui.unmount()
})

test('a prompt that starts with a tag of its own is listed', async ($, on) => {
  await start($, on, [
    { role: 'user', text: '<Button> does not render', toolUses: [], uuid: 'u1' },
    { role: 'user', text: '<task-notification>done</task-notification>', toolUses: [], uuid: 'u2' },
  ])
  const ui = await $.ui.mount({ ...pane(20), surface: 'terminal' })
  expect(await ui.find({ text: /<Button> does not render/ })).toBeDefined()
  expect(await ui.find({ text: /task-notification/ })).toBeUndefined()
  await ui.unmount()
})

test('a refresh reads only the rows after the last one seen', async ($, on) => {
  const reads: unknown[] = []
  on('command.register', (_, e) => ({ value: { command: e.name } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('session.messages', (_, e) => {
    reads.push(e)
    return { value: 'after' in e && e.after ? [{ role: 'user', text: 'second prompt', toolUses: [], uuid: 'u2' }] : [ROWS[0]!] }
  })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.turn.complete(TURN)
  expect(JSON.stringify(reads.at(-1))).toContain('11111111-1111-4111-8111-111111111111')
  const ui = await $.ui.mount({ ...pane(20), surface: 'terminal' })
  expect(await ui.find({ text: /Find me a prompt history plugin/ })).toBeDefined()
  expect(await ui.find({ text: /second prompt/ })).toBeDefined()
  await ui.unmount()
})

test('the open pane follows the top row as the conversation scrolls', async ($, on) => {
  const clock = mock.clock(on)
  await start($, on)
  const ui = await $.ui.mount({ ...pane(20), surface: 'terminal' })
  await $.ui.mount({
    plugin: 'prompt-navigator', surface: 'terminal', component: 'AssistantMessage', requestId: '66666666-6666-4666-8666-000000000000',
    props: { text: 'x', isFirstOfReply: true, onScreen: { first: 1, last: 2, of: 3 } },
  } as never).catch(() => undefined)
  await clock.settle()
  expect(JSON.stringify(await ui.find({ key: '55555555-5555-4555-8555-555555555555:0' }))).toContain('suggestion')
  await ui.unmount()
})

test('summaries reach the newest exchanges past the 40th', { options: { haikuSummaries: true } }, async ($, on) => {
  let calls = 0
  const store: Record<string, unknown> = {}
  on('store.get', (_, e) => ({ value: store[e.key] }))
  on('store.set', (_, e) => {
    store[e.key] = e.value
    return { value: undefined }
  })
  on('store.keys', () => ({ value: Object.keys(store) }))
  on('store.delete', (_, e) => {
    delete store[e.key]
    return { value: undefined }
  })
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('model.complete', () => {
    calls++
    return { value: { isAnswered: true, text: 'summary ' + calls, usage: USAGE } }
  })
  const rows: SessionMessage[] = Array.from({ length: 45 }, (_, i) => [
    { role: 'user', text: 'prompt ' + (i + 1), toolUses: [], uuid: 'p' + (i + 1) },
    { role: 'assistant', text: 'reply ' + (i + 1), toolUses: [], uuid: 'a' + (i + 1) },
  ]).flat() as SessionMessage[]
  const clock = mock.clock(on)
  await start($, on, rows)
  await $.turn.complete(TURN)
  await clock.settle()
  expect(calls).toBe(40)
  expect(store['summary:p45']).toBeDefined()
  expect(store['summary:p5']).toBeUndefined()
  await $.turn.complete(TURN)
  await clock.settle()
  expect(calls).toBe(45)
  expect(store['summary:p1']).toBeDefined()
})

test('haiku summaries are written once and cached', { options: { haikuSummaries: true } }, async ($, on) => {
  let calls = 0
  const store: Record<string, unknown> = {}
  on('store.get', (_, e) => ({ value: store[e.key] }))
  on('store.set', (_, e) => {
    store[e.key] = e.value
    return { value: undefined }
  })
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('model.complete', () => {
    calls++
    return { value: { isAnswered: true, text: 'Asked for a prompt plugin; built one', usage: USAGE } }
  })
  await start($, on)
  await $.turn.complete(TURN)
  await $.turn.complete(TURN)
  expect(calls).toBe(2)
  const ui = await $.ui.mount({ ...pane(20), surface: 'terminal' })
  expect(await ui.find({ text: /Find me a prompt history plugin/ })).toBeDefined()
  expect(await ui.find({ text: /✦ Asked for a prompt plugin; built one/ })).toBeDefined()
  await ui.unmount()
})

test('cached summaries are hidden while summaries are off', async ($, on) => {
  on('store.get', () => ({ value: 'Old cached summary' }))
  await start($, on)
  const ui = await $.ui.mount({ ...pane(20), surface: 'terminal' })
  expect(await ui.find({ text: /Find me a prompt history plugin/ })).toBeDefined()
  expect(await ui.find({ text: /Old cached summary/ })).toBeUndefined()
  await ui.unmount()
})

test('the colors pane shows every theme color', async ($, on) => {
  await start($, on)
  const ui = await $.ui.mount({ ...pane(30), requestId: 'prompt-colors', surface: 'terminal' })
  expect(await ui.find({ text: /claude/ })).toBeDefined()
  expect(await ui.find({ text: /suggestion/ })).toBeDefined()
  await ui.unmount()
})
