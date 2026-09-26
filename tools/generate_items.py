#!/usr/bin/env python3
"""Item-Icons, 16x16, AAP-Splendor128 (kraeftige Reihen wie bei Waffen und
Spielfiguren - Beute soll auf dem Boden auffallen).

Gebaut wie die Waffen: kein schwarzer Umriss (den setzt Godot als Shader),
Licht von oben links, jede Form als Koerper - Kugel, Roehre, Platte - mit
Glanz, Mittelton, Kernschatten und einem Streulicht an der Schattenkante.
Keine grossen einfarbigen Flaechen.

Gedeckt sind die Items, die es im Spiel schon gibt (resources/items,
resources/accessories), dazu neue Verbrauchsgegenstaende und Materialien:

    Material    slime_gel iron_scrap ore_chunk crystal_shard boss_core
                bone_fragment ember_ash frost_core venom_sac bat_wing
                spider_silk rune_stone
    Waehrung    gold_coin gold_pouch
    Essenz      essence_slime soul_heart
    Herzen      red_heart half_red_heart
    Zugang      key lockpick chest
    Verbrauch   health_potion mana_potion stamina_potion antidote bomb
                scroll torch bread
    Schmuck     power_ring life_amulet swift_boots iron_plate hawk_eye
                leech_fang skull_charm

    python tools/generate_items.py --out C:/Users/maxst/Desktop/Sprites/claude/Items --sheet
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image

from palette import duel_anpassen

G = 16                                  # Kantenlaenge

# Rampen: Glanz, hell, mitte, dunkel, kante
R = {
    'gold': ('fff089', 'f8c53a', 'd39741', 'b47538', '673931'),
    'stahl': ('f1f2ff', 'c9d4fd', '9a97b9', '696682', '2c3438'),
    'eisen': ('c5c7dd', '9a97b9', '696682', '464762', '282c3c'),
    'blut': ('f6a2a8', 'e27285', 'b25266', '64364b', '2a1e23'),
    'gel': ('c4f129', '8fd032', '61a53f', '477238', '293f21'),
    'kristall': ('73efe8', '42bfe8', '2789cd', '2b4e95', '1b2447'),
    'seele': ('dceaee', '8aa1f6', '4572e3', '2b4e95', '1b2447'),
    'violett': ('fad6ff', 'ceaaed', '9c8bdb', '7864c6', '494182'),
    'leder': ('f6d896', 'd39741', 'c68556', '724b2c', '452a1b'),
    'holz': ('d6a851', 'b47538', '724b2c', '4f342f', '2d1b1e'),
    'knochen': ('fcf7be', 'f1ebdb', 'ddcebf', 'bda499', '886e6a'),
    'feuer': ('fff089', 'f8c53a', 'f1641f', 'b9451d', '612721'),
    'eis': ('dceaee', 'afe9df', '8ac4c3', '64878c', '2c3438'),
    'gift': ('d0ffea', '8fd032', '61a53f', '3d6f43', '27412d'),
    'papier': ('ffe9e3', 'f1ebdb', 'ddcebf', 'b29476', '724b2c'),
    'stoff': ('e27285', 'b25266', '64364b', '36282b', '2a1e23'),
    'schatten': ('807b7a', '595757', '373334', '271f1b', '0e0c0c'),
    'erz': ('afe9df', '8ac4c3', '64878c', '465456', '2c3438'),
    'brot': ('f6d896', 'd39741', 'b47538', '724b2c', '452a1b'),
}


def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def ton(name, i):
    return rgb(R[name][i])


def bild():
    return Image.new('RGBA', (G, G), (0, 0, 0, 0))


def put(px, x, y, col):
    if 0 <= x < G and 0 <= y < G:
        px[x, y] = col


def frei(px, x, y):
    return 0 <= x < G and 0 <= y < G and px[x, y][3] == 0


LICHT = (-0.55, -0.5, 0.67)             # oben links vorne


def kugel(px, cx, cy, r, rampe, flach=1.0, glanz=True, von=0):
    """Kugel oder Tropfen: Normale aus der Ellipse, vier Stufen, Glanzfleck
    oben links, Streulicht an der unteren rechten Kante."""
    gl, hell, mitte, dunkel, kante = (ton(rampe, i) for i in range(5))
    stufen = (gl, hell, mitte, dunkel, kante)[von:] + (kante,) * von
    innen = []
    for y in range(G):
        for x in range(G):
            nx, ny = (x - cx) / r, (y - cy) / (r * flach)
            d = nx * nx + ny * ny
            if d > 1.0:
                continue
            nz = math.sqrt(max(0.0, 1 - d))
            lit = nx * LICHT[0] + ny * LICHT[1] + nz * LICHT[2]
            if lit > 0.8 and glanz:
                col = stufen[0]
            elif lit > 0.52:
                col = stufen[1]
            elif lit > 0.22:
                col = stufen[2]
            elif lit > -0.05:
                col = stufen[3]
            else:
                col = stufen[4]
            if lit <= -0.05 and nx < -0.25 and ny > 0.15:   # Bodenlicht unten links
                col = stufen[3]
            put(px, x, y, col)
            innen.append((x, y))
    for x, y in innen:                                   # Streulicht unten rechts
        if px[x, y] == stufen[4] and not frei(px, x + 1, y) and frei(px, x, y + 1):
            put(px, x, y, stufen[3])
    return innen


def platte(px, x0, y0, x1, y1, rampe, rund=0, von=0):
    """Rechteck als Koerper: obere und linke Kante hell, untere und rechte
    dunkel, Mitte dazwischen; rund schneidet die Ecken."""
    gl, hell, mitte, dunkel, kante = (ton(rampe, i) for i in range(5))
    stufen = (gl, hell, mitte, dunkel, kante)[von:] + (kante,) * von
    punkte = set()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if rund:
                dx = min(x - x0, x1 - x) + 1
                dy = min(y - y0, y1 - y) + 1
                if dx + dy <= rund + 1:
                    continue
            punkte.add((x, y))
    w = max(1, x1 - x0)
    h = max(1, y1 - y0)
    for x, y in punkte:
        oben = (x, y - 1) not in punkte
        links = (x - 1, y) not in punkte
        unten = (x, y + 1) not in punkte
        rechts = (x + 1, y) not in punkte
        u, v = (x - x0) / w, (y - y0) / h
        t = 1.0 - (u * 0.58 + v * 0.42)          # Verlauf quer ueber die Flaeche
        if unten and rechts:
            col = stufen[4]
        elif unten or rechts:
            col = stufen[4] if t < 0.3 else stufen[3]
        elif oben and links:
            col = stufen[0]
        elif t > 0.74:
            col = stufen[0] if (oben or links) else stufen[1]
        elif t > 0.52:
            col = stufen[1]
        elif t > 0.3:
            col = stufen[2]
        else:
            col = stufen[3]
        put(px, x, y, col)
    return punkte


INDEX = {}                              # Farbe -> (Rampe, Stufe)
for _n, _r in R.items():
    for _i, _h in enumerate(_r):
        INDEX.setdefault(rgb(_h), (_n, _i))


def dunkler(col, n=1):
    """Eine Stufe tiefer in derselben Rampe - fuer Kontaktschatten."""
    if col not in INDEX:
        return col
    name, i = INDEX[col]
    return ton(name, min(4, i + n))


def heller(col, n=1):
    if col not in INDEX:
        return col
    name, i = INDEX[col]
    return ton(name, max(0, i - n))


def rampe_von(col):
    return INDEX.get(col, (None, 0))[0]


def verzahnen(px):
    """Wo ein anderes Material obendrauf liegt (Korken auf Glas, Deckel auf
    Kiste, Fassung auf Stein), faellt ein Schatten auf die Zeile darunter -
    das trennt die Teile in der Tiefe statt sie nur nebeneinanderzulegen."""
    alt = [[px[x, y] for x in range(G)] for y in range(G)]
    for y in range(1, G):
        for x in range(G):
            c = alt[y][x]
            o = alt[y - 1][x]
            if c[3] and o[3] and rampe_von(c) and rampe_von(c) != rampe_von(o):
                put(px, x, y, dunkler(c, 1))


def randlicht(px):
    """Streulicht vom Boden: an der unteren linken Kante eine Stufe heller,
    damit die Form sich auch im Schatten noch woelbt."""
    alt = [[px[x, y] for x in range(G)] for y in range(G)]
    for y in range(G):
        for x in range(G):
            c = alt[y][x]
            if not c[3] or not rampe_von(c):
                continue
            unten = y + 1 >= G or not alt[y + 1][x][3]
            links = x - 1 < 0 or not alt[y][x - 1][3]
            if (unten or links) and INDEX[c][1] >= 3:
                put(px, x, y, heller(c, 1))


def glaetten(px, runden=2):
    """Einzelne Fremdpixel verschwinden: ein Pixel, dessen Farbe bei keinem
    der acht Nachbarn vorkommt, wird zur haeufigsten Nachbarfarbe. Dazu
    fliegen lose Teile (hoechstens zwei Pixel ohne Anschluss) raus."""
    for _ in range(runden):
        alt = [[px[x, y] for x in range(G)] for y in range(G)]
        for y in range(G):
            for x in range(G):
                c = alt[y][x]
                if not c[3]:
                    continue
                nb = []
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < G and 0 <= ny < G and alt[ny][nx][3]:
                            nb.append(alt[ny][nx])
                if not nb or any(q == c for q in nb):
                    continue
                eigen = rampe_von(c)
                if eigen and all(rampe_von(q) != eigen for q in nb):
                    continue                     # gesetzter Akzent, kein Rauschen
                gleiche = [q for q in nb if rampe_von(q) == eigen] or nb
                put(px, x, y, max(set(gleiche), key=gleiche.count))
    # lose Teile
    gesehen = set()
    teile = []
    for y in range(G):
        for x in range(G):
            if (x, y) in gesehen or not px[x, y][3]:
                continue
            stapel, teil = [(x, y)], []
            gesehen.add((x, y))
            while stapel:
                cx, cy = stapel.pop()
                teil.append((cx, cy))
                for dx in (-1, 0, 1):                    # auch ueber die Diagonale,
                    for dy in (-1, 0, 1):                # sonst zaehlt eine Kette als lose
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < G and 0 <= ny < G and (nx, ny) not in gesehen and px[nx, ny][3]:
                            gesehen.add((nx, ny))
                            stapel.append((nx, ny))
            teile.append(teil)
    if teile:
        teile.sort(key=len, reverse=True)
        for teil in teile[1:]:
            if len(teil) <= 2:
                for x, y in teil:
                    px[x, y] = (0, 0, 0, 0)


def kernschatten(px):
    """Umgebungsverdeckung: wo eine Form nach unten oder rechts zu Ende ist,
    aber noch etwas dahinter liegt, wird eine Stufe tiefer gesetzt; in engen
    Winkeln zwei. Das hebt die Teile voneinander ab."""
    alt = [[px[x, y] for x in range(G)] for y in range(G)]
    for y in range(G):
        for x in range(G):
            c = alt[y][x]
            if not c[3] or not rampe_von(c):
                continue
            eng = 0
            for dx, dy in ((1, 0), (0, 1), (1, 1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < G and 0 <= ny < G and alt[ny][nx][3]:
                    if rampe_von(alt[ny][nx]) != rampe_von(c):
                        eng += 1
            if eng >= 2:
                put(px, x, y, dunkler(c, 1))


def bodenschatten(px):
    """Kurzer Schlagschatten nach unten rechts - das Icon schwebt sonst."""
    unten = {}
    for y in range(G):
        for x in range(G):
            if px[x, y][3]:
                unten[x] = max(unten.get(x, -1), y)
    if not unten:
        return
    tief = max(unten.values())
    for x, y in unten.items():
        if y < tief - 1:
            continue
        for dx, col in ((1, ton('schatten', 3)), (2, ton('schatten', 4))):
            nx, ny = x + dx - 1, y + 1
            if 0 <= nx < G and 0 <= ny < G and not px[nx, ny][3]:
                px[nx, ny] = col if dx == 1 else px[nx, ny]


def band(px, punkte, col):
    for x, y in punkte:
        put(px, x, y, col)


def funke(px, stellen, col):
    for x, y in stellen:
        put(px, x, y, col)


def schatten(px, punkte, col):
    """Duenner Bodenschatten unter einer Form."""
    unten = {}
    for x, y in punkte:
        unten[x] = max(unten.get(x, -1), y)
    for x, y in unten.items():
        if frei(px, x, y + 1):
            put(px, x, y + 1, col)


# --- Material ----------------------------------------------------------------------

def slime_gel(px):
    """Gelklumpen: unten breit ausgelaufen, oben gewoelbt, ein Tropfen laeuft
    seitlich herunter - das Gel ist durchscheinend, unten liegt Streulicht."""
    kugel(px, 7.5, 9.5, 6.2, 'gel', flach=0.78)
    for x in range(3, 13):                               # ausgelaufener Rand
        if px[x, 13][3]:
            put(px, x, 13, ton('gel', 3))
    funke(px, ((5, 6), (6, 5), (6, 6)), ton('gel', 0))   # Glanz
    funke(px, ((10, 12), (11, 11)), ton('gel', 4))
    for j, y in enumerate((5, 6, 7, 8)):                 # Tropfen an der Flanke
        put(px, 12 - j // 3, y, ton('gel', 1 if j < 2 else 2))
    put(px, 12, 9, ton('gel', 3))
    funke(px, ((8, 8), (9, 9)), ton('gel', 1))           # Blasen im Gel


SCHROTT = (
    '................',
    '................',
    '.....SS001......',
    '....S00011.2....',
    '...S001122233...',
    '...00112222333..',
    '..001122223334..',
    '..011222233444..',
    '...1222333444...',
    '....22333444....',
    '.....2334444....',
    '......334.......',
    '................',
)


def iron_scrap(px):
    """Gefaltetes Blech: eine helle Flaeche knickt nach rechts unten weg,
    die Bruchkante ist gezackt, ein Lichtstreif liegt auf dem Knick."""
    t = {'S': ton('stahl', 0), '0': ton('eisen', 0), '1': ton('eisen', 1),
         '2': ton('eisen', 2), '3': ton('eisen', 3), '4': ton('eisen', 4)}
    malen(px, SCHROTT, t)
    for x, y in ((6, 4), (7, 5), (8, 6), (9, 7)):        # Knickkante
        put(px, x, y, ton('stahl', 1))
    for x, y in ((5, 6), (6, 7), (7, 8)):                # Schatten neben dem Knick
        put(px, x, y, ton('eisen', 3))
    funke(px, ((4, 3), (5, 3)), ton('stahl', 0))         # Glanz
    funke(px, ((10, 9), (9, 10)), ton('eisen', 4))


def ore_chunk(px):
    kugel(px, 7.5, 9.0, 6.0, 'holz', flach=0.82)
    for x, y in ((5, 7), (6, 6), (9, 8), (10, 10), (7, 11)):
        put(px, x, y, ton('erz', 1))                     # Erzadern
    for x, y in ((5, 8), (9, 9), (7, 12)):
        put(px, x, y, ton('erz', 3))
    funke(px, ((6, 5),), ton('erz', 0))


def crystal_shard(px):
    kern = []
    for y in range(2, 14):
        w = 1 + (y - 2) // 3 if y < 8 else max(0, 4 - (y - 8) // 2)
        for x in range(7 - w, 8 + w):
            kern.append((x, y))
    for x, y in kern:
        u = (x - 3) / 9.0
        col = ton('kristall', 0 if u < 0.25 else (1 if u < 0.45 else (2 if u < 0.72 else 3)))
        put(px, x, y, col)
    for y in range(3, 13):                               # Facettenkante
        put(px, 8, y, ton('kristall', 1) if y % 3 else ton('kristall', 0))
    funke(px, ((6, 4), (6, 5), (5, 8)), ton('kristall', 0))
    funke(px, ((10, 9), (10, 10), (9, 12)), ton('kristall', 4))
    funke(px, ((4, 11), (11, 5)), ton('kristall', 1))    # Splitter daneben
    for j, (x, y) in enumerate(((6, 3), (6, 4), (7, 5), (7, 6))):     # vordere Facettenkante
        put(px, x, y, ton('kristall', 0))
    for x, y in ((9, 6), (9, 7), (8, 8), (8, 9)):        # hintere Kante im Schatten
        put(px, x, y, ton('kristall', 4))
    for x, y in ((7, 9), (7, 10), (6, 11)):              # Lichtbrechung innen
        put(px, x, y, ton('kristall', 1))


def boss_core(px):
    kugel(px, 7.5, 8.0, 5.6, 'violett')
    for j in range(5):                                   # Rune im Kern
        put(px, 7, 5 + j, ton('violett', 0))
    funke(px, ((6, 6), (8, 6), (6, 10), (8, 10)), ton('violett', 0))
    for x, y in ((3, 4), (12, 5), (2, 9), (13, 10), (7, 1), (7, 14)):
        put(px, x, y, ton('violett', 1))                 # schwebende Splitter
    funke(px, ((3, 5), (12, 6)), ton('violett', 3))


def bone_fragment(px):
    for y in range(4, 12):                               # Schaft schraeg
        x = 4 + (y - 4) // 2
        put(px, x, y, ton('knochen', 1))
        put(px, x + 1, y, ton('knochen', 2))
        put(px, x + 2, y, ton('knochen', 3))
    for cx, cy in ((4, 3), (6, 4), (8, 11), (10, 12)):   # Gelenkkoepfe
        kugel(px, cx + 0.5, cy + 0.5, 1.9, 'knochen')
    funke(px, ((5, 7), (6, 9)), ton('knochen', 0))
    funke(px, ((7, 8), (8, 10)), ton('knochen', 4))


def ember_ash(px):
    kugel(px, 7.5, 10.0, 5.4, 'schatten', flach=0.7)
    for x, y in ((5, 9), (7, 10), (9, 8), (6, 11), (10, 11)):
        put(px, x, y, ton('feuer', 2))                   # Glut in der Asche
    funke(px, ((7, 9), (9, 9)), ton('feuer', 1))
    funke(px, ((6, 4), (9, 3), (8, 5)), ton('feuer', 0))   # aufsteigende Funken
    funke(px, ((6, 5), (9, 4)), ton('feuer', 3))


def frost_core(px):
    kugel(px, 7.5, 8.0, 5.0, 'eis')
    for dx, dy in ((0, -4), (0, 4), (-4, 0), (4, 0), (-3, -3), (3, 3), (-3, 3), (3, -3)):
        put(px, 7 + dx, 8 + dy, ton('eis', 0))           # Frostnadeln
    for dx, dy in ((0, -5), (0, 5), (-5, 0), (5, 0)):
        put(px, 7 + dx, 8 + dy, ton('eis', 2))
    funke(px, ((6, 6), (7, 5)), ton('eis', 0))
    funke(px, ((9, 10), (8, 11)), ton('eis', 4))


def venom_sac(px):
    kugel(px, 7.5, 9.5, 5.4, 'gift', flach=0.85)
    platte(px, 6, 3, 9, 5, 'gift', von=2)                # Hals
    funke(px, ((7, 4), (8, 4)), ton('gift', 3))
    funke(px, ((5, 8), (6, 7)), ton('gift', 0))          # Blasen
    funke(px, ((9, 11), (10, 10)), ton('gift', 4))
    funke(px, ((8, 9), (6, 11)), ton('gift', 1))


def malen(px, karte, farben):
    """Zeichenkarte (16 Zeilen) mit einer Farbtafel malen; '.' bleibt leer."""
    for y, zeile in enumerate(karte):
        for x, c in enumerate(zeile):
            if c != '.':
                put(px, x, y, farben[c])


BAT = (
    '..............',
    '...........AB.',
    '..........1AB.',
    '........11AAB.',
    '.....A1111AAB.',
    '...AA11112ABB.',
    '.AA1111222ABB.',
    'A.112222233AB.',
    '..A122223333B.',
    '...A2222333.B.',
    '....A223333.B.',
    '.....A23333.B.',
    '......A2333.B.',
    '.......AA33.B.',
    '.........AA...',
)


def bat_wing(px):
    """Fledermausfluegel: Arm rechts, drei Fingerknochen strahlen nach links
    unten, dazwischen die Haut - hell an der Vorderkante, dunkel hinten."""
    farben = {'A': ton('knochen', 1), 'B': ton('knochen', 3),
              '1': ton('stoff', 1), '2': ton('stoff', 2), '3': ton('stoff', 3)}
    malen(px, BAT, farben)
    funke(px, ((11, 1), (12, 2)), ton('knochen', 0))     # Glanz am Arm
    funke(px, ((6, 5), (8, 7), (4, 7)), ton('stoff', 0))   # Licht auf der Haut
    funke(px, ((2, 7), (3, 13), (9, 13)), ton('knochen', 0))   # Fingerspitzen


def spider_silk(px):
    kugel(px, 7.5, 8.5, 5.6, 'papier', flach=0.9, von=1)
    for y in range(3, 14):                               # Faeden ueber dem Knaeuel
        for x in range(3, 13):
            if (x + y) % 4 == 0 and px[x, y][3]:
                put(px, x, y, ton('papier', 1))
            elif (x - y) % 5 == 0 and px[x, y][3]:
                put(px, x, y, ton('papier', 3))
    funke(px, ((4, 6), (5, 5)), ton('papier', 0))
    funke(px, ((12, 4), (13, 3), (2, 12)), ton('papier', 2))   # lose Enden


STEIN = (
    '................',
    '................',
    '...00111222.....',
    '..0011122233....',
    '..0111222333....',
    '.01112223333 ...',
    '.01112223333....',
    '.11122233334....',
    '.11222333344....',
    '..1223333444....',
    '..2233334444....',
    '...233344444....',
    '....33444.......',
    '................',
)


def rune_stone(px):
    """Runenstein: flacher Kiesel mit abgerundeten Kanten, die Rune ist tief
    eingeschlagen - dunkle Rille, darunter eine helle Bruchkante."""
    t = {'0': ton('schatten', 0), '1': ton('schatten', 1), '2': ton('schatten', 2),
         '3': ton('schatten', 3), '4': ton('schatten', 4)}
    malen(px, [z.replace(' ', '.') for z in STEIN], t)
    rille = ((4, 4), (4, 5), (5, 6), (6, 7), (7, 8), (7, 9), (8, 5), (7, 6), (6, 9))
    for x, y in rille:                                   # eingeschlagene Rune
        put(px, x, y, ton('violett', 4))
    for x, y in rille:                                   # Lichtkante der Rille
        if px[x, y + 1][3]:
            put(px, x, y + 1, ton('violett', 1))
    funke(px, ((3, 3), (4, 3)), ton('schatten', 0))
    funke(px, ((10, 10), (9, 11)), ton('schatten', 4))


# --- Waehrung und Essenz ------------------------------------------------------------

def gold_coin(px):
    """Muenze: erhabener Rand, eingepraegter Turm, Kerben am Rand - die
    Praegung hat oben eine Lichtkante und unten einen Schatten."""
    kugel(px, 7.5, 8.0, 5.6, 'gold', flach=0.95)
    for x in range(4, 12):                               # erhabener Rand oben und unten
        if px[x, 3][3]:
            put(px, x, 3, ton('gold', 0))
        if px[x, 12][3]:
            put(px, x, 12, ton('gold', 4))
    for j in range(4):                                   # Turm als Praegung
        put(px, 7, 6 + j, ton('gold', 3))
        put(px, 8, 6 + j, ton('gold', 2))
    for x in (6, 9):
        put(px, x, 9, ton('gold', 3))
        put(px, x, 8, ton('gold', 2))
    put(px, 7, 5, ton('gold', 3)); put(px, 8, 5, ton('gold', 1))      # Zinne
    for y in (6, 9):                                     # Kerben am Rand
        put(px, 3, y, ton('gold', 3))
        put(px, 12, y, ton('gold', 4))
    funke(px, ((5, 5), (6, 5)), ton('gold', 0))          # Glanz
    funke(px, ((10, 10), (9, 11)), ton('gold', 4))


def gold_pouch(px):
    kugel(px, 7.5, 10.0, 5.8, 'leder', flach=0.85)
    platte(px, 5, 4, 10, 6, 'leder', von=2)              # Hals mit Schnur
    for x in range(5, 11):
        put(px, x, 5, ton('holz', 3))
    funke(px, ((5, 8), (6, 7)), ton('leder', 0))
    funke(px, ((10, 12), (9, 13)), ton('leder', 4))
    for x in (6, 7, 8):                                  # Muenzen schauen aus dem Hals
        put(px, x, 3, ton('gold', 1) if x < 8 else ton('gold', 2))
    put(px, 7, 2, ton('gold', 0))
    for x in range(5, 11):                               # Schnur um den Hals
        put(px, x, 6, ton('holz', 2) if x < 8 else ton('holz', 3))
    put(px, 4, 6, ton('holz', 1)); put(px, 4, 7, ton('holz', 3))      # Knoten mit Ende
    for y in (9, 10, 11):                                # Naht am Beutel
        put(px, 8, y, ton('leder', 3))
    put(px, 8, 12, ton('leder', 4))
    funke(px, ((6, 9), (5, 10)), ton('leder', 0))        # praller Bauch im Licht


def essence_slime(px):
    platte(px, 4, 4, 11, 13, 'kristall', rund=2, von=1)  # Glas
    for y in range(6, 13):                               # Essenz im Glas
        for x in range(5, 11):
            if (x - 7.5) ** 2 / 9 + (y - 10) ** 2 / 9 <= 1:
                put(px, x, y, ton('gel', 2 if (x + y) % 3 else 1))
    funke(px, ((6, 8), (7, 9)), ton('gel', 0))
    funke(px, ((9, 11), (8, 12)), ton('gel', 3))
    platte(px, 6, 2, 9, 4, 'holz', von=1)                # Korken
    funke(px, ((5, 6), (5, 7)), ton('kristall', 0))      # Glanz auf dem Glas
    funke(px, ((10, 11),), ton('kristall', 1))


def soul_heart(px):
    herz(px, 'seele')
    funke(px, ((3, 4), (12, 5), (7, 1)), ton('seele', 1))    # Seelenfunken
    funke(px, ((3, 5), (12, 6)), ton('seele', 3))


def herz(px, rampe='blut'):
    kugel(px, 5.4, 6.4, 3.6, rampe)
    kugel(px, 10.0, 6.4, 3.6, rampe)
    for y in range(7, 14):                               # Spitze
        w = max(0, 6 - (y - 7))
        for x in range(8 - w, 9 + w):
            nx = (x - 7.7) / 6.0
            ny = (y - 7) / 7.0
            lit = -nx * 0.6 - ny * 0.6 + 0.6
            i = 1 if lit > 0.55 else (2 if lit > 0.2 else (3 if lit > -0.1 else 4))
            put(px, x, y, ton(rampe, i))
    funke(px, ((4, 5), (5, 4)), ton(rampe, 0))           # Glanz
    funke(px, ((11, 9), (10, 11)), ton(rampe, 4))


def red_heart(px):
    herz(px, 'blut')


def half_red_heart(px):
    voll = bild()
    p = voll.load()
    herz(p, 'blut')
    for y in range(G):
        for x in range(8, G):
            p[x, y] = (0, 0, 0, 0)
    for y in range(G):                                   # Schnittkante dunkel
        if p[7, y][3]:
            p[7, y] = ton('blut', 3)
    for y in range(G):
        for x in range(G):
            if p[x, y][3]:
                px[x, y] = p[x, y]


# --- Zugang -------------------------------------------------------------------------

def key(px):
    kugel(px, 5.0, 4.5, 3.4, 'gold')                     # Griffring
    for y in range(3, 7):                                # Ring aushoehlen
        for x in range(4, 7):
            if (x - 5) ** 2 + (y - 4.5) ** 2 <= 1.6:
                put(px, x, y, (0, 0, 0, 0))
    for y in range(7, 14):                               # Schaft
        put(px, 6, y, ton('gold', 1))
        put(px, 7, y, ton('gold', 2 if y % 3 else 3))
    for x, y in ((8, 11), (9, 11), (8, 13), (9, 13)):    # Bart
        put(px, x, y, ton('gold', 2))
    funke(px, ((9, 12), (10, 13)), ton('gold', 3))
    funke(px, ((4, 3), (6, 8)), ton('gold', 0))
    put(px, 5, 4, ton('kristall', 1))                    # Stein im Griff
    put(px, 5, 5, ton('kristall', 2))
    put(px, 4, 5, ton('kristall', 0))
    for x in (6, 7):                                     # Ring unter dem Griff
        put(px, x, 7, ton('gold', 3))
    put(px, 8, 7, ton('gold', 4))
    for x, y in ((8, 12), (9, 12)):                      # zweiter Bart
        put(px, x, y, ton('gold', 3))


def lockpick(px):
    for j in range(10):                                  # Draht
        put(px, 3 + j, 12 - j, ton('stahl', 1))
        put(px, 4 + j, 12 - j, ton('stahl', 3))
    funke(px, ((12, 2), (13, 2), (12, 3)), ton('stahl', 0))   # Haken
    platte(px, 2, 11, 5, 14, 'holz', rund=1)             # Griff
    funke(px, ((3, 12),), ton('holz', 0))


TRUHE = (
    '................',
    '................',
    '....LLLLLLLL....',
    '...LllllllllD...',
    '..bLlllmmmmmDD..',
    '..bllmmmmmmmmD..',
    '..bbmmmmmmmmdD..',
    '..WWWWWWWWWWWW..',
    '..bmmmmKKmmmmD..',
    '..bmmmmKkmmmddD.',
    '..bmmmmmmmmdddD.',
    '..bbdddddddddDD.',
    '...bbddddddddD..',
    '................',
)


def chest(px):
    """Truhe: gewoelbter Deckel, Beschlagband links und rechts, Rahmenleiste
    in der Mitte, Schloss aus Messing - der Deckel wirft Schatten auf den
    Korpus."""
    t = {'L': ton('holz', 0), 'l': ton('holz', 1), 'm': ton('holz', 2),
         'd': ton('holz', 3), 'D': ton('holz', 4),
         'b': ton('eisen', 2), 'W': ton('eisen', 1),
         'K': ton('gold', 1), 'k': ton('gold', 3)}
    malen(px, TRUHE, t)
    for x in range(3, 13):                               # Schlagschatten des Deckels
        put(px, x, 8, dunkler(px[x, 8], 1))
    funke(px, ((4, 3), (5, 3)), ton('holz', 0))          # Lichtkante oben
    funke(px, ((3, 7), (4, 7)), ton('stahl', 1))         # Glanz auf der Leiste
    funke(px, ((12, 11), (12, 12)), ton('holz', 4))
    for y in (8, 9, 10):                                 # Schloss zuletzt: Messing bleibt hell
        put(px, 7, y, ton('gold', 1 if y < 10 else 2))
        put(px, 8, y, ton('gold', 2 if y < 10 else 3))
    put(px, 7, 9, ton('holz', 4))                        # Schluesselloch
    put(px, 7, 8, ton('gold', 0))
    for x, y in ((2, 4), (3, 4), (2, 5), (12, 4), (13, 4), (13, 5)):  # Eckbeschlaege
        put(px, x, y, ton('eisen', 1) if x < 8 else ton('eisen', 3))
    for x, y in ((2, 11), (3, 11), (12, 11), (13, 11)):
        put(px, x, y, ton('eisen', 2) if x < 8 else ton('eisen', 3))
    for x in (5, 9, 11):                                 # Maserung im Holz
        put(px, x, 5, ton('holz', 3))
        put(px, x, 10, ton('holz', 4))
    for y in (8, 9, 10):                                 # Schlossblech
        put(px, 6, y, ton('gold', 3))
        put(px, 9, y, ton('gold', 4))


# --- Verbrauch ----------------------------------------------------------------------

def flasche(px, rampe, fuell_von=7, korken='holz'):
    """Rundkolben mit Hals: Glas hell, Inhalt als Koerper, Glanzstreifen."""
    kugel(px, 7.5, 10.0, 5.2, rampe, flach=0.95, von=1)
    for y in range(fuell_von, 6, -1):                    # Fuellstandskante
        pass
    for x in range(3, 13):                               # Fluessigkeitsspiegel
        if px[x, fuell_von][3]:
            put(px, x, fuell_von, ton(rampe, 0))
    for y in range(4, 7):                                # Hals
        for x in (6, 7, 8):
            put(px, x, y, ton('kristall', 1 if x == 6 else (2 if x == 7 else 3)))
    platte(px, 5, 2, 9, 4, korken, rund=1)               # Korken
    funke(px, ((4, 9), (4, 10), (5, 8)), ton(rampe, 0))  # Glanzstreifen am Glas
    funke(px, ((11, 11), (10, 13)), ton(rampe, 4))
    for x in (5, 6, 7, 8, 9):                            # Halsring aus Messing
        put(px, x, 6, ton('gold', 2) if x < 8 else ton('gold', 3))
    put(px, 5, 6, ton('gold', 1))
    for x in range(5, 11):                               # Etikett quer ueber den Bauch
        put(px, x, 11, ton('papier', 0) if x < 8 else ton('papier', 1))
        put(px, x, 12, ton('papier', 1) if x < 8 else ton('papier', 2))
    for x in (6, 9):                                     # Schrift auf dem Etikett
        put(px, x, 11, ton('papier', 3))
    funke(px, ((8, 9), (9, 8)), ton(rampe, 1))           # Blasen im Sud
    funke(px, ((6, 2), (7, 2)), ton(korken, 0))          # Licht auf dem Korken
    put(px, 5, 4, ton(korken, 1)); put(px, 9, 4, ton(korken, 3))


def health_potion(px):
    flasche(px, 'blut')
    funke(px, ((8, 9), (9, 10)), ton('blut', 1))         # Blasen


def mana_potion(px):
    flasche(px, 'kristall')
    funke(px, ((8, 9), (9, 11)), ton('kristall', 0))


def stamina_potion(px):
    flasche(px, 'gold')
    funke(px, ((8, 10), (6, 12)), ton('gold', 0))


def antidote(px):
    flasche(px, 'gift')
    funke(px, ((8, 10), (6, 12)), ton('gift', 0))


def bomb(px):
    kugel(px, 7.0, 10.0, 5.4, 'schatten')
    platte(px, 6, 3, 9, 5, 'eisen', von=1)               # Zuendstutzen
    for j, (x, y) in enumerate(((9, 2), (10, 1), (11, 1))):  # Lunte
        put(px, x, y, ton('holz', 2))
    funke(px, ((12, 0), (11, 0)), ton('feuer', 1))       # Funke
    put(px, 12, 1, ton('feuer', 0))
    funke(px, ((5, 8), (6, 7)), ton('schatten', 0))
    funke(px, ((10, 12), (9, 13)), ton('schatten', 4))
    for x in range(5, 11):                               # Lichtband ueber der Kugel
        if px[x, 7][3]:
            put(px, x, 7, ton('schatten', 1) if x < 8 else ton('schatten', 2))
    for x in (6, 7, 8, 9):                               # Kragen aus Eisen
        put(px, x, 6, ton('eisen', 2) if x < 8 else ton('eisen', 3))
    put(px, 6, 6, ton('eisen', 1))
    for x, y in ((9, 3), (10, 2)):                       # Lunte geflochten
        put(px, x, y, ton('holz', 1))
    put(px, 10, 3, ton('holz', 3))


ROLLE = (
    '................',
    '................',
    '..RRRRRRRRRRRR..',
    '..rPPPPPPPPPPr..',
    '..rPppppppppPr..',
    '..rPpsssssspPr..',
    '..rPppppppppPr..',
    '..rPpssssspppr..',
    '..rPppppppppPr..',
    '..rPpsssspppPr..',
    '..rPppppppppPr..',
    '..rPPPPPPPPPPr..',
    '..RRRRRRRRRRRR..',
    '...rr......rr...',
    '................',
)


def scroll(px):
    """Schriftrolle: zwei Holzstaebe, dazwischen Pergament, das sich zu den
    Staeben hin woelbt - die Zeilen laufen unregelmaessig aus."""
    t = {'R': ton('holz', 1), 'r': ton('holz', 3),
         'P': ton('papier', 1), 'p': ton('papier', 2), 's': ton('papier', 3)}
    malen(px, ROLLE, t)
    for x in range(3, 13):                               # Woelbung: oben hell
        put(px, x, 4, ton('papier', 0))
        put(px, x, 10, ton('papier', 3))
    for x in (4, 5, 6, 8, 9, 10):                        # Schrift, klar gesetzt
        put(px, x, 6, ton('papier', 4))
    for x in (4, 5, 7, 8, 9):
        put(px, x, 8, ton('papier', 4))
    funke(px, ((3, 2), (4, 2)), ton('holz', 0))          # Glanz auf dem Stab
    funke(px, ((11, 12), (12, 12)), ton('holz', 4))
    for x, y in ((9, 9), (10, 9), (9, 10), (10, 10)):    # Wachssiegel auf dem Blatt
        put(px, x, y, ton('blut', 1))
    put(px, 9, 9, ton('blut', 0))
    put(px, 10, 10, ton('blut', 2))
    put(px, 8, 10, ton('blut', 2)); put(px, 11, 10, ton('blut', 3))     # Wachs laeuft aus


def torch(px):
    for y in range(7, 15):                               # Stiel
        put(px, 7, y, ton('holz', 1))
        put(px, 8, y, ton('holz', 3 if y % 3 else 2))
    platte(px, 6, 6, 9, 8, 'leder', von=1)               # Wicklung
    kugel(px, 7.5, 4.0, 3.4, 'feuer', flach=1.2)         # Flamme
    funke(px, ((7, 1), (8, 2)), ton('feuer', 0))
    funke(px, ((6, 6), (9, 6)), ton('feuer', 3))
    funke(px, ((5, 2), (10, 3)), ton('feuer', 1))        # Funkenflug
    for x, y in ((6, 6), (7, 7), (8, 8), (9, 6), (8, 7)):   # Wicklung kreuzweise
        put(px, x, y, ton('leder', 3))
    put(px, 6, 7, ton('leder', 0)); put(px, 9, 7, ton('leder', 2))
    put(px, 7, 4, ton('feuer', 0))                       # Glutkern
    put(px, 8, 5, ton('feuer', 1))
    for x, y in ((6, 10), (8, 12)):                      # Maserung am Stiel
        put(px, x, y, ton('holz', 3))


def bread(px):
    kugel(px, 7.5, 9.0, 6.0, 'brot', flach=0.75)
    for j, (x, y) in enumerate(((5, 6), (7, 5), (9, 6))):   # Einschnitte
        put(px, x, y, ton('brot', 3))
        put(px, x + 1, y + 1, ton('brot', 4))
    funke(px, ((4, 8), (5, 7)), ton('brot', 0))
    funke(px, ((11, 11), (10, 12)), ton('brot', 4))
    funke(px, ((8, 8), (6, 10)), ton('brot', 1))         # Kruste
    for x, y in ((5, 7), (6, 6), (7, 6), (8, 7)):        # Einschnitt quer
        put(px, x, y, ton('brot', 3))
        put(px, x, y + 1, ton('brot', 0))
    for x, y in ((6, 9), (9, 8), (7, 11)):               # Koerner
        put(px, x, y, ton('holz', 3))
    for x in range(4, 12):                               # Mehlstaub oben
        if px[x, 5][3] and x % 3 == 1:
            put(px, x, 5, ton('brot', 0))


# --- Schmuck ------------------------------------------------------------------------

def power_ring(px):
    for y in range(4, 13):                               # Reif
        for x in range(3, 13):
            d = ((x - 7.5) / 4.6) ** 2 + ((y - 8.5) / 4.2) ** 2
            if 0.45 <= d <= 1.0:
                u = (x - 3) / 9.0 + (y - 4) / 9.0
                put(px, x, y, ton('gold', 1 if u < 0.6 else (2 if u < 1.1 else 3)))
    funke(px, ((4, 7), (5, 6)), ton('gold', 0))
    funke(px, ((11, 11), (10, 12)), ton('gold', 4))
    kugel(px, 7.5, 3.5, 2.8, 'blut')                     # Stein
    for x in (6, 9):                                     # Fassung um den Stein
        put(px, x, 4, ton('gold', 2) if x < 8 else ton('gold', 3))
    put(px, 7, 1, ton('gold', 1)); put(px, 8, 1, ton('gold', 2))
    put(px, 8, 3, ton('blut', 0))                        # Reflex im Stein
    funke(px, ((6, 3),), ton('blut', 0))


def life_amulet(px):
    for j in range(5):                                   # Kette
        put(px, 4 + j, 2 + j, ton('gold', 2))
        put(px, 11 - j, 2 + j, ton('gold', 3))
    platte(px, 5, 6, 10, 12, 'gold', rund=2)             # Fassung
    for y in range(7, 12):                               # Herzstein
        for x in range(6, 10):
            if (x - 7.5) ** 2 / 3.2 + (y - 9) ** 2 / 5.0 <= 1:
                put(px, x, y, ton('blut', 2 if (x + y) % 2 else 1))
    funke(px, ((6, 8),), ton('blut', 0))
    funke(px, ((9, 11),), ton('blut', 4))
    funke(px, ((5, 7),), ton('gold', 0))
    for x, y in ((5, 7), (10, 7), (5, 11), (10, 11)):    # Krallen der Fassung
        put(px, x, y, ton('gold', 1) if x < 8 else ton('gold', 3))
    for j in (1, 3):                                     # Kettenglieder heller
        put(px, 4 + j, 2 + j, ton('gold', 1))
        put(px, 11 - j, 2 + j, ton('gold', 2))


STIEFEL = (
    '................',
    '................',
    '.....LLLL.......',
    '....LllldD......',
    '....LllldD......',
    '....LllldD......',
    '....WWWWWW......',
    '....LllldD......',
    '....Llllldd.....',
    '....Lllllldd....',
    '....Llllllldd...',
    '....SSSSSSSSS...',
    '.....DDDDDDD....',
    '................',
)


def swift_boots(px):
    """Stiefel in Dreiviertelansicht: Schaft mit Umschlag, Spann nach rechts,
    dicke Sohle, daneben ein kleiner Fluegel - der Schaft ist links im Licht."""
    t = {'L': ton('leder', 0), 'l': ton('leder', 1), 'd': ton('leder', 2),
         'D': ton('leder', 3), 'W': ton('holz', 3), 'S': ton('holz', 4)}
    malen(px, STIEFEL, t)
    for y in range(3, 11):                               # Naht am Schaft
        put(px, 6, y, ton('leder', 2))
    funke(px, ((4, 3), (4, 4)), ton('gold', 0))          # Glanz auf dem Leder
    funke(px, ((10, 10), (11, 10)), ton('leder', 3))
    for j, (x, y) in enumerate(((3, 6), (2, 5), (1, 4), (2, 7), (1, 6))):   # Fluegel
        put(px, x, y, ton('kristall', 0 if j < 3 else 1))
    put(px, 0, 5, ton('kristall', 2))
    for y in (4, 6, 8):                                  # Schnuerung
        put(px, 5, y, ton('holz', 3))
        put(px, 7, y, ton('holz', 4))
    put(px, 5, 3, ton('gold', 2)); put(px, 6, 3, ton('gold', 3))      # Schnalle am Schaft
    for x in range(4, 12):                               # Naht ueber der Sohle
        if px[x, 10][3]:
            put(px, x, 10, ton('leder', 3))


KUERASS = (
    '................',
    '....S......S....',
    '...S00S..S11S...',
    '..S0011SS1122S..',
    '...S001MM122S...',
    '...0011MM1223...',
    '...0011MM1223...',
    '...0112MM2233...',
    '...0112MM2233...',
    '....112MM223....',
    '....122MM233....',
    '.....22MM33.....',
    '.....2G33G3.....',
    '......3333......',
    '................',
)


def iron_plate(px):
    """Brustpanzer: zwei Schulterstuecke, dazwischen der Mittelgrat, die
    Platte woelbt sich nach links ins Licht und laeuft nach unten zusammen."""
    t = {'S': ton('eisen', 1), '0': ton('eisen', 0), '1': ton('eisen', 1),
         '2': ton('eisen', 2), '3': ton('eisen', 3),
         'M': ton('stahl', 1), 'G': ton('gold', 2)}
    malen(px, KUERASS, t)
    for y in range(4, 12):                               # Grat: Licht links, Schatten rechts
        put(px, 7, y, ton('stahl', 0) if y < 8 else ton('stahl', 1))
        put(px, 8, y, ton('eisen', 3))
    funke(px, ((4, 3), (3, 5)), ton('stahl', 0))         # Nieten
    funke(px, ((11, 6), (11, 9)), ton('eisen', 4))
    funke(px, ((3, 2), (4, 2)), ton('stahl', 0))         # Licht auf der linken Schulter
    funke(px, ((11, 2), (12, 3)), ton('eisen', 3))       # rechte Schulter im Schatten
    for y in (5, 9):                                     # Nietenreihen
        for x in (4, 11):
            put(px, x, y, ton('stahl', 1) if x < 8 else ton('eisen', 3))
    for x, y in ((5, 12), (6, 12), (9, 12), (10, 12)):   # Riemen am Bauchabschluss
        put(px, x, y, ton('leder', 2) if x < 8 else ton('leder', 3))
    put(px, 7, 12, ton('gold', 2)); put(px, 8, 12, ton('gold', 3))    # Schnalle


def hawk_eye(px):
    for y in range(5, 12):                               # Lidform
        w = int(6.5 - abs(y - 8) * 1.7)
        for x in range(8 - w, 8 + w):
            put(px, x, y, ton('papier', 1 if y < 8 else 2))
    kugel(px, 7.5, 8.0, 3.2, 'gold')                     # Iris
    kugel(px, 7.5, 8.0, 1.6, 'schatten', glanz=False)    # Pupille
    funke(px, ((6, 7),), ton('papier', 0))
    for x in range(2, 14):                               # Lidkanten
        if px[x, 5][3]:
            put(px, x, 5, ton('papier', 3))
        if px[x, 11][3]:
            put(px, x, 11, ton('papier', 4))
    put(px, 3, 7, ton('papier', 3)); put(px, 12, 7, ton('papier', 4))   # Augenwinkel
    for x, y in ((6, 6), (9, 6), (6, 10), (9, 10)):      # Irisring
        put(px, x, y, ton('gold', 3))
    put(px, 6, 7, ton('gold', 0))                        # Reflex
    for x, y in ((4, 4), (11, 4)):                       # Wimpernansatz am Lid
        put(px, x, y, ton('papier', 4))


FANG = (
    '....sssss.......',
    '...sABBBCs......',
    '...ABrrBCC......',
    '...ABrrBCC......',
    '...ABrrBCC......',
    '....ABrBCC......',
    '....ABrBC.......',
    '.....ABrC.......',
    '.....ABrC.......',
    '......ABC.......',
    '......ABC.......',
    '.......AC.......',
    '.......AC.......',
    '.......t........',
    '......ttu.......',
)


def leech_fang(px):
    """Hohlzahn: breite Wurzel im Zahnfleisch, nach unten gebogene Spitze,
    Blutkanal in der Mitte, am Ende ein Tropfen."""
    farben = {'A': ton('knochen', 1), 'B': ton('knochen', 2), 'C': ton('knochen', 3),
              'r': ton('blut', 3), 's': ton('stoff', 2),
              't': ton('blut', 1), 'u': ton('blut', 3)}
    malen(px, FANG, farben)
    funke(px, ((4, 1), (4, 2)), ton('knochen', 0))       # Glanzkante
    funke(px, ((8, 8), (8, 10), (8, 12)), ton('knochen', 4))
    funke(px, ((6, 2), (6, 3)), ton('blut', 2))          # Kanal oben heller


def skull_charm(px):
    kugel(px, 7.5, 7.5, 4.8, 'knochen', flach=0.95)
    for x, y in ((5, 7), (6, 7), (9, 7), (10, 7), (5, 8), (6, 8), (9, 8), (10, 8)):
        put(px, x, y, ton('schatten', 4))                # Augenhoehlen
    put(px, 7, 9, ton('knochen', 3)); put(px, 8, 9, ton('knochen', 4))   # Nase
    for x in range(5, 11):                               # Zahnreihe
        put(px, x, 11, ton('knochen', 1 if x % 2 else 3))
    for j in range(3):                                   # Lederband
        put(px, 4 - j, 3 - j, ton('leder', 2))
        put(px, 11 + j, 3 - j, ton('leder', 3))
    funke(px, ((5, 5), (6, 4)), ton('knochen', 0))
    for x, y in ((6, 4), (6, 5), (7, 6)):                # Riss ueber die Stirn
        put(px, x, y, ton('knochen', 4))
    for x in range(5, 11):                               # Kieferlinie
        if px[x, 10][3]:
            put(px, x, 10, ton('knochen', 3))
    put(px, 5, 12, ton('knochen', 4)); put(px, 10, 12, ton('knochen', 4))


ITEMS = {
    'slime_gel': slime_gel, 'iron_scrap': iron_scrap, 'ore_chunk': ore_chunk,
    'crystal_shard': crystal_shard, 'boss_core': boss_core, 'bone_fragment': bone_fragment,
    'ember_ash': ember_ash, 'frost_core': frost_core, 'venom_sac': venom_sac,
    'bat_wing': bat_wing, 'spider_silk': spider_silk, 'rune_stone': rune_stone,
    'gold_coin': gold_coin, 'gold_pouch': gold_pouch, 'essence_slime': essence_slime,
    'soul_heart': soul_heart, 'red_heart': red_heart, 'half_red_heart': half_red_heart,
    'key': key, 'lockpick': lockpick, 'chest': chest,
    'health_potion': health_potion, 'mana_potion': mana_potion,
    'stamina_potion': stamina_potion, 'antidote': antidote, 'bomb': bomb,
    'scroll': scroll, 'torch': torch, 'bread': bread,
    'power_ring': power_ring, 'life_amulet': life_amulet, 'swift_boots': swift_boots,
    'iron_plate': iron_plate, 'hawk_eye': hawk_eye, 'leech_fang': leech_fang,
    'skull_charm': skull_charm,
}


def bauen(name):
    img = bild()
    px = img.load()
    ITEMS[name](px)
    verzahnen(px)                       # Kontaktschatten zwischen den Teilen
    kernschatten(px)                    # Verdeckung in den Winkeln
    randlicht(px)                       # Streulicht an der Unterkante
    bodenschatten(px)                   # kurzer Schlagschatten
    glaetten(px)                        # Schattierungsrauschen raus, Akzente bleiben
    return duel_anpassen(img, 'kraeftig')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--sheet', action='store_true')
    args = ap.parse_args()
    ziel = Path(args.out)
    ziel.mkdir(parents=True, exist_ok=True)
    bilder = []
    for name in ITEMS:
        img = bauen(name)
        img.save(ziel / ('%s.png' % name))
        bilder.append((name, img))
    print('  %d Items -> %s' % (len(bilder), ziel))
    if args.sheet:
        sc, spalten = 4, 9
        zeilen = (len(bilder) + spalten - 1) // spalten
        blatt = Image.new('RGBA', (spalten * 18 * sc, zeilen * 18 * sc), (34, 35, 35, 255))
        for i, (_, im) in enumerate(bilder):
            blatt.alpha_composite(im.resize((G * sc, G * sc), Image.NEAREST),
                                  ((i % spalten) * 18 * sc + sc, (i // spalten) * 18 * sc + sc))
        blatt.save(ziel / '_vorschau.png')


if __name__ == '__main__':
    main()
