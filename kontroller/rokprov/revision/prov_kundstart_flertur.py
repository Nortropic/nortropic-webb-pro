"""Fem syntetiska utvecklingsfall med skriptad modelldubbel, aldrig intervju-eval.

Facit stannar i provet. Modellingången får bara Kundstarts vanliga ärendeobjekt.
Mänsklig användarprövning och ett nytt, orört sluturval återstår.
"""
import contextlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import korregister
import kundstart as ks
import kundstart_beredning as kb
import kundstart_fortsatt as kf
import kundstart_modell as km


# Kundens repliker är indata, förväntningarna separat testfacit. Alla namn och
# uppgifter är uppfunna för provet; inget är hämtat från privat kundmaterial.
FALL = (
    {'id': 'tjanst', 'repliker': ['Vi vill visa vår service. Ingen nätbetalning nu, kanske senare.',
        'Rättelse: bara service, ingen försäljning.'],
     'uppgifter': [('erbjudande', 'A', 'Service utan försäljning.', 'onskemal'),
                   ('betalning', 'F', 'Ingen nätbetalning i uppdraget.', 'avstatt'),
                   ('senare', 'F', 'Möjlig nätbetalning längre fram.', 'framtida')]},
    {'id': 'bokning', 'repliker': ['Besökaren behöver boka en ledig tid i vårt befintliga system.',
        'Jag vet inte vilket konto som har kopplingsstöd. Ersätt inte bokningen med ett kontaktformulär.'],
     'uppgifter': [('mal', 'B', 'Boka ledig tid i befintligt system.', 'onskemal'),
                   ('konto', 'F', 'Kontots kopplingsstöd är inte känt.', 'okant')],
     'integration': {'id': 'tid', 'behov': 'Boka en ledig tid.', 'lage': 'onskemal'}},
    {'id': 'order', 'repliker': ['Beställningen behöver granskas av oss innan ett pris kan lämnas.',
        'Ingen omedelbar betalning. Leveranstiden beror på vår kontroll.'],
     'uppgifter': [('mal', 'F', 'Beställningsunderlag granskas manuellt före offert.', 'onskemal'),
                   ('betala', 'F', 'Ingen direktbetalning.', 'avstatt'),
                   ('tid', 'I', 'Leveranstid är okänd tills underlaget granskats.', 'okant')]},
    {'id': 'migrering', 'repliker': ['Vi har en befintlig sida och vill behålla viktiga adresser och innehåll.',
        'Den gamla kontaktpersonen är fel. Byt inte domän och publicera inget innan vår kontroll.'],
     'uppgifter': [('bevara', 'C', 'Inventera och bevara viktiga adresser och innehåll.', 'onskemal'),
                   ('doman', 'H', 'Inget domänbyte ingår.', 'avstatt'),
                   ('kontakt', 'E', 'Äldre kontaktuppgift behöver rättas.', 'onskemal')]},
    {'id': 'liten', 'repliker': ['Vi behöver bara ändra texten om tillgänglighet på en sida.',
        'Behåll formgivningen. Vi vill inte börja om med hela sajten.'],
     'uppgifter': [('omfattning', 'A', 'En begränsad textändring på en sida.', 'onskemal'),
                   ('design', 'D', 'Behåll befintlig formgivning.', 'kundval'),
                   ('ny_sajt', 'I', 'Inget nytt helbygge beställs.', 'avstatt')]},
)


