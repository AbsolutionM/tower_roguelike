#!/usr/bin/env python3
"""Aktive Palette: 256 Farben in 32 Rampen zu je 8 Stufen (dunkel -> hell),
seit 26.09.2026. Vorlage ist Sprites/Character/cowboy/Front1.png - dort hat
der Nutzer die Palette bereits umgesetzt.

Aus diesem Frame ist die gewuenschte Zuordnung abgelesen (Pixel fuer Pixel
gegen die alte Fassung gestellt):

    Poncho    b4202a -> e45c5f, 73172d -> b63c35, 3b1725 -> 82211d   (Rampe 9)
    Haut      f5a097 -> fbaa84, ba756a -> d58d6b, 8e5252 -> ad6e51   (Rampe 2)
    Hut/Leder 796755 -> c0a588, 5a4e44 -> 9e8a6e, 423934 -> 5e4646   (Rampe 12)
    Blau      285cc4 -> 5274c5, 143464 -> 2d3d72                     (Rampe 29)
    Gold      f9a31b -> ffb108, ffd541 -> ffcf05                     (Rampe 31)
    Weiss     ffffff -> cdd2da                                       (Rampe 0)

palette_anpassen() setzt alles auf diese Palette: erst ueber die
Handzuordnungen (AAP-64 und die vorher benutzte Splendor-Reihe), sonst
ueber den naechsten Nachbarn in CIE-Lab. Frueher: AAP-Splendor128, davor
Duel (tools/duel.py), davor AAP-64.
"""

import math

PALETTE = """000000 222323 434549 626871 828b98 a6aeba cdd2da f5f7fa
625d54 857565 9e8c79 aea189 bbafa4 ccc3b1 eadbc9 fff3d6
583126 733d3b 885041 9a624c ad6e51 d58d6b fbaa84 ffce7f
002735 003850 004d5e 0b667f 006f89 328ca7 24aed6 88d6ff
662b29 94363a b64d46 cd5e46 e37840 f99b4e ffbc4e ffe949
282b4a 3a4568 615f84 7a7799 8690b2 96b2d9 c7d6ff c6ecff
002219 003221 174a1b 225918 2f690c 518822 7da42d a6cc34
181f2f 23324d 25466b 366b8a 318eb8 41b2e3 52d2ff 74f5fd
1a332c 2f3f38 385140 325c40 417455 498960 55b67d 91daa1
5e0711 82211d b63c35 e45c5f ff7676 ff9ba8 ffbbc7 ffdbff
2d3136 48474d 5b5c69 73737f 848795 abaebe bac7db ebf0f6
3b303c 5a3c45 8a5258 ae6b60 c7826c d89f75 ecc581 fffaab
31222a 4a353c 5e4646 725a51 7e6c54 9e8a6e c0a588 ddbf9a
2e1026 49283d 663659 975475 b96d91 c178aa db99bf f8c6da
002e49 004051 005162 006b6d 008279 00a087 00bfa3 00deda
453125 614a3c 7e6144 997951 b29062 cca96e e8cb82 fbeaa3
5f0926 6e2434 904647 a76057 bd7d64 ce9770 edb67c edd493
323558 4a5280 64659d 7877c1 8e8ce2 9c9bef b8aeff dcd4ff
431729 712b3b 9f3b52 d94a69 f85d80 ff7daf ffa6c5 ffcdff
49251c 633432 7c4b47 98595a ac6f6e c17e7a d28d7a e59a7c
202900 2f4f08 495d00 617308 7c831e 969a26 b4aa33 d0cc32
622a00 753b09 854f12 9e6520 ba882e d1aa39 e8d24b fff64f
26233d 3b3855 56506f 75686e 917a7b b39783 cfaf8e fedfb1
1d2c43 2e3d47 394d3c 4c5f33 58712c 6b842d 789e24 7fbd39
372423 53393a 784c49 945d4f a96d58 bf7e63 d79374 f4a380
2d4b47 47655a 5b7b69 71957d 87ae8e 8ac196 a9d1c1 e0faeb
001b40 03315f 07487c 105da2 1476c0 4097ea 55b1f1 6dccff
554769 765d73 977488 b98c93 d5a39a ebbd9d ffd59b fdf786
1d1d21 3c3151 584a7f 7964ba 9585f1 a996ec baabf7 d1bdfe
262450 28335d 2d3d72 3d5083 5165ae 5274c5 6c82c4 8393c3
492129 5e414a 77535b 91606a ad7984 b58b94 d4aeaa ffe2cf
721c03 9c3327 bf5a3e e98627 ffb108 ffcf05 fff02b f7f4bf""".split()

