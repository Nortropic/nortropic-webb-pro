#!/usr/bin/env python3
"""brev.py — ett brevutkast till ett prospekt, skrivet av modellen ur det vi mätt och sett. Faktalistan ur
underlag/<slug>/PROSPEKT.json är det enda brevet får åberopa; en siffra utanför listan stoppar utkastet (FEL.txt, ingen
BREV.json). Avsändare, avregistrering och artikel 13/14-text lägger utskick.py till; modellen skriver bara ämne, kropp
och ringmanus. Arbetarfiler i underlag/<slug>/brev/.

    .venv/bin/python kontroller/brev.py <slug> --kampanj <k> [--torr]     # --torr skriver bara PROMPT.txt

Exit: 0 utkast skrivet · 1 modellen gav inget giltigt svar eller kontrollen föll (se FEL.txt) · 2 fel i anropet.
Miljö: NWP_BREV_MODELL, NWP_BREV_EFFORT (annars ~/.claude/settings.json, annars opus[1m] och high), NWP_BREV_FRIST (600 s).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prospektfiler as pf  # noqa: E402
import copy_kontroll as ck  # noqa: E402

ROOT = pf.ROOT
SCHEMA = ROOT / 'kritik' / 'SCHEMA-brev.json'
VERKTYG = ['Read', 'Glob', 'Grep', 'Skill']
NEKAS = ['Write', 'Edit', 'Bash', 'NotebookEdit', 'WebFetch', 'WebSearch', 'Task']
TILLATNA_TAL = {'15'}  # mötets längd i minuter
TAL = re.compile(r'\d+(?:[,.]\d+)?')
ROLLER_RE = re.compile(r'^(info|kontakt|hej|hello|mail|post|office|kansli|bokning|admin|reception|support|kundtj[aä]nst|kontor|order|webb?)')


def ren_miljo():
    return {k: v for k, v in os.environ.items() if k != 'CLAUDECODE' and not k.startswith('CLAUDE_CODE_') and not k.startswith('NWP_')}


def modell_och_effort():
    anv = pf.las_json(Path.home() / '.claude' / 'settings.json') or {}
    return (os.environ.get('NWP_BREV_MODELL') or anv.get('model') or 'opus[1m]',
            os.environ.get('NWP_BREV_EFFORT') or anv.get('effortLevel') or 'high')


def sek(ms):
    return ('%.1f' % (ms / 1000.0)).replace('.', ',') if ms is not None else None


def mb(byte):
    return ('%.1f' % (byte / 1e6)).replace('.', ',') if byte is not None else None


def storlek(byte):
    if byte is None:
        return None
    return '%d kB' % round(byte / 1000) if byte < 1e6 else '%s MB' % mb(byte)


def fakta_ur(pro, post):
    """Faktarader med varje siffra modellen får använda, i den form den ska stå i brevet, och källan."""
    sig = pro.get('signaler') or {}
    rader = []

    def rad(text, kalla):
        rader.append('- %s [%s]' % (text, kalla))

    if sig.get('lcpMs') is not None:
        rad('Startsidan visar sitt största innehåll efter %s s på mobil' % sek(sig['lcpMs']), 'lighthouse.json LCP %d ms' % sig['lcpMs'])
    if sig.get('prestanda') is not None:
        rad('Lighthouse ger startsidan %d av 100 i prestanda på mobil' % sig['prestanda'], 'lighthouse.json')
    if sig.get('vikt_byte'):
        rad('Startsidan väger %s' % storlek(sig['vikt_byte']), 'lighthouse total-byte-weight')
    if sig.get('axe_allvarliga'):
        rad(('%d allvarligt tillgänglighetsfel på startsidan' if sig['axe_allvarliga'] == 1 else '%d allvarliga tillgänglighetsfel på startsidan') % sig['axe_allvarliga'], 'axe.json')
    if sig.get('sma_ytor'):
        rad(('%d klickyta på mobilen är mindre än 24 px' if sig['sma_ytor'] == 1 else '%d klickytor på mobilen är mindre än 24 px') % sig['sma_ytor'], 'STIL.json')
    if sig.get('spill_390'):
        rad('Innehållet går utanför skärmen på en mobil (390 px bred)', 'INSPEKTION.json')
    if sig.get('viewport_meta') is False:
        rad('Sidan saknar viewport-inställning och visas som en krympt datorsida på mobil', 'startsidans HTML')
    if sig.get('description_saknas'):
        rad('Startsidan saknar beskrivning för sökresultatet', 'startsidans HTML')
    if sig.get('title_saknas'):
        rad('Startsidan saknar titel', 'startsidans HTML')
    elif sig.get('title_langd') and sig['title_langd'] > 60:
        rad('Titeln är %d tecken och klipps i sökresultatet' % sig['title_langd'], 'startsidans HTML')
    if sig.get('valkommen_rubrik'):
        rad('Rubriken säger Välkommen i stället för vad ni gör och var', 'startsidans HTML')
    if sig.get('tel_lank_start') is False:
        rad('Telefonnumret går inte att trycka på från startsidan i mobilen', 'startsidans HTML')
    if sig.get('copyright_ar') and sig.get('copyright_gammal'):
        rad('Sidfoten anger %d' % sig['copyright_ar'], 'startsidans HTML')
    if sig.get('karusell'):
        rad('Startsidan har en bildkarusell', 'startsidans HTML')
    if sig.get('https') is False:
        rad('Sajten går utan https', 'sondering')
    if sig.get('lokal_schema_saknas'):
        rad('Ingen strukturerad data om verksamheten för sökmotorer', 'startsidans HTML')
    if sig.get('sidkarta_saknas'):
        rad('Ingen sidkarta', 'hamta_sajt')
    # poängens avdrag som inte redan står ovan, en rad per signal och aldrig utgångspunkten
    tackta = {'lcpMs', 'prestanda', 'vikt_byte', 'axe_allvarliga', 'sma_ytor', 'spill_390', 'viewport_meta', 'description_saknas', 'title_saknas',
              'title_langd', 'valkommen_rubrik', 'tel_lank_start', 'copyright_ar', 'copyright_gammal', 'karusell', 'https', 'lokal_schema_saknas', 'sidkarta_saknas'}
    for v in pro.get('varfor') or []:
        sg, t = v.get('signal'), v.get('varfor') or ''
        if not t or sg in tackta or t.startswith('utgångspunkt'):
            continue
        tackta.add(sg)
        rader.append('- %s%s [poäng: %s]' % (t[0].upper() + t[1:], (' (%s)' % v['varde']) if isinstance(v.get('varde'), (int, float)) and not isinstance(v.get('varde'), bool) else '', sg))
    return rader


def tillatna_tal(rader):
    ut = set(TILLATNA_TAL)
    for r in rader:
        r = re.sub(r'\(\d+\.\d+\)|\[poäng:[^\]]*\]', '', r)  # byggstandardens punkter (7.1) är inga mätvärden
        for t in TAL.findall(r):
            ut.add(t.replace(',', '.'))
            ut.add(t.replace('.', ','))
            if '.' in t or ',' in t:
                ut.add(t.split(',')[0].split('.')[0])
    return ut


def siffror_ok(text, tillatna):
    fel = [t for t in TAL.findall(text or '') if t not in tillatna and t.replace(',', '.') not in tillatna]
    return (not fel), fel


def prompt_text(post, pro, bas, fakta):
    bilder = [str(bas / 'diagnos' / 'inspektion' / f) for f in ('vy-390-forsta.png', 'vy-1440-forsta.png') if (bas / 'diagnos' / 'inspektion' / f).is_file()]
    egna = [str(p) for p in sorted((bas / 'kalla').glob('*.txt'))[:3]]
    url = (post.get('sajt') or {}).get('url') or ''
    return '\n'.join([
        'Skriv ett första brev från Nortropic (Luleå) till verksamheten nedan. Brevet bjuder in till ett möte på femton minuter där vi visar en skiss på hur deras webbplats kunde se ut. Du skriver bara ämnesrad, brevkropp och ett ringmanus; avsändare, avregistrering och underskrift lägger verktyget till.',
        '',
        'Verksamhet: %s (%s), %s. Webbplats: %s.' % (post.get('namn'), post.get('jurform_text') or 'juridisk form okänd', post.get('postort') or '', url),
        '',
        'Uppmätt, det enda du får hänvisa till; varje siffra i brevet ska stå på en rad här:',
        *(fakta or ['- (inga mätvärden; skriv bara utifrån skärmbilderna)']),
        '',
        'Skärmbilder av deras sajt, läs dem med Read och beskriv bara vad du ser:',
        *(['- ' + b for b in bilder] or ['- inga']),
        '',
        'Deras egna ord, för röst och vad de kallar sina tjänster (läs med Read):',
        *(['- ' + e for e in egna] or ['- inga']),
        '',
        'Regler: Svenska. Högst 120 ord i brevkroppen. Två eller tre iakttagelser, var och en knuten till en rad under Uppmätt eller till en skärmbild, i vardagliga ord ("mobilen laddar på 8 sekunder", "texten går utanför skärmen på mobilen", "sidan saknar beskrivning i sökresultatet"). Hitta aldrig på fakta, förevändningar, personer eller siffror; inget "jag letade efter …". Inga superlativ, inga löften om resultat, inga konkurrenter vid namn, inga länkar. Säg i första meningen vem vi är: Nortropic i Luleå bygger webbplatser åt lokala verksamheter. Sluta med ett konkret nästa steg: femton minuter, vi visar en skiss. Ingen inledande artighetsfras. Gå igenom texten med skillen humanizer (.claude/skills/humanizer/SKILL.md) innan du svarar; regeln mot slop är kunskap/copy-kontroll.md.',
        'fakta: en rad per iakttagelse med påståendet som det står i brevet och källan. ringmanus: samma iakttagelser som talade meningar för ett samtal under en minut, högst 90 ord.',
        'Du ändrar inga filer. Svara enligt schemat.',
    ]) + '\n'


def kontrollera(res, fakta):
    text = res.get('text') or ''
    ord_ = len(re.findall(r'\S+', text))
    ok_tal, fel_tal = siffror_ok(text, tillatna_tal(fakta))
    fynd, _ = ck.kontrollera_fil(Path('brev.md'), text, [])
    return {'ord': ord_, 'siffror_ok': ok_tal, 'siffror_fel': fel_tal, 'copy_fynd': fynd,
            'ok': ord_ <= 120 and ok_tal and bool(text.strip()) and bool((res.get('amne') or '').strip())}


def mottagartyp(epost):
    return 'roll' if ROLLER_RE.match((epost or '').split('@')[0].lower()) else 'person'


def skriv_brev(slug, kampanj, torr=False):
    poster = pf.las_register(kampanj)
    post = pf.hitta_post(poster, slug=slug)
    if not post:
        raise ValueError('ingen post med slug %s i kampanjen %s' % (slug, kampanj))
    bas = ROOT / 'underlag' / slug
    pro = pf.las_json(bas / 'PROSPEKT.json')
    if not pro:
        raise ValueError('ingen PROSPEKT.json för %s: analysera först' % slug)
    bdir = bas / 'brev'
    bdir.mkdir(parents=True, exist_ok=True)
    fakta = fakta_ur(pro, post)
    prompt = prompt_text(post, pro, bas, fakta)
    (bdir / 'PROMPT.txt').write_text(prompt, encoding='utf-8')
    modell, effort = modell_och_effort()
    upp = {'slug': slug, 'kampanj': kampanj, 'tid': pf.nu(), 'modell': modell, 'effort': effort, 'fakta': fakta}
    pf.skriv_json(bdir / 'UPPDRAG.json', upp)
    if torr:
        print(prompt)
        return 0
    for f in ('FEL.txt', 'svar.json'):
        (bdir / f).unlink(missing_ok=True)
    egen = pf.pagar_pid(bdir)
    if egen and egen != os.getpid():
        raise ValueError('ett brev skrivs redan (pid %d)' % egen)
    (bdir / 'PAGAR').write_text(str(os.getpid()))
    try:
        claude = shutil.which('claude') or str(Path.home() / '.local' / 'bin' / 'claude')
        args = [claude, '-p', '--max-turns', '40', '--permission-mode', 'dontAsk', '--output-format', 'json',
                '--setting-sources', 'project,local', '--strict-mcp-config', '--model', modell, '--effort', effort,
                '--json-schema', SCHEMA.read_text(encoding='utf-8'), '--allowedTools', *VERKTYG, '--disallowedTools', *NEKAS]
        frist = int(os.environ.get('NWP_BREV_FRIST') or 600)
        with open(bdir / 'svar.json', 'wb') as ut, open(bdir / 'stderr.log', 'wb') as err:
            try:
                subprocess.run(args, input=prompt.encode(), stdout=ut, stderr=err, cwd=str(ROOT), env=ren_miljo(), timeout=frist)
            except subprocess.TimeoutExpired:
                (bdir / 'FEL.txt').write_text('modellen svarade inte inom %d s\n' % frist, encoding='utf-8')
                return 1
        svar = pf.las_json(bdir / 'svar.json') or {}
        res = svar.get('structured_output')
        if not isinstance(res, dict):
            (bdir / 'FEL.txt').write_text('inget giltigt svar (%s): %s\n' % (svar.get('subtype'), str(svar.get('result'))[:300]), encoding='utf-8')
            return 1
        k = kontrollera(res, fakta)
        if not k['ok']:
            (bdir / 'FEL.txt').write_text(('påhittad siffra: %s\n' % ', '.join(k['siffror_fel'])) if k['siffror_fel'] else ('brevet är %d ord, över 120\n' % k['ord']), encoding='utf-8')
            return 1
        epost = post.get('epost') or ''
        brev = {'schema': 1, 'slug': slug, 'kampanj': kampanj,
                'utkast': {'amne': res['amne'].strip(), 'text': res['text'].strip(), 'fakta': res.get('fakta') or [], 'ringmanus': (res.get('ringmanus') or '').strip(),
                           'skapad': pf.nu(), 'modell': modell, 'effort': effort, 'session': svar.get('session_id'), 'turer': svar.get('num_turns')},
                'kontroll': {'copy_fynd': k['copy_fynd'], 'siffror_ok': True, 'ord': k['ord']},
                'mottagare': {'epost': epost, 'typ': mottagartyp(epost) if epost else None, 'bekraftad_person': False}}
        pf.skriv_json(bas / 'BREV.json', brev)
        pf.satt_status(kampanj, slug, 'utkast', brev_tid=brev['utkast']['skapad'])
        pf.logga(kampanj, 'brev_utkast', slug=slug, ord=k['ord'], turer=svar.get('num_turns'))
        return 0
    finally:
        pf.pagar_slapp(bdir)


def main(argv=None):
    p = argparse.ArgumentParser(prog='brev', description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    p.add_argument('--kampanj', required=True)
    p.add_argument('--torr', action='store_true')
    a = p.parse_args(argv)
    if not pf.SLUG.match(a.slug):
        print('ogiltig slug', file=sys.stderr)
        return 2
    try:
        return skriv_brev(a.slug, a.kampanj, a.torr)
    except ValueError as e:
        print('fel: %s' % e, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
