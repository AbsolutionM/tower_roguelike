#!/usr/bin/env python3
"""Duel-Palette (lospec, 256 Farben) - die neue Palette des Nutzers.

Gelesen aus Downloads/duel-1x.png. duel_anpassen() setzt AAP-64-Farben
nach der Handzuordnung AAP_ZU_DUEL um und rueckt alles andere auf die
naechste Duel-Farbe; die Generatoren waehlen ihre Rampen
aber bewusst aus den gedaempften Reihen, damit nichts nachtraeglich
gesaettigt wird.
"""

DUEL = """000000 222323 434549 626871 828b98 a6aeba cdd2da f5f7fa 625d54 857565 9e8c79 aea189 bbafa4 ccc3b1 eadbc9 fff3d6 583126 733d3b 885041 9a624c ad6e51 d58d6b fbaa84 ffce7f 002735 003850 004d5e 0b667f 006f89 328ca7 24aed6 88d6ff 662b29 94363a b64d46 cd5e46 e37840 f99b4e ffbc4e ffe949 282b4a 3a4568 615f84 7a7799 8690b2 96b2d9 c7d6ff c6ecff 002219 003221 174a1b 225918 2f690c 518822 7da42d a6cc34 181f2f 23324d 25466b 366b8a 318eb8 41b2e3 52d2ff 74f5fd 1a332c 2f3f38 385140 325c40 417455 498960 55b67d 91daa1 5e0711 82211d b63c35 e45c5f ff7676 ff9ba8 ffbbc7 ffdbff 2d3136 48474d 5b5c69 73737f 848795 abaebe bac7db ebf0f6 3b303c 5a3c45 8a5258 ae6b60 c7826c d89f75 ecc581 fffaab 31222a 4a353c 5e4646 725a51 7e6c54 9e8a6e c0a588 ddbf9a 2e1026 49283d 663659 975475 b96d91 c178aa db99bf f8c6da 002e49 004051 005162 006b6d 008279 00a087 00bfa3 00deda 453125 614a3c 7e6144 997951 b29062 cca96e e8cb82 fbeaa3 5f0926 6e2434 904647 a76057 bd7d64 ce9770 edb67c edd493 323558 4a5280 64659d 7877c1 8e8ce2 9c9bef b8aeff dcd4ff 431729 712b3b 9f3b52 d94a69 f85d80 ff7daf ffa6c5 ffcdff 49251c 633432 7c4b47 98595a ac6f6e c17e7a d28d7a e59a7c 202900 2f4f08 495d00 617308 7c831e 969a26 b4aa33 d0cc32 622a00 753b09 854f12 9e6520 ba882e d1aa39 e8d24b fff64f 26233d 3b3855 56506f 75686e 917a7b b39783 cfaf8e fedfb1 1d2c43 2e3d47 394d3c 4c5f33 58712c 6b842d 789e24 7fbd39 372423 53393a 784c49 945d4f a96d58 bf7e63 d79374 f4a380 2d4b47 47655a 5b7b69 71957d 87ae8e 8ac196 a9d1c1 e0faeb 001b40 03315f 07487c 105da2 1476c0 4097ea 55b1f1 6dccff 554769 765d73 977488 b98c93 d5a39a ebbd9d ffd59b fdf786 1d1d21 3c3151 584a7f 7964ba 9585f1 a996ec baabf7 d1bdfe 262450 28335d 2d3d72 3d5083 5165ae 5274c5 6c82c4 8393c3 492129 5e414a 77535b 91606a ad7984 b58b94 d4aeaa ffe2cf 721c03 9c3327 bf5a3e e98627 ffb108 ffcf05 fff02b f7f4bf""".split()

DUEL_RGB = [(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)) for h in DUEL]
DUEL_SET = set(DUEL_RGB)


# AAP-64 -> Duel, von Hand gewaehlt: jede AAP-Farbe bekommt eine eigene,
# gedaempfte Duel-Farbe (Gruen wird Moos, Rot Ziegel, Blau Stahlblau). Die
# Zuordnung ist eindeutig, damit Baender und die 3-Pixel-Regel auf den
# Waffen erhalten bleiben.
AAP_ZU_DUEL = {
    '060608': '000000', '141013': '1d1d21', '221c1a': '222323', '242234': '26233d',
    '322b28': '31222a', '3b1725': '431729', '73172d': '5f0926', 'b4202a': 'b63c35',
    'df3e23': 'cd5e46', 'fa6a0a': 'e37840', 'f9a31b': 'f99b4e', 'ffd541': 'ffbc4e',
    'fffc40': 'ffe949', 'd6f264': 'e0faeb', '9cdb43': '91daa1', '59c135': '55b67d',
    '14a02e': '498960', '1a7a3e': '417455', '24523b': '325c40', '122020': '1a332c',
    '143464': '23324d', '285cc4': '366b8a', '249fde': '318eb8', '20d6c7': '41b2e3',
    'a6fcdb': 'c6ecff', 'fef3c0': 'fff3d6', 'fad6b8': 'eadbc9', 'f5a097': 'ebbd9d',
    'e86a73': 'c17e7a', 'bc4a9b': 'b96d91', '793a80': '663659', '403353': '49283d',
    '71413b': '633432', 'bb7547': 'a96d58', 'dba463': 'cca96e', 'f4d29c': 'e8cb82',
    'fdf6d5': 'fffaab', 'ffffff': 'f5f7fa', 'dae0ea': 'cdd2da', 'b3b9d1': 'a6aeba',
    '8b93af': '828b98', '6d758d': '626871', '4a5462': '48474d', '333941': '2d3136',
    '422433': '4a353c', '5b3138': '5e4646', '8e5252': '77535b', 'ba756a': 'ac6f6e',
    'e4d2aa': 'ccc3b1', 'c7b08b': 'bbafa4', 'a08662': '9e8c79', '796755': '857565',
    '5a4e44': '625d54', '423934': '434549', '849be4': '8690b2',
}
assert len(set(AAP_ZU_DUEL.values())) == len(AAP_ZU_DUEL), 'Zuordnung nicht eindeutig'
assert all(v in DUEL for v in AAP_ZU_DUEL.values())
_KARTE = {tuple(int(k[i:i + 2], 16) for i in (0, 2, 4)): tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
          for k, v in AAP_ZU_DUEL.items()}


def naechste(c):
    r, g, b = c[:3]
    if (r, g, b) in _KARTE:
        return _KARTE[(r, g, b)]
    if (r, g, b) in DUEL_SET:
        return (r, g, b, 255)
    best = min(DUEL_RGB, key=lambda k: (k[0] - r) ** 2 + (k[1] - g) ** 2 + (k[2] - b) ** 2)
    return best + (255,)


def duel_anpassen(img):
    """Alle deckenden Pixel auf die naechste Duel-Farbe ruecken."""
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
