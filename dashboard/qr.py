"""QR-kod som SVG, ritad lokalt utan bibliotek eller tredjepartsanrop (dashboarden visar sajtens adress på det egna
nätverket så att ägaren kan öppna den i telefonen). Byte-läge, felrättning M, version 1–10 (upp till 213 byte),
masken med lägst straff. Efter ISO/IEC 18004; tabellerna och ordningen följer Project Nayuki:s beskrivning.

    from qr import svg
    svg('http://192.168.1.23:51234/')
"""

ECC_PER_BLOCK = [None, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26]   # nivå M, version 1–10
BLOCK = [None, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5]


def _raw_moduler(ver):
    n = (16 * ver + 128) * ver + 64
    if ver >= 2:
        a = ver // 7 + 2
        n -= (25 * a - 10) * a - 55
        if ver >= 7:
            n -= 36
    return n


def _data_kodord(ver):
    return _raw_moduler(ver) // 8 - ECC_PER_BLOCK[ver] * BLOCK[ver]


def _gf_mul(x, y):
    z = 0
    for i in range(7, -1, -1):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def _rs_delare(grad):
    res = [0] * (grad - 1) + [1]
    rot = 1
    for _ in range(grad):
        for j in range(grad):
            res[j] = _gf_mul(res[j], rot)
            if j + 1 < grad:
                res[j] ^= res[j + 1]
        rot = _gf_mul(rot, 0x02)
    return res


def _rs_rest(data, delare):
    res = [0] * len(delare)
    for b in data:
        f = b ^ res.pop(0)
        res.append(0)
        for i, c in enumerate(delare):
            res[i] ^= _gf_mul(c, f)
    return res


def _kodord(data):
    for ver in range(1, 11):
        kap = _data_kodord(ver)
        langd = 4 + (8 if ver <= 9 else 16) + 8 * len(data)
        if langd <= kap * 8:
            break
    else:
        raise ValueError('för lång för version 10 (högst 213 byte)')
    bitar = []

    def lagg(v, n):
        bitar.extend((v >> i) & 1 for i in range(n - 1, -1, -1))
    lagg(0b0100, 4)
    lagg(len(data), 8 if ver <= 9 else 16)
    for b in data:
        lagg(b, 8)
    lagg(0, min(4, kap * 8 - len(bitar)))
    lagg(0, (-len(bitar)) % 8)
    ord_ = [int(''.join(map(str, bitar[i:i + 8])), 2) for i in range(0, len(bitar), 8)]
    fyll = 0xEC
    while len(ord_) < kap:
        ord_.append(fyll)
        fyll ^= 0xEC ^ 0x11
    # block och felrättning, sedan sammanflätning
    antal, ecc = BLOCK[ver], ECC_PER_BLOCK[ver]
    raw = _raw_moduler(ver) // 8
    korta, kort_langd = antal - raw % antal, raw // antal
    delare, block, k = _rs_delare(ecc), [], 0
    for i in range(antal):
        d = ord_[k:k + kort_langd - ecc + (0 if i < korta else 1)]
        k += len(d)
        e = _rs_rest(d, delare)
        if i < korta:
            d = d + [0]
        block.append(d + e)
    ut = []
    for i in range(len(block[0])):
        for j, b in enumerate(block):
            if i != kort_langd - ecc or j >= korta:
                ut.append(b[i])
    return ver, ut


def _justering(ver):
    if ver == 1:
        return []
    a = ver // 7 + 2
    steg = (ver * 8 + a * 3 + 5) // (a * 4 - 4) * 2
    storlek = ver * 4 + 17
    pos = [storlek - 7 - i * steg for i in range(a - 1)]
    return [6] + sorted(pos)