# Die Rampen der Reihe nach - so heissen sie in den Generatoren.
RAMPEN = {
    'grau': 0, 'sand': 1, 'haut': 2, 'petrol': 3, 'feuer': 4, 'stahlblau': 5,
    'gruen': 6, 'eis': 7, 'moos': 8, 'rot': 9, 'zinn': 10, 'altholz': 11,
    'leder': 12, 'violett': 13, 'tuerkis': 14, 'holz': 15, 'wein': 16,
    'lavendel': 17, 'pink': 18, 'ocker': 19, 'oliv': 20, 'gold': 21,
    'daemmer': 22, 'waldgruen': 23, 'terrakotta': 24, 'salbei': 25,
    'himmel': 26, 'mauve': 27, 'nacht': 28, 'koenigsblau': 29, 'altrosa': 30,
    'glut': 31,
}

PALETTE_RGB = [(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)) for h in PALETTE]
PALETTE_SET = set(PALETTE_RGB)


def ton(rampe, stufe):
    """Eine Stufe aus einer benannten Rampe, 0 = dunkel .. 7 = hell."""
    return PALETTE[RAMPEN[rampe] * 8 + max(0, min(7, stufe))]


# --- AAP-64 -> neu, nach der Vorlage des Nutzers ---------------------------------
# Die Zeilen folgen den Rampen oben: Rot bleibt Rot, Haut bleibt Haut. Was
# im Cowboy-Frame belegt ist, steht genau so drin.
AAP_ZU_NEU = {
    # Schwarz, Grau, Kanten
    '060608': '000000', '141013': '1d1d21', '221c1a': '222323', '242234': '26233d',
    '322b28': '4a353c', '423934': '5e4646', '3b1725': '82211d',
    # Rot (Rampe 9) und Feuer (Rampe 4 / 31)
    '73172d': 'b63c35', 'b4202a': 'e45c5f', 'e86a73': 'ff9ba8', 'df3e23': 'cd5e46',
    'fa6a0a': 'e37840', 'f9a31b': 'ffb108', 'ffd541': 'ffcf05', 'fffc40': 'a6cc34',
    # Haut (Rampe 2)
    '422433': '733d3b', '5b3138': '885041', '8e5252': 'ad6e51', 'ba756a': 'd58d6b',
    'f5a097': 'fbaa84', 'fad6b8': 'ffce7f', 'fef3c0': 'fff3d6',
    # Leder und Hut (Rampe 12), Knochen (Rampe 1)
    '5a4e44': '9e8a6e', '796755': 'c0a588', '71413b': '725a51', 'a08662': 'ddbf9a',
    'c7b08b': 'ccc3b1', 'e4d2aa': 'eadbc9',
    # Holz (Rampe 15)
    'bb7547': 'b29062', 'dba463': 'cca96e', 'f4d29c': 'e8cb82',
    # Gruen (Rampe 6)
    '122020': '002219', '24523b': '003221', '1a7a3e': '174a1b', '14a02e': '225918',
    '59c135': '2f690c', '9cdb43': '518822', 'd6f264': '7da42d',
    # Blau (Rampe 29 / 26 / 14)
    '143464': '2d3d72', '285cc4': '5274c5', '849be4': '8393c3', '249fde': '1476c0',
    '20d6c7': '00bfa3', 'a6fcdb': '00deda',
    # Violett (Rampe 13), Schleimviolett und Runen
    'bc4a9b': 'c178aa', '793a80': '663659', '403353': '49283d', '494182': '584a7f',
    # Stahl (Rampe 0 / 10)
    'ffffff': 'cdd2da', 'fdf6d5': 'f5f7fa', 'dae0ea': 'bac7db', 'b3b9d1': 'abaebe',
    '8b93af': '848795', '6d758d': '73737f', '4a5462': '5b5c69', '333941': '48474d',
    '422433_': '',
}
AAP_ZU_NEU.pop('422433_')
assert all(v in PALETTE for v in AAP_ZU_NEU.values()), 'AAP-Ziel nicht in der Palette'


