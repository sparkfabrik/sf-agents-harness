import { expect, test } from 'claude-code/testing'
import type { RenderPropsOf } from 'claude-code'

const SURFACES = ['terminal', 'desktop'] as const

const COMMAND = {
  command: 'collapse',
  origin: { kind: 'composer' },
  presentation: { isFullscreen: true, columns: 100 },
} as const

const BASH_ROW: RenderPropsOf['ToolUse'] = {
  tool_use_id: 'toolu_1',
  tool: 'Bash',
  input: { command: 'npm test' },
  isRunning: false,
  isErrored: false,
  isInterrupted: false,
  output: { stdout: 'a\nb\nc\n', stderr: '' },
}

const EDIT_ROW: RenderPropsOf['ToolUse'] = {
  ...BASH_ROW,
  tool_use_id: 'toolu_2',
  tool: 'Edit',
  input: { file_path: '/tmp/x.ts' },
  output: {},
}

for (const surface of SURFACES) {
  test(`${surface}: a Bash call starts collapsed with a summary`, async ($, on) => {
    on('ui.render', ($, e) => {
      const { Text } = $.ui.resolve(e)
      return <Text>engine row</Text>
    })
    const ui = await $.ui.mount({ plugin: 'collapse-tools', surface, component: 'ToolUse', props: BASH_ROW })

    expect((await ui.find({ key: 'chevron-toolu_1' }))?.props.label).toBe('▸')
    expect(await ui.find({ text: 'engine row' })).toBeUndefined()
    expect(await ui.find({ text: /npm test/ })).toBeDefined()
    expect(await ui.find({ text: /✓ 3 lines/ })).toBeDefined()
  })

  test(`${surface}: clicking the chevron expands and collapses`, async ($, on) => {
    on('ui.render', ($, e) => {
      const { Text } = $.ui.resolve(e)
      return <Text>engine row</Text>
    })
    const ui = await $.ui.mount({ plugin: 'collapse-tools', surface, component: 'ToolUse', props: BASH_ROW })

    await ui.press({ key: 'chevron-toolu_1' })
    expect((await ui.find({ key: 'chevron-toolu_1' }))?.props.label).toBe('▾')
    expect(await ui.find({ text: 'engine row' })).toBeDefined()

    await ui.press({ key: 'chevron-toolu_1' })
    expect(await ui.find({ text: 'engine row' })).toBeUndefined()
  })

  test(`${surface}: Edit stays expanded by default`, async ($, on) => {
    on('ui.render', ($, e) => {
      const { Text } = $.ui.resolve(e)
      return <Text>engine row</Text>
    })
    const ui = await $.ui.mount({ plugin: 'collapse-tools', surface, component: 'ToolUse', props: EDIT_ROW })

    expect(await ui.find({ text: 'engine row' })).toBeDefined()
  })

  test(`${surface}: a running call stays expanded, then collapses when done`, async ($, on) => {
    on('ui.render', ($, e) => {
      const { Text } = $.ui.resolve(e)
      return <Text>engine row</Text>
    })
    const running = { ...BASH_ROW, isRunning: true, output: undefined }
    const ui = await $.ui.mount({ plugin: 'collapse-tools', surface, component: 'ToolUse', props: running })
    expect(await ui.find({ text: 'engine row' })).toBeDefined()

    await ui.redraw(BASH_ROW)
    expect(await ui.find({ text: 'engine row' })).toBeUndefined()
  })
}

test('the result of a collapsed call is hidden', async ($, on) => {
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine result</Text>
  })
  const ui = await $.ui.mount({
    plugin: 'collapse-tools',
    surface: 'terminal',
    component: 'ToolResult',
    props: { tool_use_id: 'toolu_1', tool: 'Bash', output: BASH_ROW.output, isErrored: false },
  })

  expect(await ui.find({ text: 'engine result' })).toBeUndefined()
})

test('/collapse none expands every call, /collapse all collapses Edit too', async ($, on) => {
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine row</Text>
  })
  const bash = await $.ui.mount({ plugin: 'collapse-tools', surface: 'terminal', component: 'ToolUse', props: BASH_ROW })
  const edit = await $.ui.mount({ plugin: 'collapse-tools', surface: 'terminal', component: 'ToolUse', props: EDIT_ROW })

  await $.command.run({ ...COMMAND, args: 'none' })
  await bash.redraw()
  expect(await bash.find({ text: 'engine row' })).toBeDefined()

  await $.command.run({ ...COMMAND, args: 'all' })
  await edit.redraw()
  expect(await edit.find({ text: 'engine row' })).toBeUndefined()
})

test('a chevron choice is reset by /collapse all', async ($, on) => {
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine row</Text>
  })
  const bash = await $.ui.mount({ plugin: 'collapse-tools', surface: 'terminal', component: 'ToolUse', props: BASH_ROW })
  await bash.press({ key: 'chevron-toolu_1' })
  expect(await bash.find({ text: 'engine row' })).toBeDefined()

  await $.command.run({ ...COMMAND, args: 'all' })
  await bash.redraw()
  expect(await bash.find({ text: 'engine row' })).toBeUndefined()
})

test('the ctrl+o transcript and --verbose draw every row in full', async ($, on) => {
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine row</Text>
  })
  const row = await $.ui.mount({ plugin: 'collapse-tools', surface: 'terminal', component: 'ToolUse', props: { ...BASH_ROW, isExpanded: true } })
  expect(await row.find({ text: 'engine row' })).toBeDefined()
  expect(await row.find({ key: 'chevron-toolu_1' })).toBeUndefined()

  const result = await $.ui.mount({
    plugin: 'collapse-tools',
    surface: 'terminal',
    component: 'ToolResult',
    props: { tool_use_id: 'toolu_1', tool: 'Bash', output: BASH_ROW.output, isErrored: false, isExpanded: true },
  })
  expect(await result.find({ text: 'engine row' })).toBeDefined()
})

