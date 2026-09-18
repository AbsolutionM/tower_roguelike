#!/usr/bin/env python3
"""Aktive Palette: AAP-Splendor128 (lospec, 128 Farben) - seit 18.09.2026.

Gelesen aus Downloads/aap-splendor128-1x.png. palette_anpassen() setzt
AAP-64-Farben nach der Handzuordnung AAP_ZU_SPLENDOR um (bewusst gedaempfte
Reihen) und rueckt alles andere auf die naechste Splendor-Farbe. Frueher:
Duel (tools/duel.py), davor AAP-64.
"""

SPLENDOR = """050403 0e0c0c 2d1b1e 612721 b9451d f1641f fca570 ffe0b7 ffffff fff089 f8c53a e88a36 b05b2c 673931 271f1b 4c3d2e 855f39 d39741 f8f644 d5dc1d adb834 7f8e44 586335 333c24 181c19 293f21 477238 61a53f 8fd032 c4f129 d0ffea 97edca 59cf93 42a459 3d6f43 27412d 14121d 1b2447 2b4e95 2789cd 42bfe8 73efe8 f1f2ff c9d4fd 8aa1f6 4572e3 494182 7864c6 9c8bdb ceaaed fad6ff eeb59c d480bb 9052bc 171516 373334 695b59 b28b78 e2b27e f6d896 fcf7be ecebe7 cbc6c1 a69e9a 807b7a 595757 323232 4f342f 8c5b3e c68556 d6a851 b47538 724b2c 452a1b 61683a 939446 c6b858 efdd91 b5e7cb 86c69a 5d9b79 486859 2c3b39 171819 2c3438 465456 64878c 8ac4c3 afe9df dceaee b8ccd8 88a3bc 5e718e 485262 282c3c 464762 696682 9a97b9 c5c7dd e6e7f0 eee6ea e3cddf bfa5c9 87738f 564f5b 322f35 36282b 654956 966888 c090a9 d4b8b8 eae0dd f1ebdb ddcebf bda499 886e6a 594d4d 33272a b29476 e1bf89 f8e398 ffe9e3 fdc9c9 f6a2a8 e27285 b25266 64364b 2a1e23""".split()

SPLENDOR_RGB = [(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)) for h in SPLENDOR]
SPLENDOR_SET = set(SPLENDOR_RGB)

# AAP-64 -> Splendor, von Hand: gedaempfte Reihen (Schleimgruen wird Salbei,
# Rot wird Himbeer/Ziegel, Stahl wird Blaugrau). Eindeutig, damit Baender
# und die 3-Pixel-Regel auf den Waffen erhalten bleiben.
# Farbtheorie mit leichter Hand: Schatten kippen etwas ins Kalte, Lichter
# etwas ins Warme; die Rampen enden eine Stufe vor Schwarz und Weiss.
AAP_ZU_SPLENDOR = {
    # Schwarz und Kanten: kuehl
    '060608': '050403', '141013': '0e0c0c', '221c1a': '171516', '242234': '282c3c',
    '322b28': '271f1b', '3b1725': '2d1b1e',
    # Rot: Schatten violett, Licht rosa; Feuer warm bis gelb
    '73172d': '64364b', 'b4202a': 'b25266', 'df3e23': 'b9451d', 'fa6a0a': 'f1641f',
    'f9a31b': 'e88a36', 'ffd541': 'f8c53a', 'fffc40': 'fff089',
    # Gruen: Schatten blaugruen, Licht warm gelbgruen
    '122020': '171819', '24523b': '2c3b39', '1a7a3e': '486859', '14a02e': '5d9b79',
    '59c135': '86c69a', '9cdb43': 'b5e7cb', 'd6f264': 'efdd91',
    # Blau / Kristall
    '143464': '1b2447', '285cc4': '2b4e95', '249fde': '2789cd', '20d6c7': '42bfe8',
    'a6fcdb': '73efe8', '849be4': '8aa1f6',
    # Haut: Schatten ins Violett, Licht ins Creme
    'fef3c0': 'fcf7be', 'fad6b8': 'ffe0b7', 'f5a097': 'eeb59c', 'ba756a': 'b28b78',
    '8e5252': '8c5b3e', 'e86a73': 'e27285',
    # Violett
    'bc4a9b': 'd480bb', '793a80': '966888', '403353': '654956',
    # Leder / Holz
    'f4d29c': 'e1bf89', 'dba463': 'd6a851', 'bb7547': 'b47538', '71413b': '724b2c',
    '5b3138': '4f342f',
    # Stahl: Licht fast weiss, Schatten tiefblau
    'ffffff': 'ffffff', 'fdf6d5': 'f1ebdb', 'dae0ea': 'e6e7f0', 'b3b9d1': 'c5c7dd',
    '8b93af': '9a97b9', '6d758d': '696682', '4a5462': '464762', '333941': '2c3438',
    '422433': '36282b',
    # Knochen: warm, Schatten grau-violett
    'e4d2aa': 'ddcebf', 'c7b08b': 'bda499', 'a08662': 'b29476', '796755': '886e6a',
    '5a4e44': '594d4d', '423934': '33272a',
}
assert len(set(AAP_ZU_SPLENDOR.values())) == len(AAP_ZU_SPLENDOR), 'Zuordnung nicht eindeutig'
assert all(v in SPLENDOR for v in AAP_ZU_SPLENDOR.values())
_KARTE = {tuple(int(k[i:i + 2], 16) for i in (0, 2, 4)): tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
          for k, v in AAP_ZU_SPLENDOR.items()}


def naechste(c):
    r, g, b = c[:3]
    if (r, g, b) in _KARTE:
        return _KARTE[(r, g, b)]
    if (r, g, b) in SPLENDOR_SET:
        return (r, g, b, 255)
    best = min(SPLENDOR_RGB, key=lambda k: (k[0] - r) ** 2 + (k[1] - g) ** 2 + (k[2] - b) ** 2)
    return best + (255,)


def palette_anpassen(img):
    """Alle deckenden Pixel auf die Palette ruecken."""
    px = img.load()
    cache = {}
    for y in range(img.height):
        for x in range(img.width):
            c = px[x, y]
            if c[3] == 0:
                continue
            if c not in cache:
                cache[c] = naechste(c)
            px[x, y] = cache[c]
    return img


# Rueckwaerts-kompatibler Name fuer die Generatoren
duel_anpassen = palette_anpassen
