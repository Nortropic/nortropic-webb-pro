export type Roll = { rubrik: string; lage: string; text: string; sessioner: string[] }
export type Sammanfattning = {
  slug: string | null
  namn: string | null
  testdata: boolean
  moment: string | null
  korning: string | null
  vantar: boolean
  roller: Roll[]
  handlingar: string[]
  avbrutna: string[]
  lever: number
  oppna: number
  paus: string | null
  pausade: number
  last: string | null
  url: string | null
  fel: string | null
}

declare module 'claude-code' {
  interface PluginState {
    'nortropic-arbetsyta': { lage: Sammanfattning | null }
  }
}
