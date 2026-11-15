export type Mode = 'auto' | 'collapsed' | 'expanded'
export type Overrides = Record<string, boolean>

declare module 'claude-code' {
  interface PluginState {
    'collapse-tools': { mode: Mode; overrides: Overrides }
  }
}