class Flertur(unittest.TestCase):
    def test_fem_verksamhetslogiker_bevaras_genom_rattelse_och_overlamning(self):
        with korregister.egen_tmp_med('nwp-kallgap-', 'fem syntetiska Kundstartförlopp') as tmp:
            for fall in FALL:
                with self.subTest(fall=fall['id']):
                    root = Path(tmp).resolve() / fall['id']
                    db = ks.Lager(root / 'underlag/kundstart')
                    slug = 'prov-' + fall['id']
                    eid, token = db.skapa(slug, 'Syntetisk kundroll', modellbudget=30)
                    def gor(slag, data):
                        d = db.las(eid, token)
                        return db.kundhandling(eid, token, d['revision'], ks.id_(), slag, data)
                    def modellsvar():
                        jobb = db.ta_jobb('skriptad-modelldubbel')
                        self.assertEqual(jobb['arende'], eid)
                        kontext = km.kontext(jobb['dokument'])
                        self.assertNotIn('FACIT-HEMLIGT-I-PROVET', json.dumps(kontext))
                        kallor = list(ks.kundkallor(jobb['dokument']))
                        values = {'namn': 'Syntetisk Exempelverksamhet', 'rackvidd': {'typ': 'nationell'}, 'kontaktvagar': [], 'tjanster': ['Service']}
                        # Detta är en explicit dubbel. Ingen tolkning eller val
                        # av nästa fråga tillskrivs en verklig modell.
                        return db.modellsvar(jobb, {'text': 'Skriptad provtur. Rätta i uppdragsöversikten.',
                            'forslag': [], 'fragor': [], 'verksamhet': {'varden': values, 'kallor': {k: kallor for k in values}}})
                    gor('meddelande', {'text': 'Syntetisk Exempelverksamhet arbetar nationellt med service.'})
                    for text in fall['repliker']:
                        gor('meddelande', {'text': text})
                        self.assertTrue(modellsvar())
                    for kid, amne, text, lage in fall['uppgifter']:
                        gor('uppgift', {'id': kid, 'amne': amne, 'text': text, 'lage': lage})
                    if fall.get('integration'):
                        gor('integrationsbehov', fall['integration'])
                    self.assertTrue(modellsvar())
                    d = db.las(eid, token)
                    d = gor('bekrafta_verksamhet', {'sha256': d['verksamhet_forslag']['sha256']})
                    kvitto = kb.overlamna(db, eid, d['revision'], 'overlamning-' + fall['id'], root)
                    u = root / 'underlag' / slug
                    body = json.loads((u / 'KUNDSTART.json').read_text())
                    self.assertTrue(kvitto['aktuell'])
                    for kid, amne, text, lage in fall['uppgifter']:
                        self.assertEqual(body['uppgifter'][kid]['text'], text)
                        self.assertEqual(body['uppgifter'][kid]['bestallning'], lage)
                    self.assertFalse(body['helbygge_tillatet'])
                    self.assertEqual(body['bestallning']['status'], 'utkast')
                    self.assertFalse((u / 'UPPDRAG.md').exists())
                    if fall.get('integration'):
                        integ = body['integrationer']['tid']
                        self.assertFalse(kf.integration_klar(integ))
                        self.assertEqual(integ['utredning']['konto']['status'], 'okant')
                        self.assertEqual(integ['behov'], 'Boka en ledig tid.')
                    # Ett aktuellt erbjudande accepteras separat. Samma uppgift
                    # i nytt operations-id ändrar inte omfattningen; ny gör det.
                    gor('forfragan', {})
                    d = db.las(eid, token)
                    off = db.erbjudande(eid, d['revision'], 'Syntetiskt avgränsat uppdrag.', 'Inget leveransdatum utlovas.', 'Intern provroll')
                    gor('acceptera', {'erbjudande': off['id']})
                    kid, amne, text, lage = fall['uppgifter'][0]
                    d = gor('uppgift', {'id': kid, 'amne': amne, 'text': text, 'lage': lage})
                    self.assertTrue(d['bestallning']['aktuell'])
                    d = gor('uppgift', {'id': kid, 'amne': amne, 'text': text + ' Syntetiskt nytt behov.', 'lage': lage})
                    self.assertFalse(d['bestallning']['aktuell'])
                    self.assertFalse(kb.aktuell(db, u))
                    # Ingen verklig adapter har rapporterat tokens eller kostnad.
                    self.assertEqual(d['modell']['status'], 'ko')


if __name__ == '__main__':
    unittest.main()
