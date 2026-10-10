-- Överföringen till verksamhetens kundregister (K10, katalogens k10-pipedrive-lead), bara när kunden valt det: en rad per
-- ärende. skickar → klar | fel; "skickar" utan slutläge är ett osäkert utfall (kundregistret har ingen idempotensnyckel)
-- som stäms av i kundregistret, aldrig ett skäl att skicka igen i blindo. person_id och lead_id sparas efter varje steg,
-- så att avstämningen ser hur långt överföringen kom. Raden tas bort med ärendet vid gallringen; det som finns i
-- kundregistret är verksamhetens och gallras där.
CREATE TABLE IF NOT EXISTS kundregister (
  forfragan TEXT PRIMARY KEY REFERENCES forfragningar(id),
  status TEXT NOT NULL CHECK (status IN ('skickar', 'klar', 'fel')),
  person_id TEXT,
  lead_id TEXT,
  forsok INTEGER NOT NULL DEFAULT 0,
  fel TEXT,
  uppdaterad TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS kundregister_status ON kundregister (status);