# --- Splendor (vorherige Palette) -> neu ------------------------------------------
# Die Generatoren schreiben noch in den Splendor-Toenen; hier werden sie
# rampenweise umgesetzt, damit Hell-Dunkel-Reihen Reihen bleiben.
SPLENDOR_ZU_NEU = {
    # Schwarz und Kanten
    '050403': '000000', '0e0c0c': '1d1d21', '171516': '222323', '14121d': '26233d',
    '2d1b1e': '372423', '271f1b': '31222a', '322f35': '3b303c', '33272a': '4a353c',
    '36282b': '53393a', '2a1e23': '431729', '323232': '434549', '373334': '48474d',
    '595757': '5b5c69', '695b59': '625d54', '807b7a': '73737f', 'a69e9a': 'abaebe',
    'cbc6c1': 'bbafa4', 'ecebe7': 'ebf0f6', 'ffffff': 'f5f7fa', 'f1f2ff': 'e0faeb',
    # Rot, Feuer, Gold
    '612721': '662b29', 'b9451d': 'bf5a3e', 'b05b2c': 'cd5e46', 'f1641f': 'e37840',
    'fca570': 'f99b4e', 'ffe0b7': 'fedfb1', 'fff089': 'fff64f', 'f8c53a': 'ffb108',
    'e88a36': 'e98627', '673931': '633432', 'f8f644': 'fff02b', 'd6a851': 'd1aa39',
    'b47538': '9e6520', '855f39': '7e6144', '724b2c': '614a3c', '452a1b': '49251c',
    '4c3d2e': '453125', 'e1bf89': 'ecc581', 'f8e398': 'fbeaa3', 'efdd91': 'e8cb82',
    'f6d896': 'edd493', 'e2b27e': 'edb67c', 'c68556': 'd58d6b', '8c5b3e': '9a624c',
    '4f342f': '53393a', 'b28b78': 'b39783',
    # Wein, Rosa, Haut
    'b25266': '9f3b52', '64364b': '663659', 'e27285': 'ff7676', 'f6a2a8': 'ff9ba8',
    'fdc9c9': 'ffbbc7', 'ffe9e3': 'ffe2cf', 'eeb59c': 'ebbd9d', 'd4b8b8': 'd4aeaa',
    'eae0dd': 'f8c6da', 'e3cddf': 'db99bf', 'bfa5c9': 'b98c93', '87738f': '765d73',
    '564f5b': '554769', '966888': '977488', 'c090a9': 'b58b94', '654956': '5e414a',
    'd480bb': 'c178aa', '9052bc': '7877c1', '7864c6': '7964ba', '9c8bdb': 'a996ec',
    'ceaaed': 'baabf7', 'fad6ff': 'd1bdfe', '494182': '584a7f',
    # Knochen und Stoff
    'fcf7be': 'fff3d6', 'f1ebdb': 'eadbc9', 'ddcebf': 'ccc3b1', 'bda499': 'aea189',
    'b29476': '9e8c79', '886e6a': '857565', '594d4d': '5e4646',
    # Gruen
    '181c19': '002219', '293f21': '2f4f08', '477238': '58712c', '61a53f': '518822',
    '8fd032': '7da42d', 'c4f129': 'a6cc34', '333c24': '202900', '586335': '4c5f33',
    '61683a': '495d00', '7f8e44': '6b842d', '939446': '7c831e', 'adb834': 'b4aa33',
    'c6b858': 'd0cc32', 'd5dc1d': 'fff64f',
    # Schleim und Salbei
    'd0ffea': 'e0faeb', 'b5e7cb': '91daa1', '97edca': 'a9d1c1', '86c69a': '8ac196',
    '59cf93': '55b67d', '5d9b79': '498960', '42a459': '417455', '3d6f43': '385140',
    '486859': '47655a', '27412d': '394d3c', '2c3b39': '2f3f38', '171819': '1a332c',
    '8ac4c3': '87ae8e', 'afe9df': '71957d',
    # Blau, Eis, Stahl
    '1b2447': '282b4a', '2b4e95': '105da2', '2789cd': '1476c0', '42bfe8': '24aed6',
    '73efe8': '74f5fd', 'c9d4fd': 'c7d6ff', '8aa1f6': '96b2d9', '4572e3': '5165ae',
    '2c3438': '2d3136', '465456': '2e3d47', '64878c': '5b7b69', 'dceaee': 'c6ecff',
    'b8ccd8': 'bac7db', '88a3bc': '8690b2', '5e718e': '7a7799', '485262': '5b5c69',
    '282c3c': '1d2c43', '464762': '56506f', '696682': '615f84', '9a97b9': '8690b2',
    'c5c7dd': 'a6aeba', 'e6e7f0': 'cdd2da', 'eee6ea': 'ebf0f6',
}
assert all(v in PALETTE for v in SPLENDOR_ZU_NEU.values()), 'Splendor-Ziel nicht in der Palette'


