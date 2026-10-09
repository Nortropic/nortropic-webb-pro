// Moddens prov (claude plugin test mod/nortropic-arbetsyta): raden och panelen ritas ur dashboardens läge, på terminalen och i
// Desktop, och en dashboard som inte svarar ger en inaktuell rad, aldrig ett påhittat läge. Dashboarden är en attrapp här
// (http.fetch besvaras under modden); den riktiga läsvägen prövas i kontroller/rokprov/revision/prov_arbetsyta.py.
import { describe, expect, mock, test } from 'claude-code/testing'

import { sammanfatta } from '../hooks/register'

const LAGE = {
  slug: 'testdata-provverkstaden', projekt: { namn: 'Provverkstaden (testdata)', testdata: true },
  moment: { nr: 3, namn: 'Ditt val', status: 'väntar på ägaren' }, korning: { startad: '2026-10-09T05:00:00Z', vantar_pa_agaren: true },
  roller: {
    arbetsledning: { rubrik: 'Arbetsledning', lage: 'beslut', lage_text: 'partnern har svarat', sessioner: ['p'] },
    utforande: { rubrik: 'Utförande', lage: 'aktiv', lage_text: '1 session lever', sessioner: ['a'] },
    granskning: { rubrik: 'Granskning', lage: 'vantar', lage_text: 'ingen session för granskning har startat', sessioner: [] },
  },
  handlingar: [{ text: 'Förfina de valda förslagen' }], sessioner: [{ session_id: 'a', lage: 'aktiv' }, { session_id: 'b', lage: 'aktiv', styrning: { lage: 'pausad' } }],
  samverkan: { oppna: 2, projektpaus: { begard: '2026-10-09T09:59:00Z' } },
}
const BAND = { component: 'AbovePrompt' as const, props: { hasSurvey: false, isWorking: false, maxRows: 4, bodyColumns: 140, scroll: { offset: 0, bodyRows: 4 }, view: {} } }
const PANEL = { component: 'Pane' as const, requestId: 'nortropic', props: { title: 'Nortropic', isFocused: true, bodyColumns: 80, placement: 'dock' as const, scroll: { offset: 0, bodyRows: 30 }, view: {} } }

function dashboard(on: any, svarar = true) {
  on('http.fetch', async (_$: unknown, e: { url: string }) => {
    if (!svarar) return { deny: 'ECONNREFUSED' }
    const text = e.url.endsWith('/api/arbetsyta') ? JSON.stringify({ projekt: [{ slug: LAGE.slug }] }) : JSON.stringify(LAGE)
    return { value: { status: 200, ok: true, headers: {}, text } }
  })
  on('command.register', async () => ({ value: undefined }))
  on('ui.open', async () => ({ value: { isPlaced: true } }))
  on('ui.toast', async () => ({ value: undefined }))
  on('ui.render', { component: 'AbovePrompt' }, async ($: any, e: any) => {  // det som andra moddar och motorn ritar under raden
    const { Text } = $.ui.resolve(e)
    return Text({ children: ['en annan modds rad'] })
  })
}

describe('nortropic-arbetsyta', () => {
  test('sammanfattningen bär rollerna, länken och testmärkningen', () => {
    const s = sammanfatta(LAGE, 'http://localhost:4771', '2026-10-09T10:00:00Z')
    expect(s.testdata).toBe(true)
    expect(s.url).toBe('http://localhost:4771/#/arbetsyta/testdata-provverkstaden')
    expect(s.roller.map((r) => r.lage)).toEqual(['beslut', 'aktiv', 'vantar'])
    expect(s.lever).toBe(2)
    expect(s.vantar).toBe(true)
    expect(s.oppna).toBe(2)
    expect(s.pausade).toBe(1)
    expect(s.paus).toBeTruthy()
  })

  test('raden och panelen ritas ur läget på terminalen och i Desktop', async ($, on) => {
    mock.clock(on, { now: Date.parse('2026-10-09T10:00:00Z') })
    mock.env(on, { NWP_ARBETSYTA_KUND: 'testdata-provverkstaden' })
    dashboard(on)
    await $.command.run({ command: 'nortropic', args: '' })
    for (const surface of ['terminal', 'desktop'] as const) {
      const rad = await $.ui.mount({ plugin: 'nortropic-arbetsyta', surface, ...BAND })
      expect(await rad.find({ type: 'Text', text: /Provverkstaden \(testdata\).*utförande arbetar, granskning väntar på start; pausad; 2 meddelanden väntar på dig/ })).toBeDefined()
      expect(await rad.find({ type: 'Text', text: /en annan modds rad/ })).toBeDefined()  // andra moddars rader står kvar
      await rad.unmount()
      const panel = await $.ui.mount({ plugin: 'nortropic-arbetsyta', surface, ...PANEL })
      expect(await panel.find({ type: 'Text', text: /väntar på ditt beslut/ })).toBeDefined()
      expect(await panel.find({ type: 'Text', text: /2 meddelanden från sessionerna väntar på ditt beslut under Meddelanden/ })).toBeDefined()
      expect(await panel.find({ type: 'Text', text: /1 session pausad/ })).toBeDefined()
      expect(await panel.find({ type: 'Link' })).toBeDefined()
      await panel.unmount()
    }
  })

  test('en dashboard som inte svarar ger en inaktuell rad, inget påhittat läge', async ($, on) => {
    mock.clock(on, { now: Date.parse('2026-10-09T10:00:00Z') })
    mock.env(on, {})
    dashboard(on, false)
    await $.command.run({ command: 'nortropic', args: '' })
    const rad = await $.ui.mount({ plugin: 'nortropic-arbetsyta', surface: 'terminal', ...BAND })
    expect(await rad.find({ type: 'Text', text: /dashboarden svarar inte/ })).toBeDefined()
    await rad.unmount()
  })
})