test('a multi-line command says how many more lines it runs', async ($, on) => {
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine row</Text>
  })
  const props = { ...BASH_ROW, input: { command: 'echo ok\nrm -rf "$HOME/project"' } }
  const ui = await $.ui.mount({ plugin: 'collapse-tools', surface: 'terminal', component: 'ToolUse', props })
  expect(await ui.find({ text: /\+1 line/ })).toBeDefined()
})

test('expandedTools takes a comma-separated list', { options: { expandedTools: 'Read, Bash' } }, async ($, on) => {
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine row</Text>
  })
  const bash = await $.ui.mount({ plugin: 'collapse-tools', surface: 'terminal', component: 'ToolUse', props: BASH_ROW })
  const edit = await $.ui.mount({ plugin: 'collapse-tools', surface: 'terminal', component: 'ToolUse', props: EDIT_ROW })

  expect(await bash.find({ text: 'engine row' })).toBeDefined()
  expect(await edit.find({ text: 'engine row' })).toBeUndefined()
})

test('disabled: rows draw as the engine does', { options: { enabled: false } }, async ($, on) => {
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine row</Text>
  })
  const ui = await $.ui.mount({ plugin: 'collapse-tools', surface: 'terminal', component: 'ToolUse', props: BASH_ROW })

  expect(await ui.find({ text: 'engine row' })).toBeDefined()
})

const FAILED_ROW: RenderPropsOf['ToolUse'] = {
  ...BASH_ROW,
  tool_use_id: 'toolu_3',
  isErrored: true,
  output: 'Exit code 1',
}

test('collapseFailed on: a failed call starts collapsed with a ✗ mark', { options: { collapseFailed: true } }, async ($, on) => {
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine row</Text>
  })
  const ui = await $.ui.mount({ plugin: 'collapse-tools', surface: 'terminal', component: 'ToolUse', props: FAILED_ROW })

  expect(await ui.find({ text: 'engine row' })).toBeUndefined()
  expect(await ui.find({ text: /✗/ })).toBeDefined()
})

test('a failed call starts expanded by default', async ($, on) => {
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine row</Text>
  })
  const ui = await $.ui.mount({ plugin: 'collapse-tools', surface: 'terminal', component: 'ToolUse', props: FAILED_ROW })

  expect(await ui.find({ text: 'engine row' })).toBeDefined()
})

const REPORT: RenderPropsOf['UserMessage'] = {
  text: '[Subagent hand-back] The text below is the final report. The report follows:\n  1. Top-level entries: README.md\n  2. register.tsx: 202 lines',
  origin: { kind: 'task-notification' },
  isExpanded: true,
  from: { name: 'general-purpose' },
}

test('a subagent report starts collapsed and expands on click', async ($, on) => {
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine report</Text>
  })
  const ui = await $.ui.mount({ plugin: 'collapse-tools', surface: 'terminal', component: 'UserMessage', props: REPORT, requestId: 'msg_1' })

  expect(await ui.find({ text: 'engine report' })).toBeUndefined()
  expect(await ui.find({ text: /Report from general-purpose/ })).toBeDefined()
  expect(await ui.find({ text: /Top-level entries/ })).toBeDefined()

  await ui.press({ key: 'message-msg_1' })
  expect(await ui.find({ text: 'engine report' })).toBeDefined()
})

const PEER_MESSAGE: RenderPropsOf['UserMessage'] = {
  text: 'Can you review my change?',
  origin: { kind: 'peer' },
  isExpanded: true,
  from: { name: 'other session' },
}

test('a message from another agent is not collapsed by default', async ($, on) => {
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine report</Text>
  })
  const ui = await $.ui.mount({ plugin: 'collapse-tools', surface: 'terminal', component: 'UserMessage', props: PEER_MESSAGE })

  expect(await ui.find({ text: 'engine report' })).toBeDefined()
})

test('collapseOtherAgents on: a message from another agent starts collapsed', { options: { collapseOtherAgents: true } }, async ($, on) => {
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine report</Text>
  })
  const ui = await $.ui.mount({ plugin: 'collapse-tools', surface: 'terminal', component: 'UserMessage', props: PEER_MESSAGE })

  expect(await ui.find({ text: 'engine report' })).toBeUndefined()
  expect(await ui.find({ text: /Message from other session/ })).toBeDefined()
})

test('collapseOtherAgents on: a channel message is not collapsed', { options: { collapseOtherAgents: true } }, async ($, on) => {
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine report</Text>
  })
  const props = { ...PEER_MESSAGE, origin: { kind: 'channel', server: 'slack' } } as const
  const ui = await $.ui.mount({ plugin: 'collapse-tools', surface: 'terminal', component: 'UserMessage', props })

  expect(await ui.find({ text: 'engine report' })).toBeDefined()
})

test('a peer message with the hand-back frame is not read as a report', async ($, on) => {
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine report</Text>
  })
  const props = { ...REPORT, origin: { kind: 'peer' } } as const
  const ui = await $.ui.mount({ plugin: 'collapse-tools', surface: 'terminal', component: 'UserMessage', props })

  expect(await ui.find({ text: 'engine report' })).toBeDefined()
})

test('collapseOwnSubagents off: a subagent report draws as the engine does', { options: { collapseOwnSubagents: false } }, async ($, on) => {
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine report</Text>
  })
  const ui = await $.ui.mount({ plugin: 'collapse-tools', surface: 'terminal', component: 'UserMessage', props: REPORT })

  expect(await ui.find({ text: 'engine report' })).toBeDefined()
})
