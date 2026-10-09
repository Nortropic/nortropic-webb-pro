-- Förfrågningar från kundsajtens formulär (worker/index.js). Ärendet och dess utkorgsrad skrivs i en transaktion;
-- bilagan ligger privat i R2 under nyckeln i kolumnen bilaga. gallras anger när ärendet ska tas bort (GALLRING_DAGAR).
CREATE TABLE IF NOT EXISTS forfragningar (
  id TEXT PRIMARY KEY,
  nyckel TEXT NOT NULL UNIQUE,
  mottagen TEXT NOT NULL,
  namn TEXT NOT NULL,
  telefon TEXT NOT NULL,
  meddelande TEXT NOT NULL,
  bilaga TEXT,
  bilaga_typ TEXT,
  bilaga_storlek INTEGER,
  bilaga_namn TEXT,
  gallras TEXT NOT NULL
);

-- Aviseringen: vantar → skickar → accepterad | fel. "skickar" utan slutläge är ett osäkert utfall som stäms av mot
-- mejltjänsten före ett nytt försök.
CREATE TABLE IF NOT EXISTS utkorg (
  forfragan TEXT PRIMARY KEY REFERENCES forfragningar(id),
  status TEXT NOT NULL CHECK (status IN ('vantar', 'skickar', 'accepterad', 'fel')),
  forsok INTEGER NOT NULL DEFAULT 0,
  mejl_id TEXT,
  fel TEXT,
  uppdaterad TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS utkorg_status ON utkorg (status);
CREATE INDEX IF NOT EXISTS forfragningar_gallras ON forfragningar (gallras);
