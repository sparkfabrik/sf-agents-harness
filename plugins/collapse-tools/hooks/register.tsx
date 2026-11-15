import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Mode, Overrides } from '../types'
import { keyArgument, outputSize, statusMark, truncate } from './summary'
import type { CallStatus } from './summary'

const mode = atom({ plugin: 'collapse-tools', key: 'mode' } as const, 'auto' as Mode)
const overrides = atom({ plugin: 'collapse-tools', key: 'overrides' } as const, {} as Overrides)

const AGENT_TOOLS = ['Agent', 'Task']
const HANDBACK = /^\s*\[Subagent hand-back\]/
const REPORT_START = /The report follows:\s*/
const MODES: Record<string, Mode> = { all: 'collapsed', none: 'expanded' }

async function isOpen($: EngineInterface, id: string, auto: boolean): Promise<boolean> {
  const chosen = (await read($, overrides))[id]
  if (chosen !== undefined) {
    return chosen
  }
  const current = await read($, mode)

  return current === 'auto' ? auto : current === 'expanded'
}

// A string field, comma-separated, so /config can show it as a text row; an
// array is still read for values stored when the field was `multiple`.
function toolList(value: unknown): string[] {
  const names = Array.isArray(value) ? value : typeof value === 'string' ? value.split(',') : []

  return names.map(name => String(name).trim()).filter(Boolean)
}

async function setOpen($: EngineInterface, id: string, open: boolean): Promise<void> {
  await update($, overrides, all => ({ ...all, [id]: open }))
}

export const register: Register = (on, options) => {
  if (options.enabled === false) {
    return
  }
  const expandedTools = toolList(options.expandedTools)
  const collapseOwnSubagents = options.collapseOwnSubagents !== false
  const collapseFailed = options.collapseFailed !== false
  const collapseOtherAgents = options.collapseOtherAgents === true

  const startsOpen = (tool: string, status: CallStatus): boolean =>
    status.isRunning ||
    (status.isErrored && !collapseFailed) ||
    status.isInterrupted ||
    expandedTools.includes(tool) ||
    (!collapseOwnSubagents && AGENT_TOOLS.includes(tool))

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'collapse',
      description: 'Collapse or expand tool calls: all, none, or toggle (default)',
      argumentHint: 'all|none|toggle',
    })

    return next(e)
  })

  on('command.run', { command: 'collapse' }, async ($, e) => {
    const arg = e.args.trim() || 'toggle'
    const current = await read($, mode)
    const target = arg === 'toggle' ? (current === 'expanded' ? 'auto' : 'expanded') : MODES[arg]
    if (target === undefined) {
      return { text: `Unknown argument "${arg}": use all, none or toggle.` }
    }
    await update($, overrides, () => ({}))
    await update($, mode, () => target)
    const words: Record<Mode, string> = {
      auto: 'Tool calls back to their default state.',
      collapsed: 'All tool calls collapsed.',
      expanded: 'All tool calls expanded.',
    }

    return { text: words[target] }
  })

  on('ui.render', { component: 'ToolUse' }, async ($, e, next) => {
    const { tool, tool_use_id: id, input, output } = e.props
    const open = await isOpen($, id, startsOpen(tool, e.props))
    const { Box, Button, Text } = $.ui.resolve(e)
    const chevron = (
      <Button
        key={`chevron-${id}`}
        plain
        label={open ? '▾' : '▸'}
        onPress={() => setOpen($, id, !open)}
      />
    )

    if (open) {
      return (
        <Box flexDirection="row">
          {chevron}
          <Text> </Text>
          {await next(e)}
        </Box>
      )
    }

    const columns = e.viewport?.columns ?? 100
    const argument = keyArgument(input)
    const size = e.props.isRunning ? undefined : outputSize(output)
    const mark = statusMark(e.props)

    return (
      <Box flexDirection="row">
        {chevron}
        <Text>
          {' '}
          <Text bold>{tool}</Text>
          {argument === undefined
            ? ''
            : `(${truncate(argument, Math.max(20, columns - tool.length - 30))})`}{' '}
          <Text dimColor>
            {mark}
            {size === undefined ? '' : ` ${size}`}
          </Text>
        </Text>
      </Box>
    )
  })

  on('ui.render', { component: 'ToolResult' }, async ($, e, next) => {
    const status = { isRunning: false, isErrored: e.props.isErrored, isInterrupted: false }
    if (await isOpen($, e.props.tool_use_id, startsOpen(e.props.tool, status))) {
      return next(e)
    }
    const { Box } = $.ui.resolve(e)

    return <Box />
  })

  // A background subagent's report arrives as a message row from that agent,
  // opened by the engine's hand-back frame; a teammate's or another session's
  // message is a row from that agent without it. The engine can draw either in
  // full (isExpanded) under its speaker label, so that flag is not a reason to
  // pass. A channel's message is a person's, and is never collapsed.
  on('ui.render', { component: 'UserMessage' }, async ($, e, next) => {
    const { from, origin, text } = e.props
    if (from === undefined || origin.kind === 'channel') {
      return next(e)
    }
    const isReport = HANDBACK.test(text)
    if (isReport ? !collapseOwnSubagents : !collapseOtherAgents) {
      return next(e)
    }
    const id = `message-${e.requestId}`
    const open = await isOpen($, id, false)
    const { Box, Button, Text } = $.ui.resolve(e)
    const chevron = (
      <Button key={id} plain label={open ? '▾' : '▸'} onPress={() => setOpen($, id, !open)} />
    )

    if (open) {
      return (
        <Box flexDirection="row">
          {chevron}
          <Text> </Text>
          {await next(e)}
        </Box>
      )
    }
    const columns = e.viewport?.columns ?? 100
    const report = isReport ? (text.split(REPORT_START)[1] ?? '') : text
    const prefix = `${isReport ? 'Report' : 'Message'} from ${from.name}`

    return (
      <Box flexDirection="row">
        {chevron}
        <Text>
          {' '}
          <Text bold>{prefix}</Text>
          <Text dimColor>
            {report.trim() === ''
              ? ''
              : ` ${truncate(report, Math.max(20, columns - prefix.length - 10))}`}
          </Text>
        </Text>
      </Box>
    )
  })

  on('ui.render', { component: 'ToolGroup' }, async ($, e, next) => {
    if (e.props.isExpanded) {
      return next(e)
    }
    const id = `group-${e.requestId}`
    const open = await isOpen($, id, false)
    const { Box, Button, Text } = $.ui.resolve(e)
    const chevron = (
      <Button key={id} plain label={open ? '▾' : '▸'} onPress={() => setOpen($, id, !open)} />
    )

    if (!open) {
      return (
        <Box flexDirection="row">
          {chevron}
          <Text> </Text>
          {await next(e)}
        </Box>
      )
    }

    return (
      <Box flexDirection="column">
        <Box flexDirection="row">
          {chevron}
          <Text dimColor> {e.props.calls.length} calls</Text>
        </Box>
        {await next({ ...e, props: { ...e.props, isExpanded: true } })}
      </Box>
    )
  })
}
