// Pure helpers that build the one-line summary of a collapsed tool call.

const ARG_KEYS = [
  'command',
  'file_path',
  'notebook_path',
  'pattern',
  'url',
  'query',
  'description',
  'skill',
  'path',
  'prompt',
]

export const keyArgument = (input: unknown): string | undefined => {
  if (typeof input !== 'object' || input === null) {
    return undefined
  }
  const record = input as Record<string, unknown>
  const key = ARG_KEYS.find(name => typeof record[name] === 'string')
  const value = key
    ? record[key]
    : Object.values(record).find(one => typeof one === 'string')

  return typeof value === 'string' ? value : undefined
}

export const truncate = (text: string, width: number): string => {
  const lines = text.trim().split('\n')
  const first = lines[0] ?? ''
  const isCut = lines.length > 1 || first.length > width

  return isCut ? `${first.slice(0, Math.max(1, width - 1))}…` : first
}

const countLines = (text: string): number =>
  text === '' ? 0 : text.replace(/\n$/, '').split('\n').length

const plural = (count: number, noun: string): string =>
  `${count} ${noun}${count === 1 ? '' : 's'}`

export const outputSize = (output: unknown): string | undefined => {
  if (typeof output === 'string') {
    return plural(countLines(output), 'line')
  }
  if (typeof output !== 'object' || output === null) {
    return undefined
  }
  const record = output as Record<string, unknown>
  const file = record.file as Record<string, unknown> | undefined
  if (typeof file?.numLines === 'number') {
    return plural(file.numLines, 'line')
  }
  if (typeof record.stdout === 'string' || typeof record.stderr === 'string') {
    const all = [record.stdout, record.stderr].filter(
      (one): one is string => typeof one === 'string' && one !== '',
    )
    return plural(countLines(all.join('\n')), 'line')
  }
  if (Array.isArray(record.filenames)) {
    return plural(record.filenames.length, 'file')
  }
  if (typeof record.numLines === 'number') {
    return plural(record.numLines, 'line')
  }
  if (typeof record.content === 'string') {
    return plural(countLines(record.content), 'line')
  }

  return undefined
}

export type CallStatus = {
  isRunning: boolean
  isErrored: boolean
  isInterrupted: boolean
}

export const statusMark = (status: CallStatus): string => {
  if (status.isRunning) {
    return '…'
  }
  if (status.isInterrupted) {
    return 'interrupted'
  }

  return status.isErrored ? '✗' : '✓'
}