def _rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _lab(c):
    r, g, b = [v / 255.0 for v in c]
    r, g, b = r ** 2.2, g ** 2.2, b ** 2.2
    x = r * 0.4124 + g * 0.3576 + b * 0.1805
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = r * 0.0193 + g * 0.1192 + b * 0.9505

    def f(t):
        return t ** (1.0 / 3) if t > 0.008856 else 7.787 * t + 16.0 / 116
    fx, fy, fz = f(x / 0.9505), f(y), f(z / 1.089)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


_LAB = [(h, _lab(_rgb(h))) for h in PALETTE]


def _naechste_lab(c):
    l = _lab(c)
    return min(_LAB, key=lambda p: (p[1][0] - l[0]) ** 2 + (p[1][1] - l[1]) ** 2 + (p[1][2] - l[2]) ** 2)[0]


# Handzuordnungen zusammen, als RGB-Tabelle
def _karte(*zuordnungen):
    k = {}
    for z in zuordnungen:
        for a, b in z.items():
            k[_rgb(a)] = _rgb(b) + (255,)
    return k


# Die Vorlage des Nutzers hat Vorrang: erst die alte Splendor-Reihe, dann
# AAP-64 daruebergelegt.
KARTE = _karte(SPLENDOR_ZU_NEU, AAP_ZU_NEU)

# Spielfiguren und Waffen duerfen eine Stufe heller in ihrer Rampe stehen -
# so heben sie sich vom Turm ab, ohne den Farbton zu wechseln.
_STUFE = {_rgb(h): i for i, h in enumerate(PALETTE)}


def _heller(rgbwert, um=1):
    i = _STUFE.get(rgbwert[:3])
    if i is None:
        return rgbwert
    rampe, stufe = divmod(i, 8)
    return _rgb(PALETTE[rampe * 8 + min(7, stufe + um)]) + (255,)


def naechste(c, stil='gedaempft'):
    r, g, b = c[:3]
    ziel = KARTE.get((r, g, b))
    if ziel is None:
        ziel = (_rgb(_naechste_lab((r, g, b))) + (255,)) if (r, g, b) not in PALETTE_SET else (r, g, b, 255)
    if stil in ('kraeftig', 'figur') and _STUFE.get(ziel[:3], 0) % 8 <= 5:
        ziel = _heller(ziel, 1)
    return ziel