def _matris(ver, kodord, mask):
    n = ver * 4 + 17
    m = [[False] * n for _ in range(n)]
    funk = [[False] * n for _ in range(n)]

    def satt(x, y, v):
        m[y][x] = v
        funk[y][x] = True
    for i in range(n):
        satt(6, i, i % 2 == 0)
        satt(i, 6, i % 2 == 0)
    for cx, cy in ((3, 3), (n - 4, 3), (3, n - 4)):
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                x, y = cx + dx, cy + dy
                if 0 <= x < n and 0 <= y < n:
                    d = max(abs(dx), abs(dy))
                    satt(x, y, d not in (2, 4))
    pos = _justering(ver)
    for i, a in enumerate(pos):
        for j, b in enumerate(pos):
            if (i == 0 and j == 0) or (i == 0 and j == len(pos) - 1) or (i == len(pos) - 1 and j == 0):
                continue
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    satt(a + dx, b + dy, max(abs(dx), abs(dy)) != 1)
    # formatbitar (nivå M = 00) och den mörka modulen
    data = (0 << 3) | mask
    rest = data
    for _ in range(10):
        rest = (rest << 1) ^ ((rest >> 9) * 0x537)
    bit = ((data << 10) | rest) ^ 0x5412
    b = lambda i: (bit >> i) & 1 == 1  # noqa: E731
    for i in range(6):
        satt(8, i, b(i))
    satt(8, 7, b(6))
    satt(8, 8, b(7))
    satt(7, 8, b(8))
    for i in range(9, 15):
        satt(14 - i, 8, b(i))
    for i in range(8):
        satt(n - 1 - i, 8, b(i))
    for i in range(8, 15):
        satt(8, n - 15 + i, b(i))
    satt(8, n - 8, True)
    if ver >= 7:
        rest = ver
        for _ in range(12):
            rest = (rest << 1) ^ ((rest >> 11) * 0x1F25)
        vb = (ver << 12) | rest
        for i in range(18):
            v = (vb >> i) & 1 == 1
            a, c = n - 11 + i % 3, i // 3
            satt(a, c, v)
            satt(c, a, v)
    # data i sicksack, två kolumner i taget från höger
    i, hoger = 0, n - 1
    while hoger >= 1:
        if hoger == 6:
            hoger = 5
        for vert in range(n):
            for j in range(2):
                x = hoger - j
                upp = ((hoger + 1) & 2) == 0
                y = n - 1 - vert if upp else vert
                if not funk[y][x] and i < len(kodord) * 8:
                    m[y][x] = (kodord[i >> 3] >> (7 - (i & 7))) & 1 == 1
                    i += 1
        hoger -= 2
    villkor = [lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0, lambda x, y: x % 3 == 0,
               lambda x, y: (x + y) % 3 == 0, lambda x, y: (x // 3 + y // 2) % 2 == 0,
               lambda x, y: x * y % 2 + x * y % 3 == 0, lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0,
               lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0][mask]
    for y in range(n):
        for x in range(n):
            if not funk[y][x] and villkor(x, y):
                m[y][x] = not m[y][x]
    return m


def _straff(m):
    n, p = len(m), 0
    rader = [''.join('1' if v else '0' for v in r) for r in m]
    kolumner = [''.join(r[x] for r in rader) for x in range(n)]
    for linje in rader + kolumner:
        lopp, forra = 0, None
        for c in linje + 'x':
            if c == forra:
                lopp += 1
            else:
                if lopp >= 5:
                    p += 3 + (lopp - 5)
                forra, lopp = c, 1
        for monster in ('10111010000', '00001011101'):
            p += 40 * linje.count(monster)
    for y in range(n - 1):
        for x in range(n - 1):
            if m[y][x] == m[y][x + 1] == m[y + 1][x] == m[y + 1][x + 1]:
                p += 3
    morka = sum(r.count('1') for r in rader)
    p += 10 * (abs(morka * 20 - n * n * 10) // (n * n))
    return p


def matris(text):
    ver, kodord = _kodord(text.encode('utf-8'))
    return min((_matris(ver, kodord, mask) for mask in range(8)), key=_straff)


def svg(text, modul=6, kant=4):
    m = matris(text)
    n = len(m)
    sida = (n + 2 * kant) * modul
    vag = ''.join('M%d %dh%dv%dh-%dz' % ((x + kant) * modul, (y + kant) * modul, modul, modul, modul)
                  for y in range(n) for x in range(n) if m[y][x])
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" '
            'aria-label="QR-kod till %s"><rect width="100%%" height="100%%" fill="#fff"/><path d="%s" fill="#000"/></svg>'
            % (sida, sida, sida, sida, text.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;'), vag))
