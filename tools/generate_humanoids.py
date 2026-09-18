#!/usr/bin/env python3
"""Menschliche und untote Gegner - Bewegung nach Sprites/Character/template,
Koerper groesser und rund gebaut.

Aus der Vorlage (Strichmaennchen in drei Farben, 32x32, zehn Frames je
Richtung) kommen nur Hub und Beinstellung je Frame:
    Back      Front und Back (gleich): Huepf-Zyklus
    TFSide    vorne + seitlich (Laufrichtung unten rechts/links)
    TBSide    hinten + seitlich (Laufrichtung oben rechts/links)
Die Beine werden mit 4/3 (breit) und 3/2 (hoch) umgesetzt: der Block wird
zur Hose, die duennen Striche werden zwei Pixel breite Beine mit Stiefeln.

Kopf und Rumpf sind eigene Formen (Kopf 12x9 mit runden Ecken, Rumpf 10x7
mit Schultern und Taille, Hueften 8x3) und werden als Koerper beleuchtet:
Kopf als Ellipsoid, Rumpf als Zylinder mit Schulterlicht und dem Schatten
des Kopfes, Licht von oben links vorne. Darauf die Merkmale, jedes mit
eigener Licht- und Schattenseite:

    zombie            graugruene Haut, Haarbueschel, hohle Augen, offener Mund,
                      zerrissenes Hemd mit Naht und Loechern
    skeleton_warrior  Schaedel mit Kiefer und Rostkappe, Brustkorb, Becken
    ghoul             lila-graue Haut, Ohren, Glutaugen, Zahnreihe, Rippen,
                      lange Krallenarme
    cultist           spitze Kapuze, Gesicht im Schatten, Robe mit Falten,
                      Strickguertel, Augensymbol
    mummy             Bandagen in Lagen, Augenschlitz, lose Enden
    bandit            Kopftuch, Augenklappe, Halstuch, Lederweste, Dolch

Ausgabe je Gegner: Front1-10, FSide1-10, BSide1-10, Back1-10, dazu
attack (6), hurt (4), death (6).

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
}
NACHT = '171516'
SCHWARZ = '0e0c0c'
GLUT, GLUT_DK, KRALLE, AUGE = 'fff089', 'e88a36', 'f1f2ff', '36282b'

CX = 15.5                      # Figurenmitte
BODEN = 30                     # unterste Fussreihe


def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def ton(name):
    return tuple(rgb(c) for c in T[name])


def put(px, x, y, col):
    if 0 <= x < 32 and 0 <= y < 40:
        px[x, y] = col


# --- Vorlage lesen ---------------------------------------------------------------

def vorlage(richtung, nr):
    """Hub (0-2) und Beinpixel eines Vorlagenframes."""
    datei = {'Front': 'Back', 'Back': 'Back', 'FSide': 'TFSide', 'BSide': 'TBSide'}[richtung]
    im = Image.open(VORLAGE / ('%s%d.png' % (datei, nr))).convert('RGBA')
    px = im.load()
    kopf_y = 32
    beine = set()
    for y in range(32):
        for x in range(32):
            c = px[x, y]
            if not c[3]:
                continue
            if c[:3] == KOPF_M:
                kopf_y = min(kopf_y, y)
            elif c[:3] == BEIN_M:
                beine.add((x, y))
    return 12 - kopf_y, beine


def ty(y):
    """Vorlagenzeile -> eigene Zeile: Boden bleibt, darueber 3/2."""
    return BODEN - int((29 - y) * 1.5 + 0.5)


def tx(x):
    return CX + (x - CX) * 4 / 3


def beine_umsetzen(beine):
    """Aus den Vorlagenbeinen: Hosenzeilen (y, x0, x1) und je Bein eine
    Punktliste (linke Spalte, y) fuer den Strich, in eigenen Koordinaten."""
    zeilen = {}
    for x, y in beine:
        zeilen.setdefault(y, []).append(x)
    hose = []
    striche = {'l': [], 'r': []}
    ys = sorted(zeilen)
    for i, y in enumerate(ys):
        xs = sorted(zeilen[y])
        if len(xs) >= 5:                                    # Block: Hose
            y0 = ty(y)
            if i + 1 < len(ys) and len(zeilen[ys[i + 1]]) >= 5:
                y1 = ty(ys[i + 1]) - 1
            else:
                y1 = ty(y + 1) - 1 if y < 29 else y0
            for yy in range(y0, max(y0, y1) + 1):
                hose.append((yy, int(math.floor(tx(xs[0]))), int(math.ceil(tx(xs[-1])))))
        else:
            for x in xs:
                seite = 'l' if x < CX else 'r'
                sx = int(math.floor(tx(x) + 0.5)) - (1 if x >= CX else 0)
                striche[seite].append((sx, ty(y)))
    if hose:
        boden = max(z[0] for z in hose)
        for seite, pts in striche.items():
            if pts:
                pts.sort(key=lambda p: p[1])
                pts.insert(0, (pts[0][0], boden + 1))
    return hose, striche


# --- Koerperformen ------------------------------------------------------------------

def maske(x0, y0, breite, einrueck):
    punkte = set()
    for j, e in enumerate(einrueck):
        li, re = (e, e) if isinstance(e, int) else e
        for x in range(x0 + li, x0 + breite - re):
            punkte.add((x, y0 + j))
    return punkte


KOPF_B, KOPF_H = 12, 9
RUMPF_B, RUMPF_H = 10, 7
HUEFT_B, HUEFT_H = 8, 3

KOPF_RUND = (2, 1, 0, 0, 0, 0, 0, 1, 2)
KOPF_SCHAEDEL = (2, 1, 0, 0, 0, 0, 1, 2, 3)
KOPF_KAPUZE = (4, 3, 2, 1, 0, 0, 0, 0, 0)
RUMPF_NORMAL = (1, 0, 0, 0, 0, 0, 1)
RUMPF_BREIT = (1, 0, 0, 0, 0, 0, 0)
RUMPF_ROBE = (1, 0, 0, 0, 0, 0, 0)


def koerper(kopf_form, rumpf_form, hose_oben):
    """Kopf, Rumpf, Hueften uebereinander auf der Hose."""
    hy1 = hose_oben - 1
    hueft = maske(int(CX - HUEFT_B / 2 + 0.5), hy1 - HUEFT_H + 1, HUEFT_B, (0, 0, 0))
    ry0 = hy1 - HUEFT_H + 1 - RUMPF_H
    rumpf = maske(int(CX - RUMPF_B / 2 + 0.5), ry0, RUMPF_B, rumpf_form)
    ky0 = ry0 - KOPF_H + 1                                # Kopf sitzt eine Zeile in den Schultern
    kopf = maske(int(CX - KOPF_B / 2 + 0.5), ky0, KOPF_B, kopf_form)
    return kopf, rumpf, hueft


def kasten(punkte):
    xs = [p[0] for p in punkte]
    ys = [p[1] for p in punkte]
    return min(xs), min(ys), max(xs), max(ys)


# --- Beleuchtung --------------------------------------------------------------------

LICHT = (-0.55, -0.55, 0.62)          # von links oben vorne


def stufe(lit, toene, grenzen=(0.52, 0.18, -0.2)):
    hell, mitte, dunkel, kante = toene
    if lit > grenzen[0]:
        return hell
    if lit > grenzen[1]:
        return mitte
    if lit > grenzen[2]:
        return dunkel
    return kante


def ellipsoid(px, punkte, toene, grenzen=(0.52, 0.18, -0.2), glanz=None):
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
        gx, gy = int(cx - rx * 0.45), int(cy - ry * 0.5)
        for dx, dy in ((0, 0), (1, 0), (0, 1)):
            if (gx + dx, gy + dy) in punkte:
                put(px, gx + dx, gy + dy, glanz)


def zylinder(px, punkte, toene, kopfschatten=True, grenzen=(0.5, 0.15, -0.22)):
    """Rumpf: Zylinder um die Hochachse, Schultern nach oben beleuchtet,
    Kopfschatten ueber die Brust, unterster Rand im Schatten."""
    x0, y0, x1, y1 = kasten(punkte)
    cx = (x0 + x1) / 2
    rx = (x1 - x0 + 1) / 2
    for x, y in punkte:
        nx = (x - cx) / rx
        nz = math.sqrt(max(0.0, 1 - nx * nx))
        ny = -0.5 if (x, y - 1) not in punkte else 0.0
        if (x, y + 1) not in punkte:
            ny = 0.5
        lit = nx * LICHT[0] + ny * LICHT[1] + nz * LICHT[2]
        if kopfschatten and y - y0 < 2 and abs(x - cx) < 3.5:
            lit -= 0.45
        put(px, x, y, stufe(lit, toene, grenzen))


def hose_malen(px, hose, toene):
    """Hosenblock: zwei Roehren nebeneinander, Schritt in der Mitte."""
    hh, hm, hd, hk = toene
    oben = min(z[0] for z in hose)
    for y, x0, x1 in hose:
        w = x1 - x0 + 1
        cx = (x0 + x1) / 2
        for x in range(x0, x1 + 1):
            if x == x1:
                col = hk
            elif x == x0:
                col = hd
            elif w > 10:                                    # ausgestrecktes Bein: eine Roehre
                col = hm if y == oben else hd
            elif abs(x - cx) < 0.6:
                col = hk
            else:
                seite = x < cx
                u = (x - x0) / (cx - x0) if seite else (x1 - x) / (x1 - cx)   # 0 aussen .. 1 innen
                col = hh if (seite and y == oben and u > 0.3) else (hm if (seite or u > 0.6) else hd)
            put(px, x, y, col)


def bein_strich(px, pts, hose, stiefel):
    """Ein Bein als Linie aus zwei Pixel breiten Punkten; die untersten zwei
    Zeilen als Stiefel."""
    hh, hm, hd, hk = hose
    sh, sm, sd, sk = stiefel
    if not pts:
        return
    zellen = set()
    if len(pts) == 1:
        zellen.add(pts[0])
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        n = max(abs(xb - xa), abs(yb - ya), 1)
        for i in range(n + 1):
            zellen.add((round(xa + (xb - xa) * i / n), round(ya + (yb - ya) * i / n)))
    unten = max(p[1] for p in zellen)
    for x, y in zellen:
        fuss = y >= unten - 1
        if fuss:
            put(px, x, y, sm if y == unten - 1 else sd)
            put(px, x + 1, y, sk)
            if y == unten:
                put(px, x + 2, y, sk)                       # Fussspitze
        else:
            put(px, x, y, hm)
            put(px, x + 1, y, hd)


def beine_malen(px, hose, striche, hosen, stiefel):
    if hose:
        hose_malen(px, hose, hosen)
    for pts in striche.values():
        bein_strich(px, pts, hosen, stiefel)


# --- Merkmale ------------------------------------------------------------------------

def tupfen(px, punkte, stellen, col):
    x0, y0, _, _ = kasten(punkte)
    for dx, dy in stellen:
        if (x0 + dx, y0 + dy) in punkte:
            put(px, x0 + dx, y0 + dy, col)


def augen(px, kopf, seitlich, farbe, hoehe=2, breite=2, zeile=4):
    """Zwei Augen im Kopf; seitlich rueckt beide nach rechts, das hintere
    wird schmaler. Gibt die linken Spalten zurueck."""
    x0, y0, x1, y1 = kasten(kopf)
    cx = (x0 + x1 + 1) // 2
    li = cx - 3 + seitlich
    re = cx + 1 + seitlich
    pos = []
    for ex, hinteres in ((li, seitlich > 0), (re, False)):
        b = breite - (1 if hinteres else 0)
        for dx in range(b):
            for dy in range(hoehe):
                if (ex + dx, y0 + zeile + dy) in kopf:
                    put(px, ex + dx, y0 + zeile + dy, farbe)
        pos.append(ex)
    return pos


def mund(px, kopf, seitlich, col, breite=2, zeile=6):
    x0, y0, x1, y1 = kasten(kopf)
    cx = (x0 + x1 + 1) // 2
    for dx in range(breite):
        put(px, cx - breite // 2 + dx + seitlich, y0 + zeile, col)


def haar_hinten(px, kopf, toene):
    """Hinterkopf voll Haar: Kugel in den Haartoenen, Straehnen als helle
    Bogenstuecke, Spitzen am Nacken."""
    hh, hm, hd, hk = toene
    ellipsoid(px, kopf, toene, grenzen=(0.6, 0.25, -0.15))
    tupfen(px, kopf, ((3, 1), (4, 2), (5, 3), (7, 2), (8, 3), (2, 4), (6, 5), (4, 6)), hh)
    tupfen(px, kopf, ((2, 8), (5, 8), (8, 8), (3, 7), (7, 7)), hk)


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
    for dx, dy in ((7, 5), (8, 5), (9, 6), (8, 6), (9, 4)):           # Wangenschatten rechts
        if (x0 + dx + seitlich, y0 + dy) in kopf:
            put(px, x0 + dx + seitlich, y0 + dy, hd)
    for dx, dy in ((3, 3), (4, 3), (7, 3), (8, 3)):                   # Brauen
        if (x0 + dx + seitlich, y0 + dy) in kopf:
            put(px, x0 + dx + seitlich, y0 + dy, hd)
    put(px, x0 + 6 + seitlich, y0 + 5, hd)                            # Nasenschatten
    put(px, x0 + 5 + seitlich, y0 + 5, hh)                            # Nasenlicht


# --- Gegner --------------------------------------------------------------------------

def zombie(px, k, r, h, hose, striche, seitlich, hinten, frame):
    haut = ton('moder')
    lumpen = ton('lumpen')
    lh, lm, ld, lk = lumpen
    beine_malen(px, hose, striche, ton('hosen'), ton('stiefel'))
    zylinder(px, h, lumpen, kopfschatten=False)
    zylinder(px, r, lumpen)
    x0, y0, x1, y1 = kasten(r)
    for dx, dy in ((1, 2), (2, 3), (3, 4), (7, 1), (6, 2), (5, 3)):    # Falten zur Mitte
        if (x0 + dx, y0 + dy) in r:
            put(px, x0 + dx, y0 + dy, ld)
    for dx, dy in ((2, 2), (7, 0), (6, 1)):
        if (x0 + dx, y0 + dy) in r:
            put(px, x0 + dx, y0 + dy, lh)
    tupfen(px, r, ((6, 4), (7, 4), (7, 5)), haut[2])                   # Loch mit Haut
    tupfen(px, r, ((6, 5), (8, 5)), haut[3])
    tupfen(px, r, ((2, 5), (2, 6)), haut[2])
    tupfen(px, r, ((4, 0), (4, 1), (4, 2)), lk)                        # offene Naht
    tupfen(px, r, ((3, 1), (5, 2)), lh)
    hx0, hy0, hx1, hy1 = kasten(h)
    for x in range(hx0, hx1 + 1):                                      # zerfetzter Saum
        if (x, hy1) in h and x % 2 == 0:
            put(px, x, hy1, lk)
    haut_kopf(px, k, haut, seitlich, hinten, haar=ton('haar'))
    kx0, ky0, kx1, ky1 = kasten(k)
    bh, bm, bd, bk = ton('haar')
    if hinten:
        for dx, dy in ((3, 4), (4, 4), (4, 5), (8, 5), (9, 5)):                          # kahle Stellen
            if (kx0 + dx, ky0 + dy) in k:
                put(px, kx0 + dx, ky0 + dy, haut[3])
    else:
        tupfen(px, k, ((2, 5), (1, 4), (10, 3), (9, 2)), haut[2])       # Flecken
        tupfen(px, k, ((2, 6), (10, 4)), rgb('654956'))                # Bluterguss
        li, re = augen(px, k, seitlich, rgb(NACHT), hoehe=2, breite=2, zeile=4)
        put(px, li, ky0 + 6, haut[3]); put(px, li + 1, ky0 + 6, haut[3])          # Traenensaecke
        put(px, re, ky0 + 5, rgb(NACHT)); put(px, re, ky0 + 6, haut[3])          # rechtes Auge haengt
        put(px, re, ky0 + 4, haut[2])
        mund(px, k, seitlich, rgb(NACHT), breite=4, zeile=7)
        put(px, kx0 + 5 + seitlich, ky0 + 7, rgb('ddcebf'))                       # Zahn
        put(px, kx0 + 8 + seitlich, ky0 + 8, haut[3])                             # haengender Winkel
    for dx, dy, t in ((1, 1, 1), (2, 0, 0), (3, 1, 1), (4, -1, 0), (5, 0, 1), (6, -1, 0),
                      (7, 0, 1), (8, -1, 1), (9, 0, 2), (10, 1, 2), (0, 2, 2), (11, 2, 2),
                      (2, 1, 2), (5, 1, 1), (8, 1, 2), (3, 0, 0)):
        put(px, kx0 + dx, ky0 + dy, (bh, bm, bd, bk)[t])


def skeleton(px, k, r, h, hose, striche, seitlich, hinten, frame):
    bein = ton('bein')
    beine_malen(px, hose, striche, ton('beinhose'), ton('beinstiefel'))
    zylinder(px, h, ton('beinhose'), kopfschatten=False)               # Becken
    tupfen(px, h, ((3, 0), (4, 0), (2, 1), (5, 1), (3, 2), (4, 2)), bein[3])
    tupfen(px, h, ((1, 0), (6, 0)), bein[0])
    x0, y0, x1, y1 = kasten(r)
    cx = (x0 + x1 + 1) // 2
    if hinten:
        zylinder(px, r, bein)
        for y in range(y0, y1 + 1):                                    # Wirbelsaeule
            put(px, cx - 1, y, bein[2] if y % 2 else bein[1])
            put(px, cx, y, bein[3] if y % 2 else bein[2])
        for j in (1, 3, 5):                                            # Rippen von hinten
            for dx in (2, 3, 4):
                if (cx - dx, y0 + j) in r:
                    put(px, cx - dx, y0 + j, bein[2])
                if (cx + dx - 1, y0 + j) in r:
                    put(px, cx + dx - 1, y0 + j, bein[3])
    else:
        for x, y in r:                                                 # dunkler Brustraum
            rand_ = (x - 1, y) not in r or (x + 1, y) not in r
            put(px, x, y, bein[3] if rand_ else rgb(NACHT))
        for y in range(y0, y1 + 1):                                    # Brustbein
            put(px, cx - 1, y, bein[1] if y % 2 else bein[0])
            put(px, cx, y, bein[2] if y % 2 else bein[1])
        for j in (1, 3, 5):                                            # Rippenboegen
            for dx in (2, 3, 4):
                yy = y0 + j + (1 if dx == 4 else 0)
                if (cx - dx, yy) in r:
                    put(px, cx - dx, yy, bein[0] if dx < 4 else bein[1])
                if (cx + dx - 1, yy) in r:
                    put(px, cx + dx - 1, yy, bein[1] if dx < 4 else bein[2])
        for dx in (-3, -2, 1, 2):                                      # Schluesselbeine
            put(px, cx + dx, y0, bein[0] if dx < 0 else bein[1])
    ellipsoid(px, k, bein, grenzen=(0.45, 0.1, -0.25))
    kx0, ky0, kx1, ky1 = kasten(k)
    if not hinten:
        li, re = augen(px, k, seitlich, rgb(SCHWARZ), hoehe=2, breite=3, zeile=3)
        put(px, li + 2, ky0 + 3, rgb(NACHT)); put(px, li + 2, ky0 + 4, rgb(NACHT))
        put(px, re + 2, ky0 + 3, rgb(NACHT)); put(px, re + 2, ky0 + 4, rgb(NACHT))
        put(px, li + 1, ky0 + 4, rgb('b25266')); put(px, re + 1, ky0 + 4, rgb('b25266'))   # Glimmen
        for ex in (li, re):                                            # Wangenknochen
            put(px, ex, ky0 + 5, bein[2]); put(px, ex + 1, ky0 + 5, bein[0]); put(px, ex + 2, ky0 + 5, bein[2])
        put(px, kx0 + 5 + seitlich, ky0 + 5, bein[3]); put(px, kx0 + 6 + seitlich, ky0 + 6, bein[3])   # Nasenloch
        for x in range(kx0 + 3, kx0 + 9):                              # Zahnreihe
            put(px, x + seitlich, ky0 + 7, bein[3] if x % 2 else bein[0])
            if (x + seitlich, ky0 + 8) in k:
                put(px, x + seitlich, ky0 + 8, bein[2] if x % 2 else bein[1])
        put(px, kx0 + 2 + seitlich, ky0 + 7, bein[2]); put(px, kx0 + 9 + seitlich, ky0 + 7, bein[3])
    else:
        tupfen(px, k, ((4, 3), (5, 4), (6, 5), (7, 4), (8, 5), (3, 6), (6, 7)), bein[3])    # Naehte
        tupfen(px, k, ((4, 4), (7, 5), (5, 6)), bein[0])
    tupfen(px, k, ((1, 3), (2, 4), (2, 5)), bein[3])                   # Riss links
    tupfen(px, k, ((3, 2), (4, 2)), bein[0])                           # Stirnwoelbung
    rost = ton('rost')
    for x, y in k:                                                     # Kappe: oberste zwei Zeilen, Rand
        if y <= ky0 + 1:
            u = (x - kx0) / (kx1 - kx0)
            put(px, x, y, rost[0] if (u < 0.45 and y == ky0) else (rost[1] if u < 0.65 else rost[2]))
        if y == ky0 + 2:
            put(px, x, y, rost[3] if x > kx0 + 4 else rost[2])
    tupfen(px, k, ((4, 1), (9, 1), (10, 0), (7, 2)), rgb('b47538'))    # Rost
    tupfen(px, k, ((6, 0), (3, 1)), rgb('e6e7f0'))                     # Nieten
    put(px, kx0 + 2, ky0, rost[3]); put(px, kx0 + 9, ky0, rost[3])


def ghoul(px, k, r, h, hose, striche, seitlich, hinten, frame):
    haut = ton('ghul')
    hh, hm, hd, hk = haut
    beine_malen(px, hose, striche, ton('ghulhose'), ton('stiefel'))
    zylinder(px, h, ton('ghulhose'), kopfschatten=False)
    zylinder(px, r, haut)
    x0, y0, x1, y1 = kasten(r)
    cx = (x0 + x1 + 1) // 2
    if hinten:                                                         # Wirbelhoecker, Schulterblaetter
        for y in range(y0, y1 + 1):
            put(px, cx - 1, y, hk if y % 2 else hd)
            put(px, cx, y, hd if y % 2 else hm)
        tupfen(px, r, ((2, 1), (3, 2), (7, 1), (6, 2)), hd)
    else:                                                              # Rippen, eingefallener Bauch
        for j in (2, 4):
            for dx in (1, 2, 3):
                if (cx - dx - 1, y0 + j) in r:
                    put(px, cx - dx - 1, y0 + j, hd)
                if (cx + dx, y0 + j) in r:
                    put(px, cx + dx, y0 + j, hk)
        tupfen(px, r, ((4, 5), (5, 5), (4, 6), (5, 6)), hd)
        tupfen(px, r, ((3, 6), (6, 6)), hk)
    tupfen(px, r, ((1, 3), (8, 2), (2, 5)), hk)                        # Flecken
    haut_kopf(px, k, haut, seitlich, hinten, haar=None, glanz=True)
    kx0, ky0, kx1, ky1 = kasten(k)
    tupfen(px, k, ((1, 2), (10, 2), (2, 7), (9, 7), (5, 0), (4, 8)), hk)   # fleckige Haut
    if hinten:
        tupfen(px, k, ((5, 4), (6, 5), (4, 6)), hd)
    else:
        li, re = augen(px, k, seitlich, rgb(NACHT), hoehe=2, breite=3, zeile=3)
        put(px, li + 1, ky0 + 3, rgb(GLUT)); put(px, re + 1, ky0 + 3, rgb(GLUT))
        put(px, li + 1, ky0 + 4, rgb(GLUT_DK)); put(px, re + 1, ky0 + 4, rgb(GLUT_DK))
        put(px, li, ky0 + 5, hk); put(px, re + 2, ky0 + 5, hk)         # Augenhoehlen unten
        for x in range(kx0 + 2, kx0 + 10):                             # breites Maul
            put(px, x + seitlich, ky0 + 7, rgb(KRALLE) if x % 2 else rgb(NACHT))
            if (x + seitlich, ky0 + 8) in k:
                put(px, x + seitlich, ky0 + 8, rgb(NACHT) if x % 2 else hk)
        put(px, kx0 + 1 + seitlich, ky0 + 7, rgb(NACHT)); put(px, kx0 + 10 + seitlich, ky0 + 7, rgb(NACHT))
    for sgn, ex in ((-1, kx0 - 1), (1, kx1 + 1)):                      # spitze Ohren
        put(px, ex, ky0 + 3, hm if sgn < 0 else hd)
        put(px, ex, ky0 + 2, hh if sgn < 0 else hm)
        put(px, ex + sgn, ky0 + 1, hm if sgn < 0 else hd)
        put(px, ex + sgn, ky0 + 2, hd if sgn < 0 else hk)
        put(px, ex, ky0 + 4, hd if sgn < 0 else hk)
    # lange Arme neben dem Rumpf, Sehnen, Krallen; im Schritt schwingt einer
    schwung = 1 if frame in (2, 3, 8, 9) else 0
    for sgn, ax in ((-1, x0 - 2), (1, x1 + 1)):
        laenge = (y1 - y0) + 4 + (schwung if sgn > 0 else 0)
        for j in range(laenge):
            put(px, ax, y0 + 1 + j, hm if sgn < 0 else hd)
            put(px, ax + sgn, y0 + 1 + j, hd if sgn < 0 else hk)
            if j % 3 == 2:
                put(px, ax, y0 + 1 + j, hd if sgn < 0 else hk)
        put(px, ax, y0 + 1, hh if sgn < 0 else hm)
        put(px, ax - sgn, y0 + 1, hm if sgn < 0 else hd)               # Schulter
        hy = y0 + 1 + laenge
        for kk in range(3):
            put(px, ax + sgn * (kk - 1), hy + (1 if kk == 1 else 0), rgb(KRALLE))
        put(px, ax + sgn, hy + 1, hk)


def cultist(px, k, r, h, hose, striche, seitlich, hinten, frame):
    robe = ton('robe')
    rh, rm, rd, rk = robe
    beine_malen(px, hose, striche, robe, ton('stiefel'))
    if hose:                                                           # Robensaum: Falten
        for y, x0, x1 in hose:
            for x in range(x0 + 1, x1):
                if (x - x0) % 3 == 1:
                    put(px, x, y, rd)
    zylinder(px, h, robe, kopfschatten=False)
    zylinder(px, r, robe)
    x0, y0, x1, y1 = kasten(r)
    cx = (x0 + x1 + 1) // 2
    rh_ = r | h
    for x, y in rh_:                                                   # haengende Falten
        if y > y0 + 1 and (x - 1, y) in rh_ and (x + 1, y) in rh_:
            d = x - x0
            if d in (2, 7):
                put(px, x, y, rd if y < y1 else rk)
            elif d in (1, 6):
                put(px, x, y, rh if (y < y0 + 4 and d == 1) else rm)
    lh, lm, ld, lk = ton('leder')
    hx0, hy0, hx1, hy1 = kasten(h)
    for x in range(hx0, hx1 + 1):                                      # Strick
        put(px, x, hy0, lm if x % 2 else ld)
    put(px, cx - 1, hy0, lh); put(px, cx, hy0, ld)
    put(px, cx, hy0 + 1, ld); put(px, cx, hy0 + 2, lk); put(px, cx + 1, hy0 + 2, lk)   # Knoten, Ende
    if not hinten:                                                     # Augensymbol
        for dx in range(-2, 3):
            put(px, cx + dx, y0 + 2, rk)
            put(px, cx + dx, y0 + 4, rk)
        put(px, cx - 2, y0 + 3, rk); put(px, cx + 2, y0 + 3, rk)
        put(px, cx - 1, y0 + 3, rgb(GLUT_DK)); put(px, cx, y0 + 3, rgb(GLUT)); put(px, cx + 1, y0 + 3, rgb(GLUT_DK))
    ellipsoid(px, k, robe, grenzen=(0.55, 0.2, -0.2))                  # Kapuze
    kx0, ky0, kx1, ky1 = kasten(k)
    if not hinten:
        for x, y in k:
            if kx0 + 2 <= x <= kx1 - 2 and ky0 + 4 <= y <= ky1 - 1:
                tief = (x > kx0 + 3) or (y > ky0 + 5)
                put(px, x, y, rgb(NACHT) if tief else rgb('2d1b1e'))
        for x in range(kx0 + 1, kx1):                                  # Kapuzenrand: oben Licht
            if (x, ky0 + 3) in k:
                put(px, x, ky0 + 3, rh if x < kx0 + 6 else rm)
        for y in range(ky0 + 4, ky1):
            put(px, kx0 + 1, y, rm)
            put(px, kx1 - 1, y, rk)
        li, re = augen(px, k, seitlich, rgb(GLUT), hoehe=1, breite=2, zeile=5)
        put(px, li, ky0 + 6, rgb(GLUT_DK)); put(px, re, ky0 + 6, rgb(GLUT_DK))
    else:
        tupfen(px, k, ((3, 4), (3, 5), (3, 6), (3, 7), (8, 4), (8, 5), (8, 6), (8, 7)), rd)
        tupfen(px, k, ((2, 4), (2, 5), (2, 6)), rh)
    tupfen(px, k, ((5, 1), (6, 2), (5, 3), (7, 3)), rk)                # Falte zur Spitze
    tupfen(px, k, ((4, 2), (4, 3)), rh)
    put(px, kx0 + 5, ky0 - 1, rm); put(px, kx0 + 6, ky0 - 1, rd)       # Spitze
    put(px, kx0 + 6, ky0 - 2, rd); put(px, kx0 + 7, ky0 - 3, rk)


def mummy(px, k, r, h, hose, striche, seitlich, hinten, frame):
    binde = ton('binde')
    bh, bm, bd, bk = binde
    fleck = rgb('886e6a')
    beine_malen(px, hose, striche, binde, ton('bindestiefel'))
    zylinder(px, h, binde, kopfschatten=False)
    zylinder(px, r, binde)
    ellipsoid(px, k, binde, grenzen=(0.5, 0.15, -0.25))
    alles = k | r | h | {(x, y) for y, x0, x1 in hose for x in range(x0, x1 + 1)}
    for x, y in alles:                                                 # Wickellagen
        r_ = (y + x // 4) % 3
        if r_ == 0 and (x + 1, y) in alles and (x - 1, y) in alles:
            put(px, x, y, bk if (x + y) % 7 == 0 else bd)
        elif r_ == 1 and (x + y) % 3 == 0 and (x, y) in (k | r):
            put(px, x, y, bh)
    tupfen(px, r, ((2, 2), (7, 1), (3, 5), (8, 5)), fleck)             # Flecken
    tupfen(px, k, ((8, 1), (2, 6), (9, 7)), fleck)
    kx0, ky0, kx1, ky1 = kasten(k)
    cx = (kx0 + kx1 + 1) // 2
    if not hinten:                                                     # Augenschlitz, ein Auge
        for x in range(kx0 + 1 + max(0, seitlich), kx1):
            put(px, x, ky0 + 4, rgb(NACHT))
            put(px, x, ky0 + 3, bd)                                    # Lage haengt ueber
            put(px, x, ky0 + 5, bm)
        put(px, kx0 + 1 + max(0, seitlich), ky0 + 4, rgb('2d1b1e'))
        put(px, cx + 1 + seitlich, ky0 + 4, rgb(AUGE)); put(px, cx + 2 + seitlich, ky0 + 4, rgb(AUGE))
        put(px, cx + 1 + seitlich, ky0 + 5, rgb(AUGE))
        put(px, cx + 2 + seitlich, ky0 + 3, bh)
        put(px, cx - 2 + seitlich, ky0 + 5, rgb('2d1b1e'))
        put(px, cx - 3 + seitlich, ky0 + 5, bd)
    for j in range(4):                                                 # lose Enden
        put(px, kx0 - 1, ky0 + 5 + j, bd if j < 2 else bk)
    put(px, kx0 - 2, ky0 + 8, bk); put(px, kx0 - 2, ky0 + 7, bd)
    x0, y0, x1, y1 = kasten(r)
    put(px, x1 + 1, y0 + 4, bd); put(px, x1 + 1, y0 + 5, bk); put(px, x1 + 2, y0 + 6, bk); put(px, x1 + 2, y0 + 7, bk)


def bandit(px, k, r, h, hose, striche, seitlich, hinten, frame):
    lumpen = ton('lumpen')
    lh, lm, ld, lk = ton('leder')
    beine_malen(px, hose, striche, ton('hosen'), ton('leder'))
    zylinder(px, h, ton('hosen'), kopfschatten=False)
    zylinder(px, r, lumpen)
    x0, y0, x1, y1 = kasten(r)
    cx = (x0 + x1 + 1) // 2
    for dx, dy in ((1, 2), (1, 3), (8, 2), (8, 3), (2, 5)):            # Aermelfalten
        if (x0 + dx, y0 + dy) in r:
            put(px, x0 + dx, y0 + dy, lumpen[2])
    tupfen(px, r, ((1, 1), (2, 4)), lumpen[0])
    for y in range(y0, y1):                                            # Lederweste, Naht, Stiche
        for dx in (-3, -2, -1, 0, 1, 2):
            if (cx + dx, y) in r:
                if hinten:
                    col = lk if dx == 0 else (lm if dx < 0 else ld)
                else:
                    col = lk if dx == -1 else (lm if dx < -1 else ld)
                    if dx in (-3, 2) and y % 2:
                        col = lk
                put(px, cx + dx, y, col)
    put(px, cx - 3, y0, lh); put(px, cx - 2, y0, lh)                   # Schulterlicht
    put(px, cx + 2, y0, lk)
    hx0, hy0, hx1, hy1 = kasten(h)
    for x in range(hx0, hx1 + 1):                                      # Guertel
        put(px, x, hy0, lk if x > cx + 1 else ld)
    put(px, cx - 1, hy0, rgb('f8c53a')); put(px, cx, hy0, rgb('e88a36'))
    if not hinten:                                                     # Dolch
        put(px, x1, y1, rgb('c5c7dd')); put(px, x1, y1 + 1, rgb('9a97b9')); put(px, x1, y1 + 2, rgb('696682'))
        put(px, x1, y1 - 1, lk); put(px, x1 - 1, y1 - 1, lk)
    haut_kopf(px, k, ton('haut'), seitlich, hinten, haar=ton('haar'))
    kx0, ky0, kx1, ky1 = kasten(k)
    th, tm, td, tk = ton('tuch')
    if not hinten:
        li, re = augen(px, k, seitlich, rgb(AUGE), hoehe=2, breite=2, zeile=4)
        put(px, li + 1, ky0 + 4, rgb('f1ebdb')); put(px, re + 1, ky0 + 4, rgb('f1ebdb'))
        for x in range(kx0 + 1, kx1):                                  # Halstuch ueber Nase und Mund
            for dy, col in ((6, th if x < kx0 + 5 else tm), (7, tm if x < kx0 + 7 else td), (8, td)):
                if (x, ky0 + dy) in k:
                    put(px, x, ky0 + dy, col)
        put(px, kx1 - 1, ky0 + 6, td); put(px, kx1 - 1, ky0 + 7, tk)
        put(px, kx0 + 4, ky0 + 7, td); put(px, kx0 + 3, ky0 + 8, tk)    # Falten
        put(px, kx0 + 6, ky0 + 8, tk)
        if seitlich == 0:                                              # Augenklappe links, Band schraeg
            for dx, dy in ((3, 4), (4, 4), (3, 5), (4, 5), (2, 3), (1, 2), (5, 3)):
                put(px, kx0 + dx, ky0 + dy, rgb(NACHT))
            put(px, kx0 + 4, ky0 + 4, rgb('2d1b1e'))
        put(px, kx0 + 9, ky0 + 5, rgb('e27285'))                       # Narbe
    for x, y in k:                                                     # Kopftuch: obere drei Zeilen
        if y <= ky0 + 2:
            u = (x - kx0) / (kx1 - kx0)
            put(px, x, y, th if (u < 0.4 and y < ky0 + 2) else (tm if u < 0.7 else td))
        if y == ky0 + 3:
            put(px, x, y, tk if x > kx0 + 7 else td)
    tupfen(px, k, ((3, 1), (6, 0), (8, 2)), td)                        # Falten im Tuch
    put(px, kx1 + 1, ky0 + 1, td); put(px, kx1 + 1, ky0 + 2, tm)       # Knoten
    put(px, kx1 + 2, ky0 + 2, tk); put(px, kx1 + 2, ky0 + 3, tk); put(px, kx1 + 1, ky0 + 3, td)


GEGNER = {
    'zombie': (zombie, KOPF_RUND, RUMPF_NORMAL),
    'skeleton_warrior': (skeleton, KOPF_SCHAEDEL, RUMPF_NORMAL),
    'ghoul': (ghoul, KOPF_RUND, RUMPF_BREIT),
    'cultist': (cultist, KOPF_KAPUZE, RUMPF_ROBE),
    'mummy': (mummy, KOPF_RUND, RUMPF_NORMAL),
    'bandit': (bandit, KOPF_RUND, RUMPF_NORMAL),
}


# --- Frames ------------------------------------------------------------------------

# (Vorlagenframe, dx, dy): Angriff ducken/springen/vorschnellen, Treffer
# zurueck, Tod sinkt in den Boden
EXTRA = {
    'attack': ((5, 0, 1), (2, 1, -2), (2, 3, -1), (1, 2, 0), (1, 1, 0), (1, 0, 0)),
    'hurt': ((1, -2, 0), (1, -3, 1), (1, -1, 0), (1, 0, 0)),
    'death': ((5, 0, 2), (5, 0, 4), (5, 0, 7), (5, 0, 10), (5, 0, 14), (5, 0, 18)),
}


def frame(name, richtung, nr, anim='walk'):
    bauen, kopf_form, rumpf_form = GEGNER[name]
    if anim == 'walk':
        vnr, dx, dy = nr, 0, 0
    else:
        vnr, dx, dy = EXTRA[anim][nr - 1]
        if richtung in ('Front', 'Back'):
            dx = 0
    hub, beine = vorlage(richtung, vnr)
    hose, striche = beine_umsetzen(beine)
    hose_oben = min(z[0] for z in hose) if hose else BODEN - 5 - int(hub * 1.5)
    k, r, h = koerper(kopf_form, rumpf_form, hose_oben)
    gross = Image.new('RGBA', (32, 40), (0, 0, 0, 0))
    px = gross.load()
    hinten = richtung in ('Back', 'BSide')
    seitlich = 1 if richtung in ('FSide', 'BSide') else 0
    bauen(px, k, r, h, hose, striche, seitlich, hinten, nr if anim == 'walk' else 1)
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    grenze = BODEN if anim == 'death' else 31             # Tod: unter dem Boden nichts mehr
    for y in range(32):
        for x in range(32):
            sx, sy = x - dx, y - dy
            if 0 <= sx < 32 and 0 <= sy < 40 and y <= grenze:
                img.putpixel((x, y), gross.getpixel((sx, sy)))
    return duel_anpassen(img)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--sheet', action='store_true')
    args = ap.parse_args()
    wurzel = Path(args.out)
    for name in GEGNER:
        ziel = wurzel / name
        ziel.mkdir(parents=True, exist_ok=True)
        for alt in ziel.glob('*.png'):
            alt.unlink()
        zeilen = []
        gesamt = 0
        for richtung in ('Front', 'FSide', 'BSide', 'Back'):
            reihe = []
            for nr in range(1, 11):
                img = frame(name, richtung, nr)
                img.save(ziel / ('%s%d.png' % (richtung, nr)))
                reihe.append(img)
            zeilen.append(reihe)
            gesamt += 10
            for anim, posen in EXTRA.items():
                reihe = []
                for nr in range(1, len(posen) + 1):
                    img = frame(name, richtung, nr, anim)
                    img.save(ziel / ('%s_%s%d.png' % (richtung, anim, nr)))
                    reihe.append(img)
                zeilen.append(reihe)
                gesamt += len(reihe)
        if args.sheet:
            sc = 3
            blatt = Image.new('RGBA', (10 * 34 * sc, len(zeilen) * 34 * sc), (23, 21, 22, 255))
            for r_, reihe in enumerate(zeilen):
                for i, im in enumerate(reihe):
                    blatt.alpha_composite(im.resize((32 * sc, 32 * sc), Image.NEAREST), (i * 34 * sc + sc, r_ * 34 * sc + sc))
            blatt.save(ziel / '_sheet.png')
        print('  %-18s %d Frames -> %s' % (name, gesamt, ziel))


if __name__ == '__main__':
    main()
