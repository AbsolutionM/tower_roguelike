#!/usr/bin/env python3
"""Menschliche und untote Gegner nach der Vorlage Sprites/Character/template.

Die Vorlage ist ein Strichmaennchen in drei Farben: Kopf (f8c53a), Rumpf
(d5dc1d), Beine (494182), 32x32, zehn Frames je Richtung:
    Back      Front und Back (gleich): Huepf-Zyklus, Beine als Block plus
              zwei duenne Striche
    TFSide    vorne + seitlich (Laufrichtung unten rechts/links)
    TBSide    hinten + seitlich (Laufrichtung oben rechts/links)
Masse: Kopf 10x7, Rumpf 8x4 + Hueften 6x2, Beinblock 6x2, Fuesse 1 px.

Die Masken werden je Frame eingelesen; Proportionen und Bewegung bleiben
die der Vorlage, nur die Ecken werden gerundet (Kopf, Schultern, Kiefer,
Kapuze). Gemalt wird als Koerper, nicht als Flaeche: der Kopf als
Ellipsoid, Rumpf und Hueften als Zylinder mit Schulterlicht und dem
Schatten des Kopfes, Licht von oben links vorne; die Hose als zwei Roehren,
die Fuesse mit Stiefelspitze wie beim Cowboy. Darauf die Merkmale:

    zombie            graugruene Haut, Haarbueschel, hohle Augen, offener Mund,
                      zerrissenes Hemd mit Naht und Loechern
    skeleton_warrior  Schaedel mit Kiefer und Rostkappe, Brustkorb, Becken
    ghoul             lila-graue Haut, Ohren, Glutaugen, Zahnreihe, Rippen,
                      lange Krallenarme neben dem Rumpf
    cultist           spitze Kapuze, Gesicht im Schatten, Robe mit Falten,
                      Strickguertel, Augensymbol
    mummy             Bandagen in Lagen, Augenschlitz, lose Enden
    bandit            Kopftuch, Augenklappe, Halstuch, Lederweste, Dolch
    wight             Topfhelm mit Sehschlitz, Brustpanzer, Umhang
    hag               Spitzhut mit Krempe, Hakennase, Robe mit Beutel
    brute             breiter Oberkoerper, Eisenmaske, Narben

Ausgabe je Gegner: Front1-10, FSide1-10, BSide1-10, Back1-10, dazu
attack (6), hurt (4), death (6) aus den Vorlagenposen abgeleitet.

    python tools/generate_humanoids.py --out C:/Users/maxst/Desktop/Sprites/claude/Enemies --sheet
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image

from palette import duel_anpassen

VORLAGE = Path('C:/Users/maxst/Desktop/Sprites/Character/template')
KOPF_M, RUMPF_M, BEIN_M = (248, 197, 58), (213, 220, 29), (73, 65, 130)

# Splendor128-Toene: hell, mitte, dunkel, kante
T = {
    'moder': ('b5e7cb', '86c69a', '5d9b79', '2c3b39'),
    'lumpen': ('b29476', '886e6a', '594d4d', '322f35'),
    'hosen': ('594d4d', '36282b', '2a1e23', '171516'),
    'bein': ('f1ebdb', 'ddcebf', 'bda499', '886e6a'),
    'beinhose': ('ddcebf', 'bda499', '886e6a', '594d4d'),
    'beinstiefel': ('bda499', '886e6a', '594d4d', '33272a'),
    'rost': ('c5c7dd', '9a97b9', '696682', '2c3438'),
    'ghul': ('c090a9', '966888', '654956', '36282b'),
    'ghulhose': ('654956', '36282b', '2a1e23', '171516'),
    'robe': ('b25266', '64364b', '36282b', '2a1e23'),
    'binde': ('fcf7be', 'f1ebdb', 'ddcebf', 'b29476'),
    'bindestiefel': ('ddcebf', 'bda499', 'b29476', '886e6a'),
    'haut': ('ffe0b7', 'eeb59c', 'b28b78', '886e6a'),
    'tuch': ('b25266', '64364b', '2a1e23', '171516'),
    'leder': ('e1bf89', 'b47538', '724b2c', '4f342f'),
    'haar': ('4f342f', '36282b', '2a1e23', '171516'),
    'stiefel': ('594d4d', '36282b', '2a1e23', '171516'),
    'ruestung': ('c9d4fd', '9a97b9', '696682', '2c3438'),
    'umhang': ('7864c6', '494182', '282c3c', '14121d'),
    'hexhaut': ('939446', '7f8e44', '586335', '333c24'),
    'hexrobe': ('9c8bdb', '7864c6', '494182', '282c3c'),
    'huene': ('e2b27e', 'c68556', '8c5b3e', '4f342f'),
    'huenehose': ('724b2c', '4f342f', '2d1b1e', '171516'),
    'narbe': ('e27285', 'b25266', '64364b', '2a1e23'),
}
NACHT = '171516'
SCHWARZ = '0e0c0c'
GLUT, GLUT_DK, KRALLE, AUGE = 'fff089', 'e88a36', 'f1f2ff', '36282b'

# Was augen() gesetzt hat, wird danach weder ueberzeichnet noch geglaettet -
# sonst sehen die Augen je nach Helm, Tuch oder Maske anders aus.
AUGENPIXEL = set()


def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def ton(name):
    return tuple(rgb(c) for c in T[name])


def put(px, x, y, col):
    if 0 <= x < 32 and 0 <= y < 32 and (x, y) not in AUGENPIXEL:
        px[x, y] = col


# --- Vorlage lesen ---------------------------------------------------------------

def maske(richtung, nr):
    """Kopf-, Rumpf- und Beinpixel eines Vorlagenframes."""
    datei = {'Front': 'Back', 'Back': 'Back', 'FSide': 'TFSide', 'BSide': 'TBSide'}[richtung]
    im = Image.open(VORLAGE / ('%s%d.png' % (datei, nr))).convert('RGBA')
    px = im.load()
    teile = {'kopf': set(), 'rumpf': set(), 'beine': set()}
    for y in range(32):
        for x in range(32):
            c = px[x, y]
            if not c[3]:
                continue
            if c[:3] == KOPF_M:
                teile['kopf'].add((x, y))
            elif c[:3] == RUMPF_M:
                teile['rumpf'].add((x, y))
            elif c[:3] == BEIN_M:
                teile['beine'].add((x, y))
    return teile


def kasten(punkte):
    xs = [p[0] for p in punkte]
    ys = [p[1] for p in punkte]
    return min(xs), min(ys), max(xs), max(ys)


def ecken(punkte, oben=1, unten=1):
    """Ecken der Kastenform abrunden: je Ecke `oben`/`unten` Pixel weg."""
    x0, y0, x1, y1 = kasten(punkte)
    weg = set()
    for i in range(oben):
        for j in range(oben - i):
            weg.add((x0 + i, y0 + j)); weg.add((x1 - i, y0 + j))
    for i in range(unten):
        for j in range(unten - i):
            weg.add((x0 + i, y1 - j)); weg.add((x1 - i, y1 - j))
    return punkte - weg


def kapuze(punkte):
    """Kopfmaske als Kapuze: oben spitz zulaufend, unten breit."""
    x0, y0, x1, y1 = kasten(punkte)
    aus = set()
    for x, y in punkte:
        j = y - y0
        e = max(0, 3 - j)                                    # Zeile 0: 3 weg, 1: 2, 2: 1
        if x0 + e <= x <= x1 - e:
            aus.add((x, y))
    return aus


def schultern(punkte):
    """Rumpf: obere Ecken weg (Schultern), Hueften bleiben."""
    x0, y0, x1, y1 = kasten(punkte)
    return punkte - {(x0, y0), (x1, y0)}


INDEX = {}                              # Farbe -> (Tonreihe, Stufe)
for _n, _r in T.items():
    for _i, _h in enumerate(_r):
        INDEX.setdefault(rgb(_h), (_n, _i))


def reihe_von(col):
    return INDEX.get(col, (None, 0))[0]


def aufraeumen(img):
    """Nimmt heraus, was zufaellig aussieht: ein Pixel, dessen Farbe bei
    keinem der acht Nachbarn vorkommt und das zur selben Tonreihe wie seine
    Umgebung gehoert, ist Rauschen und wird zur haeufigsten Nachbarfarbe.
    Bewusst gesetzte Akzente aus einer anderen Reihe (Auge, Niete, Glut)
    bleiben. Dazu fliegen lose Teile bis zwei Pixel ohne Anschluss raus."""
    px = img.load()
    for _ in range(2):
        alt = [[px[x, y] for x in range(32)] for y in range(32)]
        for y in range(32):
            for x in range(32):
                c = alt[y][x]
                if not c[3] or (x, y) in AUGENPIXEL:
                    continue
                nb = []
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx or dy:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < 32 and 0 <= ny < 32 and alt[ny][nx][3]:
                                nb.append(alt[ny][nx])
                if not nb or any(q == c for q in nb):
                    continue
                eigen = reihe_von(c)
                if eigen is None:
                    continue                        # Akzent (Glut, Zahn, Auge) bleibt
                if all(reihe_von(q) != eigen for q in nb):
                    continue                        # Material liegt allein auf, kein Rauschen
                gleiche = [q for q in nb if reihe_von(q) == eigen] or nb
                px[x, y] = max(set(gleiche), key=gleiche.count)
    gesehen, teile = set(), []
    for y in range(32):
        for x in range(32):
            if (x, y) in gesehen or not px[x, y][3]:
                continue
            stapel, teil = [(x, y)], []
            gesehen.add((x, y))
            while stapel:
                cx, cy = stapel.pop()
                teil.append((cx, cy))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        nx, ny = cx + dx, cy + dy
                        if (0 <= nx < 32 and 0 <= ny < 32 and (nx, ny) not in gesehen
                                and px[nx, ny][3]):
                            gesehen.add((nx, ny))
                            stapel.append((nx, ny))
            teile.append(teil)
    if teile:
        teile.sort(key=len, reverse=True)
        for teil in teile[1:]:
            if len(teil) <= 2:
                for x, y in teil:
                    px[x, y] = (0, 0, 0, 0)
    return img


# --- Beleuchtung --------------------------------------------------------------------

LICHT = (-0.55, -0.55, 0.62)          # von links oben vorne


def stufe(lit, toene, grenzen):
    hell, mitte, dunkel, kante = toene
    if lit > grenzen[0]:
        return hell
    if lit > grenzen[1]:
        return mitte
    if lit > grenzen[2]:
        return dunkel
    return kante


def ellipsoid(px, punkte, toene, grenzen=(0.5, 0.15, -0.22), glanz=None):
    """Kugelbeleuchtung ueber die Maske: Normale aus der Ellipse der Maske."""
    x0, y0, x1, y1 = kasten(punkte)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0 + 1) / 2, (y1 - y0 + 1) / 2
    for x, y in punkte:
        nx, ny = (x - cx) / rx, (y - cy) / ry
        nz = math.sqrt(max(0.0, 1 - min(1.0, nx * nx + ny * ny)))
        lit = nx * LICHT[0] + ny * LICHT[1] + nz * LICHT[2]
        put(px, x, y, stufe(lit, toene, grenzen))
    if glanz:
        gx, gy = int(cx - rx * 0.4), int(cy - ry * 0.45)
        for dx, dy in ((0, 0), (1, 0)):
            if (gx + dx, gy + dy) in punkte:
                put(px, gx + dx, gy + dy, glanz)


def zylinder(px, punkte, toene, kopfschatten=True, grenzen=(0.48, 0.12, -0.22)):
    """Rumpf mit Hueften: Zylinder um die Hochachse je Zeile, Schultern
    nach oben beleuchtet, Kopfschatten ueber die Brust, Saum im Schatten."""
    x0, y0, x1, y1 = kasten(punkte)
    zeilen = {}
    for x, y in punkte:
        zeilen.setdefault(y, []).append(x)
    for x, y in punkte:
        zx0, zx1 = min(zeilen[y]), max(zeilen[y])
        cx = (zx0 + zx1) / 2
        rx = (zx1 - zx0 + 1) / 2
        nx = (x - cx) / rx
        nz = math.sqrt(max(0.0, 1 - nx * nx))
        ny = -0.5 if (x, y - 1) not in punkte else 0.0
        if (x, y + 1) not in punkte:
            ny = 0.5
        lit = nx * LICHT[0] + ny * LICHT[1] + nz * LICHT[2]
        if kopfschatten and y == y0 and abs(x - cx) < 2.5:
            lit -= 0.5
        put(px, x, y, stufe(lit, toene, grenzen))


def beine_malen(px, punkte, hose, stiefel):
    """Beinblock als zwei Roehren mit Schritt in der Mitte, die duennen
    Striche als Bein, die unterste Zeile als Stiefel mit Spitze nach aussen
    (wie beim Cowboy)."""
    if not punkte:                                          # Tod: im Boden versunken
        return
    hh, hm, hd, hk = hose
    sh, sm, sd, sk = stiefel
    x0, y0, x1, y1 = kasten(punkte)
    zeilen = {}
    for x, y in punkte:
        zeilen.setdefault(y, []).append(x)
    for x, y in punkte:
        xs = zeilen[y]
        if len(xs) >= 5:                                    # Block: Hose
            bx0, bx1 = min(xs), max(xs)
            cx = (bx0 + bx1) / 2
            w = bx1 - bx0 + 1
            oben = (x, y - 1) not in punkte
            if x == bx1:
                col = hk
            elif x == bx0:
                col = hd
            elif w > 7:                                     # ausgestrecktes Bein: eine Roehre
                col = hm if oben else hd
            elif abs(x - cx) < 0.6:
                col = hk
            elif x < cx:
                col = hh if (oben and x > bx0 + 1) else hm
            else:
                col = hm if (x - cx) < 1.6 else hd
            put(px, x, y, col)
        else:                                               # Strich: Bein, unten Stiefel
            unten = (x, y + 1) not in punkte
            links = x < (x0 + x1) / 2
            if unten:
                put(px, x, y, sd)
                put(px, x + (-1 if links else 1), y, sk)    # Stiefelspitze nach aussen
            else:
                put(px, x, y, hm if links else hd)


# --- Merkmale ------------------------------------------------------------------------

def tupfen(px, punkte, stellen, col, x0=None, y0=None):
    if x0 is None:
        x0, y0, _, _ = kasten(punkte)
    for dx, dy in stellen:
        if (x0 + dx, y0 + dy) in punkte:
            put(px, x0 + dx, y0 + dy, col)


AUGENZEILE = 3                          # gleiche Zeile im Kopf bei jeder Figur


def augen(px, kopf, seitlich, haut, art='klar', iris=None, verdeckt=None):
    """Das Augenpaar ist bei allen Figuren gleich gebaut: dieselbe Zeile,
    2 px breit, 2 px hoch, vier Pixel Abstand, darueber eine Braue und
    darunter ein Wangenschatten. Nur das Material wechselt:

        klar    helle Lederhaut, Iris zur Nasenseite
        hohl    leere Hoehle, unten am tiefsten
        glut    Hoehle mit einem Glutpunkt

    In der Seitenansicht schaut der Kopf nach links: die Zuege ruecken nach
    links, das vordere (linke) Auge bleibt 2 px breit, das hintere (rechte)
    wird 1 px schmal, weil es vom Kopf angeschnitten ist."""
    x0, y0, x1, y1 = kasten(kopf)
    z = y0 + AUGENZEILE
    hh, hm, hd, hk = haut
    li, re = x0 + 2 + seitlich, x0 + 6 + seitlich
    gesetzt = []
    for ex in (li, re):
        if verdeckt == ('li' if ex == li else 're'):
            continue                                     # Klappe, Binde, Straehne
        hinteres = seitlich != 0 and ex == re            # rechtes Auge liegt hinten
        breite, ax = (1, ex + 1) if hinteres else (2, ex)
        for dx in range(breite):
            for dy in (0, 1):
                if (ax + dx, z + dy) in kopf:
                    put(px, ax + dx, z + dy, rgb('f1ebdb') if art == 'klar' else rgb(NACHT))
                    gesetzt.append((ax + dx, z + dy))
        if seitlich:
            innen = ax                                       # Blick nach links
        else:
            innen = ax + 1 if ex == li else ax               # Iris zur Nase hin
        if art == 'klar':
            put(px, innen, z, iris or rgb(AUGE))
            put(px, innen, z + 1, rgb(AUGE))
        elif art == 'glut':
            put(px, innen, z, iris or rgb(GLUT))
            put(px, innen, z + 1, rgb(GLUT_DK))
        else:
            put(px, ax, z + 1, rgb(SCHWARZ))                 # Hoehle unten am tiefsten
        for dx in range(breite):
            if (ax + dx, z - 1) in kopf:
                put(px, ax + dx, z - 1, hd)                  # Braue
            if (ax + dx, z + 2) in kopf:
                put(px, ax + dx, z + 2, hd)                  # Wangenschatten
    AUGENPIXEL.update(gesetzt)
    return li, re


def haar_hinten(px, kopf, toene):
    hh, hm, hd, hk = toene
    ellipsoid(px, kopf, toene, grenzen=(0.58, 0.22, -0.15))
    tupfen(px, kopf, ((2, 1), (3, 2), (5, 1), (6, 2), (2, 4), (7, 4), (4, 5)), hh)
    tupfen(px, kopf, ((1, 6), (3, 6), (6, 6), (8, 6)), hk)


def haut_kopf(px, kopf, haut, seitlich, hinten, haar=None, glanz=True):
    hh, hm, hd, hk = haut
    if hinten:
        if haar:
            haar_hinten(px, kopf, haar)
        else:
            ellipsoid(px, kopf, haut)
        return
    ellipsoid(px, kopf, haut, glanz=hh if glanz else None)
    x0, y0, x1, y1 = kasten(kopf)
    for dx, dy in ((7, 4), (8, 4), (8, 3), (7, 5)):                 # Wangenschatten rechts
        if (x0 + dx + seitlich, y0 + dy) in kopf:
            put(px, x0 + dx + seitlich, y0 + dy, hd)
    for dx in (2, 3, 6, 7):                                         # Brauen
        if (x0 + dx + seitlich, y0 + 2) in kopf:
            put(px, x0 + dx + seitlich, y0 + 2, hd)
    put(px, x0 + 5 + seitlich, y0 + 4, hd)                          # Nasenschatten
    put(px, x0 + 4 + seitlich, y0 + 4, hh)


# --- Gegner: Kopf, Rumpf, Extras ------------------------------------------------------

def zombie(px, m, seitlich, hinten, frame):
    haut = ton('moder')
    lumpen = ton('lumpen')
    lh, lm, ld, lk = lumpen
    beine_malen(px, m['beine'], ton('hosen'), ton('stiefel'))
    r = schultern(m['rumpf'])
    zylinder(px, r, lumpen)
    x0, y0, x1, y1 = kasten(r)
    tupfen(px, r, ((1, 2), (2, 3), (6, 1), (5, 2)), ld, x0, y0)       # Falten zur Mitte
    tupfen(px, r, ((2, 1), (6, 0)), lh, x0, y0)
    tupfen(px, r, ((5, 3), (6, 3)), haut[2], x0, y0)                  # Loch mit Haut
    tupfen(px, r, ((6, 4),), haut[3], x0, y0)
    tupfen(px, r, ((1, 4), (2, 4)), haut[2], x0, y0)                  # Riss im Hemd
    tupfen(px, r, ((1, 5), (2, 5)), haut[3], x0, y0)
    tupfen(px, r, ((3, 0), (3, 1)), lk, x0, y0)                       # offene Naht
    tupfen(px, r, ((4, 1),), lh, x0, y0)
    for x in range(x0, x1 + 1):                                       # zerfetzter Saum
        if (x, y1) in r and x % 2 == 0:
            put(px, x, y1, lk)
    k = ecken(m['kopf'])
    haut_kopf(px, k, haut, seitlich, hinten, haar=ton('haar'))
    kx0, ky0, kx1, ky1 = kasten(k)
    bh, bm, bd, bk = ton('haar')
    if hinten:
        for dx, dy in ((3, 3), (4, 3), (4, 4)):                       # kahle Stelle am Hinterkopf
            put(px, kx0 + dx, ky0 + dy, haut[3])
    else:
        for dx, dy in ((1, 4), (1, 5), (2, 5)):                       # Faeule als Fleck,
            put(px, kx0 + dx, ky0 + dy, haut[2])                      # nicht als Streusel
        put(px, kx0 + 1, ky0 + 6, haut[3])
        li, re = augen(px, k, seitlich, haut, art='hohl')
        put(px, li, ky0 + 6, haut[3])                                 # eingefallene Wangen
        put(px, re + 1, ky0 + 6, haut[3])
        for dx in range(3):                                           # offener Mund, ein Zahn
            put(px, kx0 + 3 + dx + seitlich, ky0 + 5 + (1 if dx == 2 else 0), rgb(NACHT))
        put(px, kx0 + 4 + seitlich, ky0 + 5, rgb('ddcebf'))
        put(px, kx0 + 6 + seitlich, ky0 + 6, haut[3])                 # haengender Winkel
    for dx in range(0, 10):                                           # Haarkappe, geschlossen
        put(px, kx0 + dx, ky0, bm if dx < 5 else bd)
        put(px, kx0 + dx, ky0 + 1, bh if dx < 3 else (bm if dx < 7 else bd))
    for dx in (1, 4, 7):                                              # Struhnen stehen ab
        put(px, kx0 + dx, ky0 - 1, bm)
    put(px, kx0 - 1, ky0 + 1, bd)                                     # Haar faellt seitlich
    put(px, kx1 + 1, ky0 + 1, bk)
    put(px, kx0 - 1, ky0 + 2, bk)
    put(px, kx1 + 1, ky0 + 2, bk)


def skeleton(px, m, seitlich, hinten, frame):
    bein = ton('bein')
    beine_malen(px, m['beine'], ton('beinhose'), ton('beinstiefel'))
    if m['beine']:                                                    # Becken: Kerben oben
        bx0, by0, bx1, by1 = kasten(m['beine'])
        tupfen(px, m['beine'], ((1, 0), (4, 0)), bein[3], bx0, by0)
        tupfen(px, m['beine'], ((2, 0), (3, 0)), bein[0], bx0, by0)
    r = schultern(m['rumpf'])
    x0, y0, x1, y1 = kasten(r)
    cx = (x0 + x1 + 1) // 2                                           # 16
    if hinten:
        zylinder(px, r, bein)
        for y in range(y0, y1 + 1):                                   # Wirbelsaeule
            put(px, cx - 1, y, bein[3] if y % 2 else bein[2])
            put(px, cx, y, bein[2] if y % 2 else bein[1])
        for j in (1, 3):                                              # Rippen von hinten
            for dx in (2, 3):
                if (cx - dx, y0 + j) in r:
                    put(px, cx - dx, y0 + j, bein[2])
                if (cx + dx - 1, y0 + j) in r:
                    put(px, cx + dx - 1, y0 + j, bein[3])
    else:
        for x, y in r:                                                # dunkler Brustraum
            rand_ = (x - 1, y) not in r or (x + 1, y) not in r
            put(px, x, y, bein[3] if rand_ else rgb(NACHT))
        for y in range(y0, y1 + 1):                                   # Brustbein
            put(px, cx - 1, y, bein[1] if y % 2 else bein[0])
            put(px, cx, y, bein[2] if y % 2 else bein[1])
        for j in (0, 2, 4):                                           # Rippenboegen, je zwei Pixel
            for dx in (2, 3):
                if (cx - dx, y0 + j) in r:
                    put(px, cx - dx, y0 + j, bein[0] if dx == 2 else bein[1])
                if (cx + dx - 1, y0 + j) in r:
                    put(px, cx + dx - 1, y0 + j, bein[1] if dx == 2 else bein[2])
            for dx in (3, 4):                                         # Bogen faellt nach aussen ab
                if (cx - dx, y0 + j + 1) in r:
                    put(px, cx - dx, y0 + j + 1, bein[1])
                if (cx + dx - 1, y0 + j + 1) in r:
                    put(px, cx + dx - 1, y0 + j + 1, bein[2])
        put(px, cx - 2, y0, bein[0]); put(px, cx + 1, y0, bein[1])   # Schluesselbeine
    k = ecken(m['kopf'], oben=1, unten=2)                             # Schaedel: schmaler Kiefer
    ellipsoid(px, k, bein, grenzen=(0.42, 0.08, -0.25))
    kx0, ky0, kx1, ky1 = kasten(k)
    if not hinten:
        li, re = augen(px, k, seitlich, bein, art='glut', iris=rgb('b25266'))
        put(px, li, ky0 + 5, bein[2]); put(px, li + 1, ky0 + 5, bein[0])    # Wangenknochen
        put(px, re, ky0 + 5, bein[2]); put(px, re + 1, ky0 + 5, bein[0])
        put(px, kx0 + 4 + seitlich, ky0 + 5, bein[3])                 # Nasenloch
        for x in range(kx0 + 2, kx0 + 8):                             # Kiefer: dunkler Spalt
            if (x + seitlich, ky0 + 6) in k:
                put(px, x + seitlich, ky0 + 6, bein[3])
        for dx in (2, 3, 5, 6):                                       # Zaehne paarweise
            if (kx0 + dx + seitlich, ky0 + 6) in k:
                put(px, kx0 + dx + seitlich, ky0 + 6, bein[0])
    else:
        tupfen(px, k, ((3, 2), (4, 3), (5, 4), (6, 3), (2, 5)), bein[3], kx0, ky0)    # Naehte
        tupfen(px, k, ((3, 3), (6, 4)), bein[0], kx0, ky0)
    for dx, dy in ((1, 1), (1, 2), (0, 2)):                           # Riss an der Schlaefe
        put(px, kx0 + dx, ky0 + dy, bein[3])
    tupfen(px, k, ((3, 1), (4, 1)), bein[0], kx0, ky0)                # Stirnwoelbung
    rost = ton('rost')
    for x, y in k:                                                    # Kappe: obere zwei Zeilen
        if y <= ky0 + 1:
            u = (x - kx0) / (kx1 - kx0)
            put(px, x, y, rost[0] if (u < 0.45 and y == ky0) else (rost[1] if u < 0.65 else rost[2]))
    for dx in (2, 5, 8):                                              # Nietenreihe am Kappenrand
        put(px, kx0 + dx, ky0 + 1, rgb('e6e7f0'))
    for dx in (3, 4):                                                 # Rostfleck, zusammenhaengend
        put(px, kx0 + dx, ky0, rgb('b47538'))
    put(px, kx0 + 1, ky0 + 1, rost[3]); put(px, kx1 - 1, ky0 + 1, rost[3])


def ghoul(px, m, seitlich, hinten, frame):
    haut = ton('ghul')
    hh, hm, hd, hk = haut
    beine_malen(px, m['beine'], ton('ghulhose'), ton('stiefel'))
    r = schultern(m['rumpf'])
    zylinder(px, r, haut)
    x0, y0, x1, y1 = kasten(r)
    cx = (x0 + x1 + 1) // 2
    if hinten:                                                        # Wirbelhoecker
        for y in range(y0, y1 + 1):
            put(px, cx - 1, y, hk if y % 2 else hd)
            put(px, cx, y, hd if y % 2 else hm)
        tupfen(px, r, ((1, 1), (6, 1)), hd, x0, y0)
    else:                                                             # Rippen, Bauch
        for j in (1, 3):
            for dx in (1, 2):
                if (cx - dx - 1, y0 + j) in r:
                    put(px, cx - dx - 1, y0 + j, hd)
                if (cx + dx, y0 + j) in r:
                    put(px, cx + dx, y0 + j, hk)
        tupfen(px, r, ((3, 4), (4, 4)), hd, x0, y0)
        tupfen(px, r, ((2, 5), (5, 5)), hk, x0, y0)
    tupfen(px, r, ((1, 2), (1, 3)), hk, x0, y0)                       # Schatten unter der Achsel
    k = ecken(m['kopf'])
    haut_kopf(px, k, haut, seitlich, hinten, haar=None)
    kx0, ky0, kx1, ky1 = kasten(k)
    for dx, dy in ((1, 1), (1, 2), (8, 1), (8, 2)):                   # Schwielen an den Schlaefen
        put(px, kx0 + dx, ky0 + dy, hk)
    if hinten:
        tupfen(px, k, ((4, 3), (5, 4), (3, 5)), hd, kx0, ky0)
    else:
        li, re = augen(px, k, seitlich, haut, art='glut')
        for x in range(kx0 + 1, kx0 + 9):                             # breites Maul, offen
            put(px, x + seitlich, ky0 + 5, rgb(NACHT))
            if (x + seitlich, ky0 + 6) in k:
                put(px, x + seitlich, ky0 + 6, hk)
        for dx in (2, 5, 7):                                          # obere Fangzaehne
            put(px, kx0 + dx + seitlich, ky0 + 5, rgb(KRALLE))
        for dx in (3, 6):                                             # untere Zaehne
            if (kx0 + dx + seitlich, ky0 + 6) in k:
                put(px, kx0 + dx + seitlich, ky0 + 6, rgb(KRALLE))
        put(px, kx0 + 1 + seitlich, ky0 + 5, rgb(NACHT)); put(px, kx0 + 8 + seitlich, ky0 + 5, rgb(NACHT))
    for sgn, ex in ((-1, kx0 - 1), (1, kx1 + 1)):                     # spitze Ohren
        put(px, ex, ky0 + 2, hm if sgn < 0 else hd)
        put(px, ex, ky0 + 1, hh if sgn < 0 else hm)
        put(px, ex + sgn, ky0 + 1, hd if sgn < 0 else hk)
        put(px, ex, ky0 + 3, hd if sgn < 0 else hk)
    # lange Arme neben dem Rumpf, Sehnen, Krallen; im Schritt schwingt einer
    schwung = 1 if frame in (2, 3, 8, 9) else 0
    for sgn, ax in ((-1, x0 - 2), (1, x1 + 2)):
        laenge = (y1 - y0) + 3 + (schwung if sgn > 0 else 0)
        for j in range(laenge):
            put(px, ax, y0 + 1 + j, hm if sgn < 0 else hd)
            put(px, ax + sgn, y0 + 1 + j, hd if sgn < 0 else hk)
            if j % 3 == 2:
                put(px, ax, y0 + 1 + j, hd if sgn < 0 else hk)
        put(px, ax, y0 + 1, hh if sgn < 0 else hm)
        hy = y0 + 1 + laenge
        for kk in range(3):
            put(px, ax + sgn * (kk - 1), hy + (1 if kk == 1 else 0), rgb(KRALLE))
        put(px, ax + sgn, hy + 1, hk)


def cultist(px, m, seitlich, hinten, frame):
    robe = ton('robe')
    rh, rm, rd, rk = robe
    beine_malen(px, m['beine'], robe, ton('stiefel'))
    for x, y in m['beine']:                                           # Robensaum: Falten
        if (x - 1, y) in m['beine'] and (x + 1, y) in m['beine'] and x % 3 == 1:
            put(px, x, y, rd)
    r = schultern(m['rumpf'])
    zylinder(px, r, robe)
    x0, y0, x1, y1 = kasten(r)
    cx = (x0 + x1 + 1) // 2
    for x, y in r:                                                    # haengende Falten
        if y > y0 and (x - 1, y) in r and (x + 1, y) in r:
            d = x - x0
            if d in (2, 5):
                put(px, x, y, rd if y < y1 else rk)
            elif d == 1:
                put(px, x, y, rh if y < y0 + 3 else rm)
    lh, lm, ld, lk = ton('leder')
    for x in range(x0 + 1, x1):                                       # Strick
        if (x, y0 + 4) in r:
            put(px, x, y0 + 4, lm if x % 2 else ld)
    put(px, cx - 1, y0 + 4, lh); put(px, cx, y0 + 5, ld); put(px, cx, y0 + 6, lk)   # Knoten, Ende
    if not hinten:                                                    # Augensymbol
        for dx in range(-2, 2):
            put(px, cx + dx, y0 + 1, rk)
            put(px, cx + dx, y0 + 3, rk)
        put(px, cx - 2, y0 + 2, rk); put(px, cx + 1, y0 + 2, rk)
        put(px, cx - 1, y0 + 2, rgb(GLUT)); put(px, cx, y0 + 2, rgb(GLUT_DK))
    k = kapuze(m['kopf'])
    ellipsoid(px, k, robe, grenzen=(0.55, 0.2, -0.2))
    kx0, ky0, kx1, ky1 = kasten(k)
    if not hinten:
        for x, y in k:                                                # Gesicht im Schatten
            if kx0 + 2 <= x <= kx1 - 2 and ky0 + 3 <= y <= ky1 - 1:
                tief = (x > kx0 + 3) or (y > ky0 + 4)
                put(px, x, y, rgb(NACHT) if tief else rgb('2d1b1e'))
        for x in range(kx0 + 2, kx1 - 1):                             # Kapuzenrand oben: Licht
            put(px, x, ky0 + 2, rh if x < kx0 + 5 else rm)
        for y in range(ky0 + 3, ky1):
            put(px, kx0 + 1, y, rm)
            put(px, kx1 - 1, y, rk)
        li, re = augen(px, k, seitlich, robe, art='glut')             # Augen wie bei allen
    else:
        tupfen(px, k, ((2, 3), (2, 4), (2, 5), (7, 3), (7, 4), (7, 5)), rd, kx0, ky0)
        tupfen(px, k, ((1, 3), (1, 4)), rh, kx0, ky0)
    tupfen(px, k, ((4, 0), (5, 1), (4, 2)), rk, kx0, ky0)             # Falte zur Spitze
    tupfen(px, k, ((3, 1), (3, 2)), rh, kx0, ky0)
    put(px, kx0 + 4, ky0 - 1, rm); put(px, kx0 + 5, ky0 - 1, rd)      # Spitze
    put(px, kx0 + 5, ky0 - 2, rd); put(px, kx0 + 6, ky0 - 3, rk)


def mummy(px, m, seitlich, hinten, frame):
    binde = ton('binde')
    bh, bm, bd, bk = binde
    fleck = rgb('886e6a')
    beine_malen(px, m['beine'], binde, ton('bindestiefel'))
    r = schultern(m['rumpf'])
    k = ecken(m['kopf'])
    zylinder(px, r, binde)
    ellipsoid(px, k, binde, grenzen=(0.5, 0.15, -0.25))
    alles = k | r | m['beine']
    for x, y in alles:                                                # Wickellagen: jede
        if (x + 1, y) not in alles or (x - 1, y) not in alles:        # zweite Zeile eine Lage,
            continue                                                  # oben hell, unten dunkel
        if y % 3 == 0:
            put(px, x, y, bh)
        elif y % 3 == 2:
            put(px, x, y, bd)
    for x, y in alles:                                                # zwei schraege Naehte
        if (x + 1, y) in alles and (x - 1, y) in alles and (x + y) % 7 == 0:
            put(px, x, y, bk)
    x0, y0, x1, y1 = kasten(r)
    for dx in (2, 3, 4):                                              # alte Verfaerbung, eine Lage
        put(px, x0 + dx, y0 + 4, fleck)
    kx0, ky0, kx1, ky1 = kasten(k)
    put(px, kx0 + 7, ky0 + 1, fleck)
    put(px, kx0 + 8, ky0 + 1, fleck)
    if not hinten:                                                    # Schlitz zwischen den Lagen
        for x in range(kx0 + 1 + max(0, seitlich), kx1):
            put(px, x, ky0 + 2, bd)                                   # Lage haengt ueber
            put(px, x, ky0 + 5, bm)
        augen(px, k, seitlich, binde, art='hohl')                     # Augen wie bei allen
        put(px, kx0 + 4 + seitlich, ky0 + 3, rgb('2d1b1e'))           # Schatten im Schlitz
        put(px, kx0 + 5 + seitlich, ky0 + 3, rgb('2d1b1e'))
        put(px, kx0 + 4 + seitlich, ky0 + 4, bd)
        put(px, kx0 + 5 + seitlich, ky0 + 4, bd)
    for j in range(3):                                                # lose Enden
        put(px, kx0 - 1, ky0 + 4 + j, bd if j < 2 else bk)
    put(px, kx0 - 2, ky0 + 6, bk)
    put(px, x1 + 1, y0 + 3, bd); put(px, x1 + 1, y0 + 4, bk); put(px, x1 + 2, y0 + 5, bk)


def bandit(px, m, seitlich, hinten, frame):
    lumpen = ton('lumpen')
    lh, lm, ld, lk = ton('leder')
    beine_malen(px, m['beine'], ton('hosen'), ton('leder'))
    r = schultern(m['rumpf'])
    zylinder(px, r, lumpen)
    x0, y0, x1, y1 = kasten(r)
    cx = (x0 + x1 + 1) // 2
    tupfen(px, r, ((0, 2), (7, 2), (1, 3)), lumpen[2], x0, y0)        # Aermelfalten
    tupfen(px, r, ((1, 1),), lumpen[0], x0, y0)
    for y in range(y0, y0 + 4):                                       # Lederweste, Naht, Stiche
        for dx in (-3, -2, -1, 0, 1, 2):
            if (cx + dx, y) in r:
                if hinten:
                    col = lk if dx == 0 else (lm if dx < 0 else ld)
                else:
                    col = lk if dx == -1 else (lm if dx < -1 else ld)
                    if dx in (-3, 2) and y % 2:
                        col = lk
                put(px, cx + dx, y, col)
    put(px, cx - 3, y0, lh); put(px, cx - 2, y0, lh); put(px, cx + 2, y0, lk)   # Schulterlicht
    for x in range(x0 + 1, x1):                                       # Guertel
        if (x, y0 + 4) in r:
            put(px, x, y0 + 4, lk if x > cx else ld)
    put(px, cx - 1, y0 + 4, rgb('f8c53a')); put(px, cx, y0 + 4, rgb('e88a36'))
    if not hinten:                                                    # Dolch
        put(px, x1, y1, rgb('c5c7dd')); put(px, x1, y1 + 1, rgb('9a97b9')); put(px, x1, y1 - 1, lk)
    k = ecken(m['kopf'])
    haut_kopf(px, k, ton('haut'), seitlich, hinten, haar=ton('haar'))
    kx0, ky0, kx1, ky1 = kasten(k)
    th, tm, td, tk = ton('tuch')
    if not hinten:
        li, re = augen(px, k, seitlich, ton('haut'), art='klar',
                       verdeckt='li' if seitlich == 0 else None)
        for x in range(kx0 + 1, kx1):                                 # Halstuch ueber Nase und Mund
            for dy, col in ((5, th if x < kx0 + 4 else tm), (6, tm if x < kx0 + 6 else td)):
                if (x, ky0 + dy) in k:
                    put(px, x, ky0 + dy, col)
        put(px, kx1 - 1, ky0 + 5, td); put(px, kx0 + 3, ky0 + 6, tk)  # Schatten, Falte
        if seitlich == 0:                                             # Augenklappe ueber dem linken Auge
            for dx, dy in ((2, 3), (3, 3), (2, 4), (3, 4)):
                put(px, kx0 + dx, ky0 + dy, rgb(NACHT))
            put(px, kx0 + 3, ky0 + 3, rgb('2d1b1e'))
            for dx, dy in ((1, 2), (4, 2), (0, 1)):                   # Band ueber die Schlaefe
                put(px, kx0 + dx, ky0 + dy, rgb('2a1e23'))
        put(px, kx0 + 8, ky0 + 5, rgb('e27285'))                      # Schnitt ueber der Wange
        put(px, kx0 + 8, ky0 + 6, rgb('b25266'))
    for x, y in k:                                                    # Kopftuch: obere zwei Zeilen
        if y <= ky0 + 1:
            u = (x - kx0) / (kx1 - kx0)
            put(px, x, y, th if (u < 0.4 and y == ky0) else (tm if u < 0.7 else td))
        if y == ky0 + 2:
            put(px, x, y, tk if x > kx0 + 6 else td)
    for dx, dy in ((3, 1), (4, 1), (6, 0), (7, 0)):                   # Falten im Tuch
        put(px, kx0 + dx, ky0 + dy, td)
    put(px, kx1 + 1, ky0 + 1, td); put(px, kx1 + 1, ky0 + 2, tm)      # Knoten, Zipfel
    put(px, kx1 + 2, ky0 + 2, tk); put(px, kx1 + 2, ky0 + 3, tk)


def breiter(punkte, um=1):
    """Maske seitlich verbreitern - fuer schwere Gegner."""
    aus = set(punkte)
    x0, y0, x1, y1 = kasten(punkte)
    for x, y in punkte:
        if x == x0:
            for d in range(1, um + 1):
                aus.add((x - d, y))
        if x == x1:
            for d in range(1, um + 1):
                aus.add((x + d, y))
    return aus


def wight(px, m, seitlich, hinten, frame):
    """Gepanzerter Untoter: Topfhelm mit Sehschlitz und Glut dahinter,
    Brustpanzer mit Nieten und Guertel, Umhang, Knochenbeine."""
    stahl = ton('ruestung')
    sh, sm, sd, sk = stahl
    uh, um_, ud, uk = ton('umhang')
    beine_malen(px, m['beine'], ton('beinhose'), ton('beinstiefel'))
    r = schultern(m['rumpf'])
    x0, y0, x1, y1 = kasten(r)
    cx = (x0 + x1 + 1) // 2
    for y in range(y0 + 1, y1 + 1):                               # Umhang schaut seitlich vor
        put(px, x0 - 1, y, uh if hinten else um_)
        put(px, x1 + 1, y, ud)
    put(px, x0 - 1, y1 + 1, ud)
    put(px, x1 + 1, y1 + 1, uk)
    if hinten:
        zylinder(px, r, ton('umhang'))
        for y in range(y0, y1 + 1):                               # Umhangfalten
            put(px, cx - 1, y, ud if y % 2 else uk)
            put(px, cx + 1, y, um_ if y % 2 else uh)
    else:
        zylinder(px, r, stahl)
        for y in range(y0, y1 + 1):                               # Mittelgrat
            put(px, cx - 1, y, sh if y < y0 + 3 else sm)
            put(px, cx, y, sd)
        for dx, dy in ((0, 0), (7, 0), (1, 3), (6, 3)):           # Nieten
            tupfen(px, r, ((dx, dy),), sh, x0, y0)
        for x in range(x0 + 1, x1):                               # Guertel
            if (x, y0 + 4) in r:
                put(px, x, y0 + 4, sk if x > cx else sd)
        tupfen(px, r, ((3, 4), (4, 4)), rgb('b47538'), x0, y0)    # Schnalle
    k = ecken(m['kopf'])
    kx0, ky0, kx1, ky1 = kasten(k)
    ellipsoid(px, k, stahl, grenzen=(0.5, 0.15, -0.2))            # Topfhelm
    for x, y in k:                                                # unten kantiger als eine Kugel
        if y >= ky0 + 5:
            put(px, x, y, sd if x > kx0 + 5 else sm)
    for x in range(kx0, kx1 + 1):                                 # Helmrand
        if (x, ky0 + 2) in k:
            put(px, x, ky0 + 2, sk if x > kx0 + 5 else sd)
    if not hinten:
        for x in range(kx0 + 1, kx1):                             # Sehschlitz
            for dy in (3, 4):
                if (x, ky0 + dy) in k:
                    put(px, x, ky0 + dy, rgb(SCHWARZ) if dy == 3 else rgb(NACHT))
        augen(px, k, seitlich, stahl, art='glut')                 # Glut dahinter
        for x in range(kx0 + 3, kx0 + 8):                         # Luftschlitze
            if x % 2 and (x + seitlich, ky0 + 5) in k:
                put(px, x + seitlich, ky0 + 5, sk)
    put(px, kx0 + 4, ky0 - 1, sm)
    put(px, kx0 + 5, ky0 - 1, sd)
    put(px, kx0 + 5, ky0 - 2, uh)
    put(px, kx0 + 4, ky0 - 2, um_)
    tupfen(px, k, ((2, 1), (3, 1)), sh, kx0, ky0)                 # Glanz auf dem Helm
    tupfen(px, k, ((8, 4), (8, 5)), sk, kx0, ky0)


def hag(px, m, seitlich, hinten, frame):
    """Hexe: breitkrempiger Spitzhut, fahle Haut, Hakennase, Robe mit
    Guertel und Kraeuterbeutel."""
    haut = ton('hexhaut')
    robe = ton('hexrobe')
    rh, rm, rd, rk = robe
    beine_malen(px, m['beine'], robe, ton('stiefel'))
    for x, y in m['beine']:                                       # Robensaum
        if (x - 1, y) in m['beine'] and (x + 1, y) in m['beine'] and x % 3 == 0:
            put(px, x, y, rd)
    r = schultern(m['rumpf'])
    zylinder(px, r, robe)
    x0, y0, x1, y1 = kasten(r)
    cx = (x0 + x1 + 1) // 2
    for x, y in r:                                                # Faltenrinnen
        if y > y0 and (x - 1, y) in r and (x + 1, y) in r and (x - x0) in (2, 5):
            put(px, x, y, rd if y < y1 else rk)
    for x in range(x0 + 1, x1):                                   # Guertelband
        if (x, y0 + 4) in r:
            put(px, x, y0 + 4, rk if x > cx else rd)
    tupfen(px, r, ((5, 5), (6, 5), (5, 6)), ton('leder')[2], x0, y0)   # Beutel
    tupfen(px, r, ((6, 6),), ton('leder')[3], x0, y0)
    k = ecken(m['kopf'])
    haut_kopf(px, k, haut, seitlich, hinten, haar=ton('haar'))
    kx0, ky0, kx1, ky1 = kasten(k)
    if not hinten:
        li, re = augen(px, k, seitlich, haut, art='klar', iris=rgb('f8c53a'))
        for j in range(3):                                        # Hakennase
            put(px, kx0 + 4 + seitlich + (1 if j == 2 else 0), ky0 + 3 + j, haut[2])
        for x in range(kx0 + 3, kx0 + 7):                         # eingefallener Mund
            put(px, x + seitlich, ky0 + 5, rgb(NACHT))
        put(px, kx0 + 3 + seitlich, ky0 + 6, haut[3])             # Kinnschatten
        put(px, kx0 + 4 + seitlich, ky0 + 6, haut[3])
        put(px, kx0 + 5 + seitlich, ky0 + 5, ton('bein')[1])      # ein Zahn
        put(px, kx0 + 8, ky0 + 4, haut[3])                        # eingefallene Wange
        put(px, kx0 + 8, ky0 + 5, haut[3])
    hh, hm, hd, hk = ton('haar')
    for x in range(kx0 - 1, kx1 + 2):                             # Haar unter der Krempe
        put(px, x, ky0 + 1, hm if x < kx0 + 4 else hd)
    for x in (kx0, kx0 + 3, kx1 - 1):                             # Straehnen haengen tiefer
        put(px, x, ky0 + 2, hd)
    for x, y in ((kx0 - 1, ky0 + 3), (kx0 - 1, ky0 + 4), (kx1 + 1, ky0 + 3), (kx1 + 1, ky0 + 4)):
        put(px, x, y, hd)
    for x in range(kx0 - 2, kx1 + 3):                             # Hutkrempe
        put(px, x, ky0, rk if x > kx0 + 5 else rd)
        put(px, x, ky0 - 1, rm if x < kx0 + 5 else rd)
    for j, w in enumerate((3, 2, 2, 1)):                          # Spitzhut, geknickt
        y = ky0 - 2 - j
        vers = j // 2
        for x in range(kx0 + 3 - w + vers, kx0 + 5 + w + vers):
            put(px, x, y, rh if x < kx0 + 4 + vers else (rm if x < kx0 + 6 + vers else rd))
    put(px, kx0 + 8, ky0 - 6, rk)


def brute(px, m, seitlich, hinten, frame):
    """Schlaeger: breiter Oberkoerper, kleiner Kopf in einer Eisenmaske,
    nackte Brust mit Narben, schwere Hose."""
    haut = ton('huene')
    hh, hm, hd, hk = haut
    beine_malen(px, m['beine'], ton('huenehose'), ton('stiefel'))
    r = breiter(schultern(m['rumpf']), 1)
    zylinder(px, r, haut)
    x0, y0, x1, y1 = kasten(r)
    cx = (x0 + x1 + 1) // 2
    if hinten:
        for y in range(y0, y1 + 1):                               # Rueckenrinne
            put(px, cx - 1, y, hd)
            put(px, cx, y, hm)
        tupfen(px, r, ((1, 1), (8, 1)), hd, x0, y0)               # Schulterblaetter
    else:
        for dx in (-4, -3, 2, 3):                                 # Brustmuskeln
            for y in range(y0 + 1, y0 + 3):
                if (cx + dx, y) in r:
                    put(px, cx + dx, y, hh if dx < 0 else hm)
        for y in range(y0 + 1, y0 + 4):                           # Brustfurche
            put(px, cx - 1, y, hk)
            put(px, cx, y, hd)
        for dx in range(-4, 4):                                   # Rippenbogen unter der Brust
            if (cx + dx, y0 + 3) in r:
                put(px, cx + dx, y0 + 3, hd)
        for dx, dy in ((2, 5), (3, 5), (5, 5), (6, 5), (2, 6), (6, 6)):   # Bauchmuskeln
            tupfen(px, r, ((dx, dy),), hd, x0, y0)
        for dx, dy in ((3, 6), (5, 6)):
            tupfen(px, r, ((dx, dy),), hh, x0, y0)
        for dx, dy in ((1, 2), (2, 2), (2, 3), (3, 3)):           # Narbe quer ueber die Brust
            tupfen(px, r, ((dx, dy),), ton('narbe')[2], x0, y0)
        for dx, dy in ((1, 3), (2, 4)):                           # Wulst darunter
            tupfen(px, r, ((dx, dy),), ton('narbe')[3], x0, y0)
    for y in range(y0 + 1, y1 + 1):                               # Schulterkanten
        put(px, x0, y, hm if hinten else hd)
        put(px, x1, y, hk)
    for x in range(x0 + 1, x1):                                   # breiter Guertel
        if (x, y1) in r:
            put(px, x, y1, ton('leder')[2] if x < cx else ton('leder')[3])
    tupfen(px, r, ((4, y1 - y0), (5, y1 - y0)), rgb('b47538'), x0, y0)
    k = ecken(m['kopf'], oben=2, unten=1)                         # kleiner, eckiger Kopf
    kx0, ky0, kx1, ky1 = kasten(k)
    haut_kopf(px, k, haut, seitlich, hinten, haar=ton('haar'), glanz=False)
    if not hinten:
        eisen = ton('ruestung')
        li, re = augen(px, k, seitlich, haut, art='klar', iris=rgb('b25266'))
        for dx in (0, 1):                                         # schwere Brauen
            put(px, li + dx, ky0 + 2, hk)
            put(px, re + dx, ky0 + 2, hk)
        for x, y in k:                                            # Maulkorb, untere Gesichtshaelfte
            if ky0 + 5 <= y <= ky0 + 6 and kx0 + 1 <= x <= kx1 - 1:
                put(px, x, y, eisen[1] if x < kx0 + 5 else eisen[2])
        for x in range(kx0 + 2, kx1 - 1):                         # Spalt im Maulkorb
            if (x, ky0 + 5) in k:
                put(px, x, ky0 + 5, eisen[3])
        for dx in (2, 5):                                         # zwei Nieten am Rand
            if (kx0 + dx, ky0 + 5) in k:
                put(px, kx0 + dx, ky0 + 5, eisen[0])
    else:
        tupfen(px, k, ((3, 3), (5, 4)), ton('haar')[3], kx0, ky0)
    put(px, kx0 - 1, ky0 + 3, ton('leder')[2])                    # Riemen der Maske
    put(px, kx1 + 1, ky0 + 3, ton('leder')[3])



GEGNER = {'zombie': zombie, 'skeleton_warrior': skeleton, 'ghoul': ghoul,
          'cultist': cultist, 'mummy': mummy, 'bandit': bandit,
          'wight': wight, 'hag': hag, 'brute': brute}


# --- Frames ------------------------------------------------------------------------

def verschieben(m, dx, dy):
    return {k: {(x + dx, y + dy) for x, y in v if y + dy <= 29} for k, v in m.items()}


# (Vorlagenframe, dx, dy): Angriff ducken/springen/vorschnellen, Treffer
# zurueck, Tod sinkt in den Boden
EXTRA = {
    'attack': ((5, 0, 1), (2, 1, -2), (2, 3, -1), (1, 2, 0), (1, 1, 0), (1, 0, 0)),
    'hurt': ((1, -2, 0), (1, -3, 1), (1, -1, 0), (1, 0, 0)),
    'death': ((5, 0, 2), (5, 0, 4), (5, 0, 7), (5, 0, 10), (5, 0, 14), (5, 0, 18)),
}


def frame(bauen, richtung, nr, anim='walk'):
    AUGENPIXEL.clear()
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    px = img.load()
    if anim == 'walk':
        m = maske(richtung, nr)
    else:
        vnr, dx, dy = EXTRA[anim][nr - 1]
        if richtung in ('Front', 'Back'):
            dx = 0
        m = verschieben(maske(richtung, vnr), dx, dy)
    hinten = richtung in ('Back', 'BSide')
    seitlich = -1 if richtung in ('FSide', 'BSide') else 0   # Seitenansicht: Blick nach links
    if m['kopf'] and m['rumpf']:
        bauen(px, m, seitlich, hinten, nr if anim == 'walk' else 1)
    if anim == 'death':                                     # unter dem Boden nichts mehr
        for y in range(30, 32):
            for x in range(32):
                px[x, y] = (0, 0, 0, 0)
    return duel_anpassen(aufraeumen(img))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--sheet', action='store_true')
    args = ap.parse_args()
    wurzel = Path(args.out)
    for name, bauen in GEGNER.items():
        ziel = wurzel / name
        ziel.mkdir(parents=True, exist_ok=True)
        for alt in ziel.glob('*.png'):
            alt.unlink()
        zeilen = []
        gesamt = 0
        for richtung in ('Front', 'FSide', 'BSide', 'Back'):
            reihe = []
            for nr in range(1, 11):
                img = frame(bauen, richtung, nr)
                img.save(ziel / ('%s%d.png' % (richtung, nr)))
                reihe.append(img)
            zeilen.append(reihe)
            gesamt += 10
            for anim, posen in EXTRA.items():
                reihe = []
                for nr in range(1, len(posen) + 1):
                    img = frame(bauen, richtung, nr, anim)
                    img.save(ziel / ('%s_%s%d.png' % (richtung, anim, nr)))
                    reihe.append(img)
                zeilen.append(reihe)
                gesamt += len(reihe)
        if args.sheet:
            sc = 3
            blatt = Image.new('RGBA', (10 * 34 * sc, len(zeilen) * 34 * sc), (34, 35, 35, 255))
            for r_, reihe in enumerate(zeilen):
                for i, im in enumerate(reihe):
                    blatt.alpha_composite(im.resize((32 * sc, 32 * sc), Image.NEAREST), (i * 34 * sc + sc, r_ * 34 * sc + sc))
            blatt.save(ziel / '_sheet.png')
        print('  %-18s %d Frames -> %s' % (name, gesamt, ziel))


if __name__ == '__main__':
    main()
