#!/usr/bin/env python3
"""Helbyggets MCP-argument, med samma nyckelhantering och kundvakt som ateljén.

Fyra designtjänster konfigureras normalt. NWP_MCP_CONFIG=av stänger anslutningarna för
isolerade mekanikprov; en av flödets fyra repolokala mallar väljer bara den tjänsten.
Det äldre Inspo-försöket har ingen kundvakt och kan inte öppnas i den här vägen.
Inga MCP-namn läggs i allowedTools: dontAsk och den prövande kroken gäller varje anrop.
Sandlådans inställningar bevaras. Autentiseringskonfigurationen skrivs med 0600;
nycklar exponeras inte i modellprocessens argument eller miljö. Klienten läser konfigurationen.

    byggmcp.py <slug> <NWP_MCP_CONFIG eller tomt> <sandbox-settings-json>

Skriver NUL-avgränsade argument för kor.sh. Anropar ingen tjänst eller modell.
"""
import copy
import json
import re
from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atelje
import kundvakt


def kompetensbevis(kund, korning):
    """Körningens egen session, bunden i START före modellen; inga nya modellanrop.

    Ett typfel, en främmande identitet, ett saknat/trasigt transkript eller ett
    uteblivet/felmarkerat slutresultat är en brist.
    Beviset ligger i slutposten, aldrig i en fil som byggaren själv får förklara giltig.
    Bara huvudsessionen observeras här; underagenters egna transkript ingår inte.
    Läsordning gäller första observerade Write/Edit/MultiEdit, inte Bash-skrivningar.
    """
    import kompetens
    k = Path(kund)
    ut = {'pass': 'helbygge', 'korning': korning, 'session_id': None, 'kvitto': None, 'brister': []}
    try:
        if not isinstance(korning, str) or not re.fullmatch(r'[0-9A-Za-z][0-9A-Za-z_-]{0,63}', korning):
            raise ValueError('körningens identitet saknas eller är ogiltig')
        f = k / 'korningar' / korning / 'START.json'
        if f.is_symlink() or f.parent.is_symlink() or f.parent.parent.is_symlink():
            raise ValueError('körningens startpost är länkad')
        start = json.loads(f.read_text(encoding='utf-8'))
        if not isinstance(start, dict) or start.get('korning') != korning:
            raise ValueError('startposten gäller inte körningen')
        sid = start.get('session_id')
        if not isinstance(sid, str) or str(uuid.UUID(sid)) != sid or uuid.UUID(sid).version != 4:
            raise ValueError('startposten saknar ett giltigt sessions-id')
        ut['session_id'] = sid
        logg = k / ('korning-%s.jsonl' % korning)
        if logg.is_symlink():
            raise ValueError('körningens logg är länkad')
        init, resultat = [], []
        with logg.open(encoding='utf-8') as fh:
            for rad in fh:
                if not rad.strip():
                    continue
                try:
                    post = json.loads(rad)
                except ValueError:
                    # kor.sh lägger även stderr här. Diagnostik är inte en händelse,
                    # men en bruten JSON-händelse får inte döljas som diagnostik.
                    if rad.lstrip().startswith('{'):
                        raise ValueError('körningens händelselogg är ofullständig')
                    continue
                if not isinstance(post, dict):
                    raise ValueError('körningens händelse har fel format')
                ar_init = post.get('type') == 'system' and post.get('subtype') == 'init'
                if ar_init or post.get('type') == 'result':
                    identitet = post.get('session_id')
                    if not isinstance(identitet, str) or identitet != sid:
                        raise ValueError('körningens logg och startpost har olika sessions-id')
                    if ar_init:
                        if resultat:
                            raise ValueError('körningens början följde efter avslutet')
                        init.append(post)
                    else:
                        if not init:
                            raise ValueError('körningens avslut saknar början')
                        resultat.append(post)
                elif resultat:
                    raise ValueError('en händelse följde efter slutresultatet')
        if len(init) != 1 or len(resultat) != 1:
            raise ValueError('körningens början eller avslut är inte entydigt observerat')
        if resultat[0].get('subtype') != 'success' or resultat[0].get('is_error') is not False:
            raise ValueError('körningens slutresultat är inte lyckat')
        import bildkedja
        transkript = bildkedja.transkript(sid)
        if transkript is None:
            raise ValueError('sessionens transkript saknas')
        antal = 0
        with transkript.open(encoding='utf-8') as fh:
            for rad in fh:
                if not rad.strip():
                    continue
                if not isinstance(json.loads(rad), dict):
                    raise ValueError('sessionens transkript har fel format')
                antal += 1
        if not antal:
            raise ValueError('sessionens transkript är tomt')
        kv = kompetens.kvitto([sid], 'helbygge', skrivprefix='kunder/%s/sajt/' % k.name)
        ut.update(kvitto=kv, brister=kompetens.kravbrister(kv, 'helbygge'))
    except Exception:  # noqa: BLE001 — även ett observationsfel nekar, aldrig godkännande utan kvitto
        # Undantagens strängar kan bära privat logginnehåll. Beskedet ger bara kontraktet som brast.
        ut['brister'] = ['helbyggets session eller kompetensbevis kunde inte bindas till körningen']
    ut['uppfyllt'] = not ut['brister']
    return ut


def argument(slug, val, settings):
    if not atelje.SLUG.fullmatch(slug):
        raise ValueError('ogiltig slug')
    if not isinstance(settings, dict):
        raise ValueError('inställningarna måste vara ett objekt')
    ut = copy.deepcopy(settings)
    bas = atelje.ROOT / 'kontroller' / 'mcp'
    val = str(val or '').strip()
    namn = ['refero', 'mobbin', 'motion', '21st']
    if val == 'av':
        namn = []
    elif val:
        p = Path(val).resolve(strict=True)
        giltiga = {(bas / (n + '.json')).resolve(): n for n in namn}
        if p not in giltiga:
            raise ValueError('NWP_MCP_CONFIG är inte en av flödets fyra skyddade designtjänster; Inspo kräver en egen prövad kundvakt')
        namn = [giltiga[p]]
    filer = []
    if namn:
        for n in namn:
            p = atelje.refero_mcp_fil() if n == 'refero' else atelje.tjugoforsta_mcp_fil() if n == '21st' else str(bas / (n + '.json'))
            if not Path(p).is_file():
                raise ValueError('MCP-konfigurationen saknas för %s' % n)
            filer.append(p)
        skydd = json.loads(kundvakt.installningar(slug, atelje.UNDERLAG, rot=atelje.ROOT))
        for typ, poster in skydd['hooks'].items():
            ut.setdefault('hooks', {}).setdefault(typ, []).extend(poster)
    args = ['--settings', json.dumps(ut, ensure_ascii=False)]
    if filer:
        args += ['--mcp-config', *filer]
    return args


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if len(a) != 3:
        print('byggmcp behöver slug, konfigval och inställningarna', file=sys.stderr)
        return 2
    try:
        args = argument(a[0], a[1], json.loads(a[2]))
    except (OSError, ValueError, TypeError, AttributeError, KeyError):
        # Aldrig en nyckel, ett konfigurationsinnehåll eller den fulla settings-strängen i ett fel.
        print('helbyggets MCP-konfiguration eller kundvakt kunde inte förberedas; kontrollera de repolokala mallarna och konfigvalet', file=sys.stderr)
        return 2
    sys.stdout.buffer.write(b'\0'.join(x.encode('utf-8') for x in args) + b'\0')
    return 0


if __name__ == '__main__':
    sys.exit(main())
