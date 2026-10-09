// Nortropics arbetsyta i Claude Code (ägarens uppdrag 2026-10-09, kunskap/arbetsyta.md): en rad ovanför prompten och en
// panel (/nortropic) med kund, moment, rollsessioner och nästa handling, lästa ur dashboardens läsväg
// (GET /api/arbetsyta på http://localhost:<port>), och en länk till arbetsytan i webbläsaren. Modden läser bara: den
// skriver inget, godkänner inget, skriver inte om någon prompt och anropar ingen modell. Den ser inte motorns
// claude -p-processer själv; allt den visar kommer från dashboardens läge, med tiden det lästes.
import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Roll, Sammanfattning } from '../types'

const PANEL = 'nortropic'
const INTERVALL = 15000
const lage = atom({ plugin: 'nortropic-arbetsyta', key: 'lage' } as const, null)
const LAGEN: Record<string, string> = {
  vantar: 'väntar på start', startar: 'start pågår', aktiv: 'arbetar', verktyg: 'väntar på verktyg',
  beslut: 'väntar på ditt beslut', avslutad: 'avslutad', avbruten: 'avbruten', okant: 'okänt läge',
}

type Lage = {
  slug?: string; projekt?: { namn?: string; testdata?: boolean }; moment?: { nr: number; namn: string; status: string } | null
  korning?: { startad?: string; lage?: string; vantar_pa_agaren?: boolean } | null
  roller?: Record<string, { rubrik: string; lage: string; lage_text: string; sessioner: string[] }>
  handlingar?: { text: string }[]; sessioner?: { session_id?: string; roll?: string; lage?: string; kandidat?: string; styrning?: { lage?: string } }[]
  samverkan?: { oppna?: number; projektpaus?: { begard?: string } | null } | null
}

export function sammanfatta(d: Lage, bas: string, nu: string): Sammanfattning {
  const roller: Roll[] = ['arbetsledning', 'utforande', 'granskning'].map((k) => {
    const r = d.roller?.[k]
    return { rubrik: r?.rubrik ?? k, lage: r?.lage ?? 'okant', text: r?.lage_text ?? 'inte observerat', sessioner: r?.sessioner ?? [] }
  })
  const sess = d.sessioner ?? []
  return {
    slug: d.slug ?? null,
    namn: d.projekt?.namn ?? d.slug ?? null,
    testdata: Boolean(d.projekt?.testdata),
    moment: d.moment ? `${d.moment.nr}. ${d.moment.namn}, ${d.moment.status}` : null,
    korning: d.korning?.startad ? `körningen ${d.korning.startad.slice(0, 16).replace('T', ' ')} UTC` : null,
    vantar: Boolean(d.korning?.vantar_pa_agaren),
    roller,
    handlingar: (d.handlingar ?? []).map((h) => h.text),
    avbrutna: sess.filter((s) => s.lage === 'avbruten' && s.session_id).map((s) => String(s.session_id)),
    lever: sess.filter((s) => s.lage === 'aktiv' || s.lage === 'verktyg' || s.lage === 'startar').length,
    oppna: d.samverkan?.oppna ?? 0,
    paus: d.samverkan?.projektpaus ? 'körningen är pausad eller har paus begärd' : null,
    pausade: sess.filter((s) => s.styrning?.lage === 'pausad').length,
    last: nu,
    url: d.slug ? `${bas}/#/arbetsyta/${encodeURIComponent(d.slug)}` : `${bas}/#/arbetsyta`,
    fel: null,
  }
}

// modulens läge: en omladdning börjar om, och nästa läsning fyller det igen
let bas = 'http://localhost:4771'
let forra: Sammanfattning | null = null
let klockan: { cancel: () => void } | null = null

async function las($: EngineInterface) {
  const nu = new Date(await $.clock.now()).toISOString()
  try {
    const lista = await $.http.fetch(bas + '/api/arbetsyta')
    if (!lista.ok) throw new Error('HTTP ' + lista.status)
    const projekt = (JSON.parse(lista.text).projekt ?? []) as { slug: string }[]
    const onskad = await $.env.get('NWP_ARBETSYTA_KUND')
    const p = projekt.find((x) => x.slug === onskad) ?? projekt[0]
    if (!p) {
      await update($, lage, () => ({ ...tom(nu), fel: 'inga kunder i arbetsytan än' }))
      return
    }
    const svar = await $.http.fetch(bas + '/api/arbetsyta/' + encodeURIComponent(p.slug))
    if (!svar.ok) throw new Error('HTTP ' + svar.status)
    const ny = sammanfatta(JSON.parse(svar.text) as Lage, bas, nu)
    if (forra && forra.slug === ny.slug) {  // bara verkliga övergångar, aldrig varje verktygsanrop
      if (!forra.vantar && ny.vantar) $.ui.toast(`Nortropic: ${ny.namn} väntar på ditt beslut`)
      const nyaAvbrott = ny.avbrutna.filter((s) => !forra!.avbrutna.includes(s)).length
      if (nyaAvbrott) $.ui.toast(`Nortropic: ${nyaAvbrott} session${nyaAvbrott > 1 ? 'er' : ''} avbröts hos ${ny.namn}`)
      if (ny.oppna > forra.oppna) $.ui.toast(`Nortropic: ${ny.oppna} meddelande${ny.oppna > 1 ? 'n' : ''} från sessionerna väntar på ditt beslut`)
    }
    forra = ny
    await update($, lage, () => ny)
  } catch (e) {
    await update($, lage, (f) => ({ ...(f ?? tom(nu)), fel: `dashboarden svarar inte på ${bas} (${String((e as Error)?.message ?? e).slice(0, 80)}); starta ./dashboard.sh`, last: (f ?? tom(nu)).last }))
  }
}


