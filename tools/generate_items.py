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
            if lit > 0.82 and glanz:
                col = stufen[0]
            elif lit > 0.55:
                col = stufen[1]
            elif lit > 0.2:
                col = stufen[2]
            elif lit > -0.12:
                col = stufen[3]
            else:
                col = stufen[4]
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
    for x, y in punkte:
        oben = (x, y - 1) not in punkte
        links = (x - 1, y) not in punkte
        unten = (x, y + 1) not in punkte
        rechts = (x + 1, y) not in punkte
        if unten or rechts:
            col = stufen[4] if (unten and rechts) else stufen[3]
        elif oben and links:
            col = stufen[0]
        elif oben or links:
            col = stufen[1]
        else:
            col = stufen[2]
        put(px, x, y, col)
    return punkte


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
    kugel(px, 7.5, 9.5, 6.2, 'gel', flach=0.78)
    funke(px, ((5, 6), (6, 5)), ton('gel', 0))
    funke(px, ((10, 12), (11, 11)), ton('gel', 4))
    for x, y in ((4, 4), (11, 6), (9, 3)):               # abspritzende Tropfen
        put(px, x, y, ton('gel', 1))
        put(px, x, y + 1, ton('gel', 3))


def iron_scrap(px):
    platte(px, 3, 5, 11, 10, 'eisen', rund=2)
    funke(px, ((4, 6), (5, 6), (4, 7)), ton('eisen', 0))
    funke(px, ((9, 9), (10, 9), (10, 8)), ton('eisen', 4))
    for x, y in ((6, 5), (8, 10), (11, 7)):              # gezackte Bruchkante
        put(px, x, y, (0, 0, 0, 0))
    funke(px, ((7, 7), (8, 8)), ton('eisen', 3))         # Kratzer
    funke(px, ((6, 8), (9, 6)), ton('stahl', 1))         # blanke Stelle


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


def rune_stone(px):
    platte(px, 3, 3, 12, 12, 'schatten', rund=3)
    for x, y in ((5, 5), (6, 5), (6, 6), (7, 7), (8, 8), (9, 9), (9, 10), (10, 10)):
        put(px, x, y, ton('violett', 1))                 # eingeritzte Rune
    funke(px, ((6, 9), (9, 6)), ton('violett', 0))
    funke(px, ((4, 4), (5, 4)), ton('schatten', 0))
    funke(px, ((11, 11), (10, 11)), ton('schatten', 4))


# --- Waehrung und Essenz ------------------------------------------------------------

def gold_coin(px):
    kugel(px, 7.5, 8.0, 5.6, 'gold', flach=0.95)
    for j in range(5):                                   # Praegung: Stern
        put(px, 7, 5 + j, ton('gold', 3))
    funke(px, ((5, 7), (9, 7), (5, 9), (9, 9)), ton('gold', 3))
    funke(px, ((6, 6), (7, 6)), ton('gold', 0))
    funke(px, ((10, 10), (9, 11)), ton('gold', 4))


def gold_pouch(px):
    kugel(px, 7.5, 10.0, 5.8, 'leder', flach=0.85)
    platte(px, 5, 4, 10, 6, 'leder', von=2)              # Hals mit Schnur
    for x in range(5, 11):
        put(px, x, 5, ton('holz', 3))
    funke(px, ((5, 8), (6, 7)), ton('leder', 0))
    funke(px, ((10, 12), (9, 13)), ton('leder', 4))
    funke(px, ((7, 3), (8, 2), (6, 3)), ton('gold', 1))  # Muenzen oben raus
    funke(px, ((7, 2),), ton('gold', 0))


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


def lockpick(px):
    for j in range(10):                                  # Draht
        put(px, 3 + j, 12 - j, ton('stahl', 1))
        put(px, 4 + j, 12 - j, ton('stahl', 3))
    funke(px, ((12, 2), (13, 2), (12, 3)), ton('stahl', 0))   # Haken
    platte(px, 2, 11, 5, 14, 'holz', rund=1)             # Griff
    funke(px, ((3, 12),), ton('holz', 0))


def chest(px):
    platte(px, 2, 7, 13, 13, 'holz')                     # Korpus
    for x in range(3, 13):                               # Bretterfuge
        put(px, x, 10, ton('holz', 3))
    for y in range(4, 8):                                # Deckel gewoelbt
        w = 6 - (7 - y) // 2
        for x in range(8 - w, 8 + w):
            nx = (x - 7.5) / 6.0
            i = 0 if (nx < -0.3 and y < 6) else (1 if nx < 0.35 else 2)
            put(px, x, y, ton('holz', i))
    for x in (3, 12):                                    # Eisenbaender
        for y in range(4, 14):
            if px[x, y][3]:
                put(px, x, y, ton('eisen', 2 if x < 8 else 3))
    platte(px, 6, 7, 9, 10, 'gold', rund=1)              # Schloss
    put(px, 7, 9, ton('holz', 4)); put(px, 8, 9, ton('holz', 4))
    funke(px, ((6, 8),), ton('gold', 0))
    funke(px, ((4, 5), (5, 5)), ton('holz', 0))
    schatten(px, [(x, 13) for x in range(2, 14)], ton('holz', 4))


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
    funke(px, ((4, 9), (4, 10), (5, 8)), ton(rampe, 0))  # Glanzstreifen
    funke(px, ((11, 11), (10, 13)), ton(rampe, 4))
    funke(px, ((6, 2),), ton(korken, 0))


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