def palette_anpassen(img, stil='gedaempft'):
    """Alle deckenden Pixel auf die Palette ruecken. stil: gedaempft (Gegner,
    Kacheln) oder kraeftig/figur (Spielfiguren, Waffen, Beute)."""
    px = img.load()
    cache = {}
    for y in range(img.height):
        for x in range(img.width):
            c = px[x, y]
            if c[3] == 0:
                continue
            if c not in cache:
                cache[c] = naechste(c, stil)
            px[x, y] = cache[c]
    return img


# --- Kontur ----------------------------------------------------------------------
# Der Nutzer umrandet seine Figuren seit 26.09.2026 mit 1 px in der
# *dunkelsten Stufe der Rampe des angrenzenden Materials* (Leder 31222a,
# Haut 583126, Poncho 5e0711) - kein Schwarz, keine zweite Farbe. Gemessen
# an Sprites/Character/cowboy/Front1.png: 76 Konturpixel, alle auf der
# 4er-Nachbarschaft, die Farbe folgt dem Material ringsum.

_RAMPE_VON = {}
for _i, _h in enumerate(PALETTE):
    _RAMPE_VON.setdefault(_rgb(_h), _i // 8)

_VIER = ((0, -1), (0, 1), (-1, 0), (1, 0))
_DIAG = tuple((dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx and dy)


def _rampe(c):
    r = _RAMPE_VON.get(c[:3])
    if r is None:
        r = _RAMPE_VON[naechste(c)[:3]]
    return r


def umriss(img):
    """Legt die Kontur neu an: eine schon vorhandene wird abgezogen, dann
    bekommt jeder freie Pixel neben der Figur die dunkelste Stufe der Rampe,
    die ringsum ueberwiegt (gerade Nachbarn zaehlen doppelt). Grau zaehlt nur,
    wenn es nichts anderes gibt - ein heller Punkt auf dem Stiefel soll die
    Kontur nicht einfaerben."""
    px = img.load()
    w, h = img.size
    deckend = {(x, y) for y in range(h) for x in range(w) if px[x, y][3]}
    rampen = {p: _rampe(px[p]) for p in deckend}
    stufe = {}
    for p in deckend:
        i = _RAMPE_VON.get(px[p][:3])
        stufe[p] = None if i is None else _STUFE[px[p][:3]] % 8
    def dunkel(c):
        return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
    alt = set()
    for p in deckend:                                 # vorhandene Kontur erkennen:
        if all((p[0] + dx, p[1] + dy) in deckend for dx, dy in _VIER):
            continue                                  # liegt innen, ist keine
        nachbarn = [px[(p[0] + dx, p[1] + dy)] for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                    if (dx or dy) and (p[0] + dx, p[1] + dy) in deckend
                    and px[(p[0] + dx, p[1] + dy)] != px[p]]    # gleiche Farbe: derselbe Ring
        if (nachbarn and dunkel(px[p]) <= min(dunkel(c) for c in nachbarn)
                and (stufe[p] is None or stufe[p] <= 2)):
            alt.add(p)                                # dunkler als alles ringsum
    innen = deckend - alt
    for p in alt:
        px[p] = (0, 0, 0, 0)
    neu = {}
    for x in range(w):
        for y in range(h):
            p = (x, y)
            if p in innen:
                continue
            gewicht = {}
            for (dx, dy), g in [(d, 2) for d in _VIER] + [(d, 1) for d in _DIAG]:
                q = (x + dx, y + dy)
                if q in innen:
                    gewicht[rampen[q]] = gewicht.get(rampen[q], 0) + g
            if not gewicht or not any((x + dx, y + dy) in innen for dx, dy in _VIER):
                continue
            ohne_grau = {r: g for r, g in gewicht.items() if r != 0}
            wahl = max((ohne_grau or gewicht).items(), key=lambda t: (t[1], -t[0]))[0]
            neu[p] = _rgb(PALETTE[wahl * 8]) + (255,)
    for p, c in neu.items():
        px[p] = c
    return img


# Rueckwaerts-kompatible Namen fuer die Generatoren
duel_anpassen = palette_anpassen
SPLENDOR = PALETTE