export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    if (klockan) klockan.cancel()  // en omladdning eller en andra start: en klocka åt gången
    const port = await $.env.get('NWP_DASHBOARD_PORT')
    if (port && /^\d{2,5}$/.test(port)) bas = 'http://localhost:' + port
    klockan = $.clock.every(INTERVALL, () => las($))
    void las($)
    try {
      await $.command.register({ name: 'nortropic', description: 'Nortropics arbetsyta: kund, moment och rollsessioner (läser bara)', immediate: true })
    } catch {
      // ett upptaget namn stoppar inte raden ovanför prompten
    }
    return next(e)
  })

  on('command.run', { command: 'nortropic' }, async ($) => {
    await las($)
    await $.ui.open({ id: PANEL, title: 'Nortropic', focus: true, closeOnEscape: true })
    return {}
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const l = await read($, lage) as Sammanfattning | null
    if (e.props.hasSurvey || !l) return next(e)
    const { Box, Text } = $.ui.resolve(e)
    const utf = l.roller.find((r) => r.rubrik === 'Utförande'), gr = l.roller.find((r) => r.rubrik === 'Granskning')
    const text = l.fel && !l.slug ? `Nortropic: ${l.fel}`
      : `Nortropic ${l.namn ?? ''}${l.testdata ? ' (testdata)' : ''}: ${l.moment ?? 'moment okänt'}; utförande ${LAGEN[utf?.lage ?? 'okant'] ?? utf?.lage}, granskning ${LAGEN[gr?.lage ?? 'okant'] ?? gr?.lage}${l.paus ? '; pausad' : ''}${l.oppna ? `; ${l.oppna} meddelande${l.oppna > 1 ? 'n' : ''} väntar på dig` : ''}; läst ${(l.last ?? '').slice(11, 16)} UTC${l.fel ? ' (inaktuellt)' : ''} · /nortropic`
    const andras = await next(e)  // andra moddars rader står kvar under vår
    return (
      <Box flexDirection="column">
        <Text dimColor wrap="truncate-end">{text}</Text>
        {andras}
      </Box>
    )
  })

  on('ui.render', { component: 'Pane', requestId: PANEL }, async ($, e) => {
    const l = await read($, lage) as Sammanfattning | null
    const { Box, Text, Link, Button } = $.ui.resolve(e)
    if (!l) return <Text dimColor>Läser arbetsytan…</Text>
    const oppna = l.url ?? `${bas}/#/arbetsyta`
    return (
      <Box flexDirection="column" gap={1}>
        <Box flexDirection="column">
          <Text bold>{(l.namn ?? 'Ingen kund') + (l.testdata ? ' (testdata)' : '')}</Text>
          <Text>{l.moment ?? 'Moment okänt'}{l.korning ? `, ${l.korning}` : ''}</Text>
          {l.vantar ? <Text color="yellow">Körningen väntar på ditt beslut.</Text> : <Text dimColor>{l.lever} sessioner lever.</Text>}
          {l.paus ? <Text color="cyan">{`Paus: ${l.paus}${l.pausade ? ` (${l.pausade} session${l.pausade > 1 ? 'er' : ''} pausad${l.pausade > 1 ? 'e' : ''})` : ''}.`}</Text> : null}
          {l.oppna ? <Text color="yellow">{`${l.oppna} meddelande${l.oppna > 1 ? 'n' : ''} från sessionerna väntar på ditt beslut under Meddelanden.`}</Text> : null}
          {l.fel ? <Text color="red">{`Inaktuellt: ${l.fel}`}</Text> : null}
        </Box>
        <Box flexDirection="column">
          {l.roller.map((r) => <Text key={r.rubrik}>{`${r.rubrik}: ${LAGEN[r.lage] ?? r.lage}. ${r.text}`}</Text>)}
        </Box>
        <Text dimColor>{l.handlingar.length ? `Nästa handling i arbetsytan: ${l.handlingar.join(', ')}` : 'Ingen handling är möjlig just nu.'}</Text>
        <Box flexDirection="row" columnGap={2}>
          <Link href={oppna} label="Öppna arbetsytan" />
          {e.surface === 'terminal'
            ? <Button key="oppna" label="Öppna i webbläsaren" onPress={async () => { try { await $.process.run(['open', oppna]) } catch { $.ui.toast('Kunde inte öppna webbläsaren') } }} />
            : null}
        </Box>
        <Text dimColor>{`Läst ${(l.last ?? '').slice(11, 19)} UTC ur dashboardens läsväg var ${INTERVALL / 1000}:e sekund. Panelen startar inget, skickar inget och beslutar inget; meddelanden, paus, beslut och godkännande gör du i arbetsytan, där din nyckel och beslutstjänsten gäller.`}</Text>
      </Box>
    )
  })
}

function tom(nu: string): Sammanfattning {
  return { slug: null, namn: null, testdata: false, moment: null, korning: null, vantar: false, roller: [], handlingar: [], avbrutna: [], lever: 0, oppna: 0, paus: null, pausade: 0, last: nu, url: null, fel: null }
}