def scroll(px):
    platte(px, 3, 4, 12, 11, 'papier', von=1)            # Blatt
    for y in (6, 8, 10):                                 # Schrift
        for x in range(4, 12):
            if (x + y) % 3:
                put(px, x, y, ton('papier', 4))
    put(px, 11, 6, ton('papier', 2)); put(px, 10, 10, ton('papier', 2))
    for y in range(3, 13):                               # Rollen oben und unten
        pass
    for x in range(2, 14):
        put(px, x, 3, ton('holz', 1 if x < 8 else 2))
        put(px, x, 12, ton('holz', 2 if x < 8 else 3))
    funke(px, ((3, 3), (4, 3)), ton('holz', 0))
    funke(px, ((12, 12), (13, 12)), ton('holz', 4))
    funke(px, ((4, 5), (5, 5)), ton('papier', 0))


def torch(px):
    for y in range(7, 15):                               # Stiel
        put(px, 7, y, ton('holz', 1))
        put(px, 8, y, ton('holz', 3 if y % 3 else 2))
    platte(px, 6, 6, 9, 8, 'leder', von=1)               # Wicklung
    kugel(px, 7.5, 4.0, 3.4, 'feuer', flach=1.2)         # Flamme
    funke(px, ((7, 1), (8, 2)), ton('feuer', 0))
    funke(px, ((6, 6), (9, 6)), ton('feuer', 3))
    funke(px, ((5, 2), (10, 3)), ton('feuer', 1))        # Funkenflug


def bread(px):
    kugel(px, 7.5, 9.0, 6.0, 'brot', flach=0.75)
    for j, (x, y) in enumerate(((5, 6), (7, 5), (9, 6))):   # Einschnitte
        put(px, x, y, ton('brot', 3))
        put(px, x + 1, y + 1, ton('brot', 4))
    funke(px, ((4, 8), (5, 7)), ton('brot', 0))
    funke(px, ((11, 11), (10, 12)), ton('brot', 4))
    funke(px, ((8, 8), (6, 10)), ton('brot', 1))         # Kruste


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


def swift_boots(px):
    for x0 in (2, 8):                                    # zwei Stiefel
        platte(px, x0, 5, x0 + 4, 11, 'leder', rund=1)
        for x in range(x0, x0 + 6):                      # Sohle
            put(px, x, 12, ton('holz', 3 if x < x0 + 3 else 4))
        put(px, x0 + 5, 11, ton('leder', 3))
        funke(px, ((x0 + 1, 6),), ton('leder', 0))
        funke(px, ((x0 + 3, 9), (x0 + 3, 10)), ton('leder', 3))
    funke(px, ((1, 4), (0, 6), (7, 3)), ton('kristall', 1))   # Windstriche
    funke(px, ((1, 5),), ton('kristall', 0))


def iron_plate(px):
    for y in range(3, 14):                               # Brustplatte
        w = int(5.5 - abs(y - 7) * 0.25) if y < 11 else 5 - (y - 10)
        for x in range(8 - w, 8 + w):
            u = (x - (8 - w)) / (2.0 * w)
            i = 0 if (u < 0.18 and y < 6) else (1 if u < 0.42 else (2 if u < 0.72 else 3))
            put(px, x, y, ton('eisen', i))
    for y in range(4, 13):                               # Mittelgrat
        put(px, 7, y, ton('stahl', 1))
        put(px, 8, y, ton('eisen', 3))
    funke(px, ((4, 4), (11, 4)), ton('eisen', 4))        # Schulterkanten
    funke(px, ((5, 6), (10, 9)), ton('stahl', 0))        # Nieten


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
    funke(px, ((3, 4), (12, 4)), ton('papier', 3))       # Wimpern


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
    ITEMS[name](img.load())
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
        blatt = Image.new('RGBA', (spalten * 18 * sc, zeilen * 18 * sc), (23, 21, 22, 255))
        for i, (_, im) in enumerate(bilder):
            blatt.alpha_composite(im.resize((G * sc, G * sc), Image.NEAREST),
                                  ((i % spalten) * 18 * sc + sc, (i // spalten) * 18 * sc + sc))
        blatt.save(ziel / '_vorschau.png')


if __name__ == '__main__':
    main()
