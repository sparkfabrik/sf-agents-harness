export type Reply = { id: string; text: string }

export type Prompt = {
  id: string
  text: string
  /** The last question or sentence of the assistant message a short prompt answered. */
  context?: string
  /** A Haiku summary of the exchange, when summaries are on. */
  summary?: string
  /** The assistant's text messages (the ● rows) that followed the prompt. */
  replies: Reply[]
}

declare module 'claude-code' {
  interface PluginState {
    'prompt-navigator': {
      prompts: Shaped<Prompt[]>
      lastId: string
      /** First item of the window; -1 follows the end. */
      offset: number
      showReplies: boolean
      /** The topmost transcript row on screen, written to redraw the pane. */
      top: string
    }
  }
}
