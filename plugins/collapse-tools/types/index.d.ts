export type Mode = 'auto' | 'collapsed' | 'expanded'
/** A row's own choice, kept while /collapse has not reset it (its epoch). */
export type Override = { open: boolean; epoch: number }

declare module 'claude-code' {
  interface PluginState {
    'collapse-tools': { mode: Mode; epoch: number; override: StateFamily<Override | null> }
  }
}
