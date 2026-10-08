// Tillägg till resformatet. CSS behåller sitt äldre första-synliga-beteende.
// Semantik är strikt: namn/etikett och vid behov ett uttryckligt avgränsat område.
export function hitta(rot, val, djup = 0) {
  if (typeof val === 'string' && val.trim()) return rot.locator(val).filter({ visible: true }).first();
  if (djup > 8 || !val || typeof val !== 'object' || Array.isArray(val)) throw new Error('ogiltig semantisk väljare');
  const keys = Object.keys(val);
  const roll = typeof val.roll === 'string' && val.roll.trim() && typeof val.namn === 'string' && val.namn.trim();
  const etikett = typeof val.etikett === 'string' && val.etikett.trim();
  if (Boolean(roll) === Boolean(etikett) || keys.some(k => !(roll ? ['roll','namn','inom'] : ['etikett','inom']).includes(k))) {
    throw new Error('väljare kräver roll och namn, eller etikett, samt valfritt inom');
  }
  if (Object.hasOwn(val, 'inom') && (!val.inom || typeof val.inom !== 'object' || Array.isArray(val.inom))) throw new Error('väljare inom kräver ett semantiskt område');
  const scope = Object.hasOwn(val, 'inom') ? hitta(rot, val.inom, djup + 1) : rot;
  return (roll ? scope.getByRole(val.roll, { name: val.namn, exact: true }) : scope.getByLabel(val.etikett, { exact: true })).filter({ visible: true });
}

export async function synligt(rot, val) {
  const loc = hitta(rot, val);
  if (typeof val !== 'string') {
    // Pröva området för sig: två likadana regioner ska inte döljas av en unik knapp längre ned.
    if (Object.hasOwn(val, 'inom')) await synligt(rot, val.inom);
    const antal = await loc.count();
    if (antal !== 1) throw new Error(`semantisk väljare har ${antal} träffar; använd ett unikt namn eller avgränsa med inom: ${JSON.stringify(val)}`);
  }
  return loc;
}
