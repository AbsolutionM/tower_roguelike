#!/usr/bin/env python3
"""Spielfiguren im Stil von Sprites/Character/cowboy (32x32, AAP-64).

Vom Cowboy abgelesen (Front1-10, FSide1, Back1):
    Keine Arme. Die Figur ist Hut, Gesicht, Rumpf, Guertel, Hose, zwei
    Stiefel - die Waffe kommt im Spiel dazu.
    Jedes Teil hat drei Toene und eine Kante, Licht von oben links: Krone
    oben hell, die Krempe wirft einen Schattenstreifen aufs Gesicht,
    Gesicht links hell / rechts dunkler, Rumpf an den Flanken dunkler und
    unten links am dunkelsten, Rumpf verjuengt sich zum Guertel.
    Augen sind 2x2-Bloecke in 422433, kein Weiss, kein Schwarz.
    Stiefel: 2 px breit, dunkel + helle Spitze, darunter ein dunkles Pixel.
    Rumpf symmetrisch (die Poncho-Schraege gehoert nur dem Cowboy).
    Laufzyklus ist ein Huepfen: Frame 1 Stand, 2-3 Koerper 1 hoch mit
    gestreckten Beinen, 4 Stand, 5 zwei hoch mit eingezogenen Beinen,
    6 eins hoch eingezogen, 7 nur rechter Fuss unten, 8-9 wie 5-6,
    10 nur linker Fuss unten.

Vier Richtungen (Front, FSide, BSide, Back) mal zehn Frames.
Keine 3-Pixel-Regel - die gilt fuer Waffen.

Ausgabe nur in eigene Ordner:
    python tools/generate_characters.py --out C:/Users/maxst/Desktop/Sprites/claude/Character --sheet
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image

from duel import duel_anpassen


AAP = {
    'schwarz': '060608', 'kohle': '141013', 'nacht': '221c1a',
    'haut_hell': 'fad6b8', 'haut': 'f5a097', 'haut_dk': 'ba756a', 'haut_tief': '8e5252',
    'rot_hell': 'e86a73', 'rot': 'b4202a', 'rot_dk': '73172d', 'wein': '3b1725',
    'braun_hell': 'a08662', 'braun': '796755', 'braun_dk': '5a4e44', 'braun_tief': '423934',
    'erde': '322b28',
    'leder': 'bb7547', 'leder_hell': 'dba463', 'leder_dk': '71413b', 'leder_tief': '5b3138',
    'stahl_hell': 'dae0ea', 'stahl_licht': 'b3b9d1', 'stahl': '8b93af',
    'stahl_dk': '6d758d', 'stahl_tief': '4a5462', 'stahl_kante': '333941', 'stahl_nacht': '242234',
    'blau_hell': '849be4', 'blau': '285cc4', 'blau_dk': '143464', 'himmel': '249fde',
    'gold': 'ffd541', 'gold_dk': 'f9a31b', 'gold_tief': 'fa6a0a', 'weiss': 'ffffff',
    'lila_hell': 'bc4a9b', 'lila': '793a80', 'lila_dk': '403353', 'lila_tief': '242234',
    'gruen_hell': '9cdb43', 'gruen': '59c135', 'gruen_dk': '1a7a3e', 'gruen_tief': '24523b',
    'creme': 'fef3c0', 'sand': 'f4d29c', 'tuerkis': '20d6c7', 'tuerkis_hell': 'a6fcdb',
}


def C(name):
    h = AAP[name]
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


SCHWARZ = C('schwarz')
WEISS = C('weiss')

# Rampen: hell, mitte, dunkel, kante
STAHL = ('stahl_hell', 'stahl_licht', 'stahl', 'stahl_tief')
STAHL_DK = ('stahl_licht', 'stahl', 'stahl_dk', 'stahl_kante')
HAUT = ('haut_hell', 'haut', 'haut_dk', 'haut_tief')
BLAU = ('blau_hell', 'blau', 'blau_dk', 'blau_dk')
LEDER = ('leder_hell', 'leder', 'leder_dk', 'leder_tief')
LILA = ('lila_hell', 'lila', 'lila_dk', 'lila_tief')
LILA_DK = ('lila', 'lila_dk', 'lila_tief', 'lila_tief')
GOLD = ('gold', 'gold_dk', 'gold_tief', 'leder_dk')
GRUEN = ('gruen_hell', 'gruen', 'gruen_dk', 'gruen_tief')
ROT = ('rot_hell', 'rot', 'rot_dk', 'wein')
BRAUN = ('braun_hell', 'braun', 'braun_dk', 'braun_tief')


# --- Figuren -----------------------------------------------------------------

FIGUREN = {
    'knight': dict(
        kopf='helm', kopf_ton=STAHL, haut=HAUT, haar=STAHL_DK,   # hinten: Helmkalotte
        rumpf=STAHL_DK, brust=BLAU, guertel=LEDER, schnalle=('gold_dk', 'gold'),
        hose=BLAU, stiefel=STAHL_DK, bart=None,
    ),
    'mage': dict(
        kopf='hut', kopf_ton=LILA, haut=HAUT, haar=BRAUN,
        rumpf=LILA, brust=None, guertel=GOLD, schnalle=('tuerkis', 'tuerkis_hell'),
        hose=LILA_DK, stiefel=LEDER, bart=('stahl_licht', 'stahl'),
    ),
    'ranger': dict(
        kopf='kapuze', kopf_ton=GRUEN, haut=HAUT, haar=BRAUN,
        rumpf=LEDER, brust=GRUEN, guertel=BRAUN, schnalle=('gold_dk', 'gold'),
        hose=BRAUN, stiefel=LEDER, bart=None,
    ),
}
AUGE = C('wein')            # 422433 wie beim Cowboy


# --- Zeichenkern ---------------------------------------------------------------

def put(px, x, y, col):
    if 0 <= x < 32 and 0 <= y < 32:
        px[x, y] = col


def kuppel(px, cx, cy, rx, ry, ton, oben_nur=False, licht=(-0.55, -0.6)):
    """Ellipsen-Kuppel mit Kugelnormale. Licht von oben links."""
    hell, mitte, dunkel, kante = (C(t) for t in ton)
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            d = nx * nx + ny * ny
            if d > 1.0 or (oben_nur and y + 0.5 > cy):
                continue
            nz = math.sqrt(1.0 - d)
            l = nx * licht[0] + ny * licht[1] + nz * 0.6
            if d > 0.78 and l < 0.45:
                col = kante
            elif l > 0.72:
                col = hell
            elif l > 0.35:
                col = mitte
            else:
                col = dunkel
            put(px, x, y, col)


# Stauchung: im Sprung (Fuesse eingezogen) ist der Rumpf eine Zeile
# kuerzer und die Hosenzeile faellt weg - beim Cowboy ist die Figur in
# Frame 5 fuenf Zeilen kuerzer als im Stand (Beine 3, Rumpf 1, Hose 1).
AKTIV_ZEILEN = 6


def rumpf(px, cx, y0, ton, brust=None, hinten=False, seitlich=0):
    """Rumpf wie der Poncho des Cowboys: sechs Zeilen, oben 11 breit, unten
    9, Flanken dunkel, unten links am dunkelsten (Kante), Licht links.
    brust: Rampe fuer ein Brustfeld in der Mitte (Wappen, Weste)."""
    hell, mitte, dunkel, kante = (C(t) for t in ton)
    # symmetrisch: der Poncho des Cowboys haengt schief, ein Panzer oder
    # Hemd nicht. Schulterlinie hell, Flanken dunkel, Kante aussen, die
    # unterste Zeile im Schatten.
    breiten = (11, 11, 11, 11, 9, 9)[:AKTIV_ZEILEN] if AKTIV_ZEILEN >= 6 else (11, 11, 11, 9, 9)
    for j, b in enumerate(breiten):
        x0 = cx - b // 2
        for i in range(b):
            x = x0 + i
            rand = min(i, b - 1 - i)                   # Abstand zur naeheren Flanke
            if j == 0:
                col = dunkel if rand == 0 else hell
            elif rand == 0:
                col = kante if j >= 2 else dunkel
            elif rand == 1 or j == len(breiten) - 1:
                col = dunkel
            elif j == 1 and rand >= 2:
                col = hell if rand >= 3 else mitte
            else:
                col = mitte
            put(px, x, y0 + j, col)
    if brust and not hinten:
        bh, bm, bd, bk = (C(t) for t in brust)
        for j in range(1, 5):
            halb = 2 if j < 4 else 1
            for dx in range(-halb, halb + 1):
                x = cx + dx + seitlich // 2
                put(px, x, y0 + j, bh if dx < 0 else (bm if dx == 0 else bd))
            put(px, cx - halb - 1 + seitlich // 2, y0 + j, bk)


def guertel(px, cx, y, ton, schnalle, hinten=False):
    hell, mitte, dunkel, kante = (C(t) for t in ton)
    for i in range(9):
        x = cx - 4 + i
        put(px, x, y, kante if i in (0, 8) else mitte)
    if not hinten:
        put(px, cx - 1, y, C(schnalle[0]))
        put(px, cx, y, C(schnalle[1]))
        put(px, cx + 1, y, C(schnalle[0]))


def hose(px, cx, y, ton):
    if AKTIV_ZEILEN < 6:                            # eingezogen: keine Hosenzeile
        return
    hell, mitte, dunkel, kante = (C(t) for t in ton)
    for i in range(9):
        x = cx - 4 + i
        put(px, x, y, kante if i in (0, 8) else (dunkel if i in (1, 7) else mitte))


def stiefel(px, x, y, ton, lang=0, spitze_rechts=False):
    """Ein Stiefel: 2 px breit. Zeile 0 Schaft, Zeile 1 dunkel + weisse
    Spitze, Zeile 2 ein dunkles Pixel unter der Ferse. lang streckt den
    Schaft um weitere Zeilen."""
    hell, mitte, dunkel, kante = (C(t) for t in ton)
    for j in range(1 + lang):
        put(px, x, y + j, dunkel)
        put(px, x + 1, y + j, kante if j == 0 else dunkel)
    yb = y + 1 + lang
    # keine weisse Spitze - die gehoert nur dem Cowboy; die Spitze ist der
    # helle Ton des Stiefels
    if spitze_rechts:
        put(px, x, yb, hell)
        put(px, x + 1, yb, dunkel)
        put(px, x + 1, yb + 1, kante)
    else:
        put(px, x, yb, dunkel)
        put(px, x + 1, yb, hell)
        put(px, x, yb + 1, kante)


def gesicht(px, cx, y0, haut, seitlich=0, hinten=False, haar=None, bart=None):
    """Gesicht 10 breit, 5 Zeilen: Schattenzeile unter der Krempe, links
    hell, rechts dunkel, Kinn dunkel. Augen 2x2 in Wein. seitlich verschiebt
    Augen; hinten zeigt Haar."""
    # 11 breit, mittig auf cx: Licht von oben links, also links hell und
    # rechts dunkel - das ist Beleuchtung, keine schiefe Form
    hh, hm, hd, hk = (C(t) for t in haut)
    x0 = cx - 5
    for j in range(5):
        for i in range(11):
            x = x0 + i
            u = (i + 0.5) / 11
            if j == 4 and (i < 1 or i > 9):
                continue
            if j == 0:
                col = hk if i < 2 or i > 8 else hd        # Krempenschatten
            elif i == 0 or (j == 4 and i == 1):
                col = hk if j > 2 else hd
            elif i == 10 or (j == 4 and i == 9):
                col = hk
            elif j == 4:
                col = hd
            elif u < 0.3:
                col = hh
            elif u > 0.75:
                col = hd
            else:
                col = hm
            put(px, x, y0 + j, col)
    if hinten:
        bh, bm, bd, bk = (C(t) for t in haar)
        for j in range(5):
            for i in range(11):
                x = x0 + i
                if px[x, y0 + j][3]:
                    u = (i + 0.5) / 11
                    put(px, x, y0 + j, bk if i in (0, 10) or j == 4 else (bm if u < 0.6 else bd))
        return
    ey = y0 + 2
    for ex in (cx - 3 + seitlich, cx + 2 + seitlich):
        if x0 < ex < x0 + 10:
            put(px, ex, ey, AUGE)
            put(px, ex + 1, ey, AUGE)
            put(px, ex, ey + 1, AUGE)
    if seitlich:                                       # hinteres Auge verdeckt
        hx = cx - 3 + seitlich if seitlich > 0 else cx + 2 + seitlich
        put(px, hx, ey, hm if seitlich > 0 else hd)
        put(px, hx + 1, ey, hm if seitlich > 0 else hd)
        put(px, hx, ey + 1, hm if seitlich > 0 else hd)
    # Mund: drei Pixel im Kinnton, seitlich mit verschoben
    for dx in (-1, 0, 1):
        put(px, cx + dx + seitlich // 2, y0 + 4, hk)
    if bart:
        b1, b2 = (C(t) for t in bart)
        for i in range(-2, 3):
            put(px, cx + i + seitlich // 2, y0 + 4, b1 if i < 1 else b2)
        put(px, cx + seitlich // 2, y0 + 5, b2)


# --- Kopfbedeckungen -----------------------------------------------------------

def helm(px, cx, y_krempe, ton):
    """Kesselhelm: Kuppel mit breiter Krempe, Nasal in der Mitte."""
    hell, mitte, dunkel, kante = (C(t) for t in ton)
    kuppel(px, cx, y_krempe - 0.5, 5.5, 5.5, ton, oben_nur=True)
    for x in range(cx - 8, cx + 8):
        u = (x - (cx - 8)) / 15.0
        put(px, x, y_krempe, hell if u < 0.35 else (mitte if u < 0.7 else dunkel))
        put(px, x, y_krempe + 1, kante if 0.1 < u < 0.9 else dunkel)
    put(px, cx - 8, y_krempe, kante)
    put(px, cx + 7, y_krempe, kante)
    for j in range(3):                                 # Nasal
        put(px, cx, y_krempe + 2 + j, dunkel)
    put(px, cx - 2, y_krempe - 4, C('stahl_hell'))      # Glanz


def hut(px, cx, y_krempe, ton):
    """Spitzhut: schiefe Spitze, breite Krempe."""
    hell, mitte, dunkel, kante = (C(t) for t in ton)
    hoehe = 9
    for j in range(hoehe):
        t = j / (hoehe - 1)
        halb = 1 + int(round(5.0 * t))
        kipp = int(round((1 - t) * (1 - t) * 3))
        xa, xb = cx - halb + kipp, cx + halb + kipp
        for x in range(xa, xb + 1):
            u = (x - xa) / max(1, xb - xa)
            col = hell if u < 0.35 else (mitte if u < 0.7 else dunkel)
            if x in (xa, xb):
                col = kante
            put(px, x, y_krempe - hoehe + 1 + j, col)
    for x in range(cx - 8, cx + 9):
        u = (x - (cx - 8)) / 16.0
        put(px, x, y_krempe, hell if u < 0.3 else (mitte if u < 0.65 else dunkel))
        put(px, x, y_krempe + 1, kante if 0.05 < u < 0.95 else dunkel)
    put(px, cx - 8, y_krempe, kante)
    put(px, cx + 8, y_krempe, kante)
    put(px, cx - 1, y_krempe - 1, C('gold_dk'))          # Hutband mit Schnalle
    put(px, cx, y_krempe - 1, C('gold'))


def kapuze(px, cx, y_krempe, ton):
    """Kapuze: Kuppel, die seitlich bis auf die Schultern faellt; Oeffnung
    ums Gesicht als dunkler Ring."""
    hell, mitte, dunkel, kante = (C(t) for t in ton)
    kuppel(px, cx, y_krempe + 1.0, 6.5, 7.0, ton, oben_nur=True)
    for j in range(2):
        for x in range(cx - 7 + j, cx + 7 - j):
            put(px, x, y_krempe + j, dunkel if j else mitte)
    for x in range(cx - 4, cx + 4):
        put(px, x, y_krempe + 1, kante)
    put(px, cx - 5, y_krempe + 2, kante)
    put(px, cx + 4, y_krempe + 2, kante)


# --- Laufzyklus ----------------------------------------------------------------
# Vom Cowboy abgelesen: ein Huepfen. (Hub, Fuesse)

SCHRITTE = (
    (0, 'beide'), (-1, 'lang'), (-1, 'lang'), (0, 'beide'), (-2, 'keine'),
    (-1, 'keine'), (0, 'rechts'), (-2, 'keine'), (-1, 'keine'), (0, 'links'),
)
# Seitlich (FSide1-10 des Cowboys): ein echter Schritt. Je Frame Hub und die
# beiden Stiefel als (dx, dy) relativ zur Grundstellung, None = angehoben.
SCHRITTE_SEITE = (
    (0, ((0, 0), (0, 0))),
    (-1, ((-1, 1), (1, 1))),
    (-1, ((-2, 1), (1, 1))),
    (0, ((-1, 0), (1, 0))),
    (0, (None, (1, 0))),
    (-2, (None, None)),
    (-1, ((0, 0), (0, 0))),
    (0, ((1, 0), (-1, 1))),
    (-1, ((1, 1), None)),
    (-2, (None, None)),
)


# Vorlehnen im Schritt: Kopf und Rumpf ruecken ein Pixel nach vorn, die
# Fuesse bleiben - wie der Poncho des Cowboys, der im Schritt nach hinten
# schwingt. Je Seitenframe.
LEHNEN_SEITE = (0, 1, 1, 0, 0, 0, 0, 1, 1, 0)
LEHNEN = 0


def fuss_spec(fuesse):
    """Frontzyklus-Namen in Stiefelpaare uebersetzen."""
    return {'beide': ((0, 0), (0, 0)), 'lang': ((0, 1), (0, 1)), 'keine': (None, None),
            'rechts': (None, (0, 0)), 'links': ((0, 0), None)}[fuesse]


def stiefel_paar(px, cx, y_fuss, ton, paar):
    """Zwei Stiefel symmetrisch unter der Figur: x 12-13 und 17-18 bei cx 15."""
    links, rechts = paar
    cx -= LEHNEN                                    # Fuesse bleiben am Boden
    if links:
        stiefel(px, cx - 3 + links[0], y_fuss + links[1], ton, 0, spitze_rechts=True)
    if rechts:
        stiefel(px, cx + 2 + rechts[0], y_fuss + rechts[1], ton, 0, spitze_rechts=False)


def frame(fig, richtung, nr):
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    px = img.load()
    seite = richtung in ('FSide', 'BSide')
    if seite:
        hub, paar = SCHRITTE_SEITE[nr - 1]
    else:
        hub, fuesse = SCHRITTE[nr - 1]
        paar = fuss_spec(fuesse)
    hinten = richtung in ('Back', 'BSide')
    seitlich = {'Front': 0, 'FSide': 2, 'BSide': -2, 'Back': 0}[richtung]
    global AKTIV_ZEILEN, LEHNEN
    AKTIV_ZEILEN = 5 if paar == (None, None) else 6
    LEHNEN = LEHNEN_SEITE[nr - 1] if seite else 0
    cx = 15 + LEHNEN
    y_krempe = 12 + hub
    y_gesicht = y_krempe + 2
    y_rumpf = y_gesicht + 5
    y_guertel = y_rumpf + AKTIV_ZEILEN
    y_hose = y_guertel + 1
    y_fuss = y_hose + 1

    # Stiefel zuerst, der Rumpf liegt darueber
    stiefel_paar(px, cx, y_fuss, fig['stiefel'], paar)
    hose(px, cx, y_hose, fig['hose'])
    guertel(px, cx, y_guertel, fig['guertel'], fig['schnalle'], hinten=hinten)
    rumpf(px, cx, y_rumpf, fig['rumpf'], fig['brust'], hinten=hinten, seitlich=seitlich)
    gesicht(px, cx, y_gesicht, fig['haut'], seitlich=seitlich, hinten=hinten,
            haar=fig['haar'], bart=fig['bart'])
    {'helm': helm, 'hut': hut, 'kapuze': kapuze}[fig['kopf']](px, cx, y_krempe, fig['kopf_ton'])
    if richtung == 'BSide':
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--sheet', action='store_true')
    args = ap.parse_args()
    wurzel = Path(args.out)
    for name, fig in FIGUREN.items():
        ziel = wurzel / name
        ziel.mkdir(parents=True, exist_ok=True)
        frames = []
        for richtung in ('Front', 'FSide', 'BSide', 'Back'):
            for nr in range(1, 11):
                img = duel_anpassen(frame(fig, richtung, nr))
                img.save(ziel / ('%s%d.png' % (richtung, nr)))
                frames.append(img)
        if args.sheet:
            sc = 4
            blatt = Image.new('RGBA', (10 * 34 * sc, 4 * 34 * sc), (56, 52, 72, 255))
            for i, im in enumerate(frames):
                g = im.resize((32 * sc, 32 * sc), Image.NEAREST)
                blatt.alpha_composite(g, ((i % 10) * 34 * sc + sc, (i // 10) * 34 * sc + sc))
            blatt.save(ziel / '_sheet.png')
        print('  %-10s 40 Frames -> %s' % (name, ziel))


if __name__ == '__main__':
    main()
