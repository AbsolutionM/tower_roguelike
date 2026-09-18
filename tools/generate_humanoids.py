#!/usr/bin/env python3
"""Menschliche und untote Gegner nach der Vorlage Sprites/Character/template.

Die Vorlage ist ein Strichmaennchen in drei Farben: Kopf (f8c53a), Rumpf
(d5dc1d), Beine (494182), 32x32, zehn Frames je Richtung:
    Back      Front und Back (gleich): Huepf-Zyklus, Beine als Block plus
              zwei duenne Striche
    TFSide    vorne + seitlich (Laufrichtung unten rechts/links)
    TBSide    hinten + seitlich (Laufrichtung oben rechts/links)
Masse: Kopf 10x7, Rumpf 8x4 + Hueften 6x2, Beinblock 6x2, Fuesse 1 px.

Hier werden die Masken je Frame eingelesen und je Gegner bemalt - so
bewegen sich Beine und Koerper exakt wie in der Vorlage. Kopf und Rumpf
tragen die Merkmale:

    zombie            graugruene Haut, Haarbueschel, hohle Augen, offener Mund,
                      zerrissenes Hemd
    skeleton_warrior  Schaedel mit Rostkappe, Brustkorb mit Rippen, Knochenbeine
    ghoul             lila-graue Haut, Ohren, leuchtende Augen, Zahnreihe,
                      lange Krallenarme neben dem Rumpf
    cultist           Kapuze, Gesicht im Schatten mit gluehenden Augen,
                      Augensymbol auf der Robe
    mummy             Bandagen in Streifen, Augenschlitz, lose Enden
    bandit            Kopftuch, Augenklappe, Halstuch, Lederweste, Dolch

Ausgabe je Gegner: Front1-10, FSide1-10, BSide1-10, Back1-10, dazu
attack (6), hurt (4), death (6) aus den Vorlagenposen abgeleitet.

    python tools/generate_humanoids.py --out C:/Users/maxst/Desktop/Sprites/claude/Enemies --sheet
"""

from __future__ import annotations

import argparse
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


def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def ton(name):
    return tuple(rgb(c) for c in T[name])


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


def rand(punkte):
    return {(x, y) for x, y in punkte
            if any((x + dx, y + dy) not in punkte for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


# --- Malen ------------------------------------------------------------------------

def put(px, x, y, col):
    if 0 <= x < 32 and 0 <= y < 32:
        px[x, y] = col


def flaeche(px, punkte, toene, falten=(), hals=True):
    """Stoff oder Haut mit Licht von oben links: innen ein schraeger Verlauf
    hell -> mitte -> dunkel, die Kanten dunkel (rechts und unten dunkler als
    links), Halsschatten unter dem Kinn. Dazu Falten: schraege Rinnen in
    dunkel mit einem Grat in hell auf der Lichtseite - keine glatten Flaechen.
    falten: (fx, fy, n, richtung) relativ zur linken oberen Ecke, richtung
    +1 = nach rechts unten, -1 = nach links unten."""
    hell, mitte, dunkel, kante = toene
    x0, y0, x1, y1 = kasten(punkte)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    innen = set()
    for x, y in punkte:
        u = (x - x0 + 0.5) / w
        v = (y - y0 + 0.5) / h
        links = (x - 1, y) not in punkte
        rechts = (x + 1, y) not in punkte
        unten = (x, y + 1) not in punkte
        licht = (1 - u) * 0.65 + (1 - v) * 0.35
        if rechts:
            col = kante
        elif unten:
            col = dunkel if u < 0.5 else kante
        elif links:
            col = mitte if v < 0.55 else dunkel
        elif licht > 0.66:
            col = hell
        elif licht < 0.36:
            col = dunkel
        else:
            col = mitte
            innen.add((x, y))
        if not (links or rechts or unten):
            innen.add((x, y))
        put(px, x, y, col)
    if hals:                                                # Halsschatten unter dem Kinn
        cx = (x0 + x1) // 2
        for dx in (-1, 0, 1, 2):
            if (cx + dx, y0) in punkte and (cx + dx + 1, y0) in punkte and (cx + dx - 1, y0) in punkte:
                put(px, cx + dx, y0, dunkel)
    for fx, fy, n, s in falten:
        for i in range(n):
            p = (x0 + fx + i * s, y0 + fy + i)
            if p in innen:
                put(px, p[0], p[1], dunkel)
                q = (p[0] - 1, p[1])
                if q in innen and q != (x0 + fx + (i - 1) * s, y0 + fy + i - 1):
                    put(px, q[0], q[1], hell)


def tupfen(px, punkte, stellen, col, x0=None, y0=None):
    """Einzelne Pixel relativ zur linken oberen Ecke der Maske - Flecken,
    Loecher, Nieten. Nur innerhalb der Maske."""
    if x0 is None:
        x0, y0, _, _ = kasten(punkte)
    for dx, dy in stellen:
        if (x0 + dx, y0 + dy) in punkte:
            put(px, x0 + dx, y0 + dy, col)


def beine_malen(px, punkte, hose, stiefel):
    """Beinblock als Hose: Licht oben links, Schatten rechts, Bundfalte in
    der Mitte, Kniefalte unten. Die duennen Striche als Stiefel mit hellem
    Schaft und dunkler Sohle."""
    if not punkte:                                          # Tod: im Boden versunken
        return
    hh, hm, hd, hk = hose
    sh, sm, sd, sk = stiefel
    x0, y0, x1, y1 = kasten(punkte)
    breit = {y: sum(1 for (x, yy) in punkte if yy == y) for y in range(y0, y1 + 1)}
    block = [y for y in range(y0, y1 + 1) if breit[y] >= 5]
    for x, y in punkte:
        if breit[y] >= 5:                                   # Block: Hose
            bx0 = min(xx for xx, yy in punkte if yy == y)
            bx1 = max(xx for xx, yy in punkte if yy == y)
            cx = (bx0 + bx1) / 2
            if x == bx0 or x == bx1:
                col = hk
            elif y == block[0] and x < cx:
                col = hh
            elif abs(x - cx) < 0.6:
                col = hk if y == block[-1] else hd          # Schritt / Bundfalte
            elif x < cx:
                col = hm if y != block[-1] else hd
            else:
                col = hd if y != block[-1] else hk
            put(px, x, y, col)
        else:                                               # Strich: Stiefel
            oben = (x, y - 1) not in punkte or breit[y - 1] >= 5
            unten = (x, y + 1) not in punkte
            put(px, x, y, sk if unten else (sh if oben else sm))


def gesicht(px, kopf, haut, seitlich, hinten, haar=None):
    """Gesicht in die Kopfmaske: Haut mit Licht oben links, Stirn hell,
    Wangenschatten rechts und unter den Augen, Kinnzeile dunkel. Augen als
    2x2 in Wein, Mund 2 px. seitlich rueckt die Zuege, hinten zeigt Haar
    mit Straehnen."""
    hh, hm, hd, hk = haut
    x0, y0, x1, y1 = kasten(kopf)
    cx = (x0 + x1) // 2
    flaeche(px, kopf, haut, hals=False)
    tupfen(px, kopf, ((2, 1), (3, 1), (4, 1), (3, 2)), hh, x0, y0)           # Stirnlicht
    tupfen(px, kopf, ((7, 4), (8, 4), (7, 5)), hd, x0, y0)                   # Wangenschatten
    if hinten:
        if haar:
            bh, bm, bd, bk = haar
            saum = rand(kopf)
            for x, y in kopf:
                u = (x - x0 + 0.5) / (x1 - x0 + 1)
                put(px, x, y, bk if (x, y) in saum else (bm if u < 0.6 else bd))
            for dx, dy in ((2, 1), (3, 2), (4, 1), (6, 2), (7, 3), (3, 4), (5, 5)):   # Straehnen
                if (x0 + dx, y0 + dy) in kopf:
                    put(px, x0 + dx, y0 + dy, bh)
            for dx in (1, 3, 5, 7, 8):                                         # Haarspitzen am Nacken
                if (x0 + dx, y1) in kopf:
                    put(px, x0 + dx, y1, bd)
        return
    ey = y0 + 3
    for ex in (cx - 2 + seitlich, cx + 2 + seitlich):
        if x0 < ex < x1:
            put(px, ex, ey, rgb(AUGE))
            put(px, ex + (1 if ex > cx else -1), ey, rgb(AUGE))
            put(px, ex, ey + 1, rgb(AUGE))
            put(px, ex, ey - 1, hd)                                             # Braue
            put(px, ex + (1 if ex > cx else -1), ey - 1, hd)
    if seitlich:                                            # hinteres Auge verdeckt
        for dx, dy in ((-2, 0), (-3, 0), (-2, 1), (-2, -1), (-3, -1)):
            put(px, cx + dx + seitlich, ey + dy, hm)
        put(px, cx - 3 + seitlich, ey + 1, hd)
    put(px, cx + seitlich, ey + 1, hd)                                          # Nasenschatten
    for dx in (0, 1):
        put(px, cx + dx + seitlich // 2, y0 + 5, hk)


# --- Gegner: Kopf, Rumpf, Extras ------------------------------------------------------

def zombie(px, m, seitlich, hinten, frame):
    haut = ton('moder')
    beine_malen(px, m['beine'], ton('hosen'), ton('stiefel'))
    flaeche(px, m['rumpf'], ton('lumpen'), falten=((1, 1, 3, 1), (6, 0, 3, -1)))
    x0, y0, x1, y1 = kasten(m['rumpf'])
    lh, lm, ld, lk = ton('lumpen')
    tupfen(px, m['rumpf'], ((5, 1), (6, 1), (2, 4)), haut[2], x0, y0)                    # Loecher, Haut
    tupfen(px, m['rumpf'], ((5, 2), (2, 5)), haut[3], x0, y0)                            # Lochschatten
    for x in range(x0 + 1, x1):                                                          # zerfetzter Saum
        if (x, y1) in m['rumpf'] and x % 2 == 0:
            put(px, x, y1, ld)
    tupfen(px, m['rumpf'], ((4, 1), (4, 2)), lk, x0, y0)                                 # Naht
    gesicht(px, m['kopf'], haut, seitlich, hinten, haar=ton('haar'))
    kx0, ky0, kx1, ky1 = kasten(m['kopf'])
    cx = (kx0 + kx1) // 2
    if not hinten:
        tupfen(px, m['kopf'], ((2, 4), (1, 3), (8, 2)), haut[2], kx0, ky0)              # Flecken
        tupfen(px, m['kopf'], ((2, 5), (8, 3)), rgb('654956'), kx0, ky0)                # Bluterguss
        for ex, dy in ((cx - 2 + seitlich, 0), (cx + 2 + seitlich, 1)):   # hohle Augen, eins tiefer
            if kx0 < ex < kx1:
                put(px, ex, ky0 + 3 + dy, rgb(NACHT))
                put(px, ex + (1 if ex > cx else -1), ky0 + 3 + dy, rgb(NACHT))
                put(px, ex, ky0 + 4 + dy, haut[3])
                put(px, ex + (1 if ex > cx else -1), ky0 + 4 + dy, haut[2])
        for dx in (0, 1, 2):                                  # offener Mund, ein Zahn
            put(px, cx - 1 + dx + seitlich // 2, ky0 + 5, rgb(NACHT))
        put(px, cx + seitlich // 2, ky0 + 5, rgb('ddcebf'))
        put(px, cx + 2 + seitlich // 2, ky0 + 6, haut[3])     # haengender Mundwinkel
    bh, bm, bd, bk = ton('haar')
    for dx, dy, t in ((-4, 0, 1), (-3, -1, 0), (-2, 0, 1), (-1, -1, 0), (0, 0, 1), (1, -1, 0),
                      (2, 0, 1), (3, -1, 1), (4, 0, 2), (-5, 1, 2), (5, 1, 2), (-1, 0, 2), (3, 0, 2)):
        put(px, cx + dx, ky0 + dy, (bh, bm, bd, bk)[t])


def skeleton(px, m, seitlich, hinten, frame):
    bein = ton('bein')
    beine_malen(px, m['beine'], ton('beinhose'), ton('beinstiefel'))
    if m['beine']:                                            # Becken: zwei Kerben, Kreuzbein
        bx0, by0, bx1, by1 = kasten(m['beine'])
        bcx = (bx0 + bx1) // 2
        tupfen(px, m['beine'], ((bcx - bx0 - 1, 0), (bcx - bx0 + 2, 0)), bein[3], bx0, by0)
        tupfen(px, m['beine'], ((bcx - bx0, 0), (bcx - bx0 + 1, 0)), bein[0], bx0, by0)
    x0, y0, x1, y1 = kasten(m['rumpf'])
    cx = (x0 + x1) // 2
    if hinten:
        flaeche(px, m['rumpf'], bein, hals=False)
        for y in range(y0, y1 + 1):                           # Wirbelsaeule mit Wirbeln
            put(px, cx, y, bein[3] if y % 2 else bein[2])
            put(px, cx + 1, y, bein[2] if y % 2 else bein[1])
        for j in (0, 2):                                      # Schulterblaetter
            for dx in (2, 3):
                if (cx - dx, y0 + j) in m['rumpf']:
                    put(px, cx - dx, y0 + j, bein[2])
                if (cx + dx, y0 + j + 1) in m['rumpf']:
                    put(px, cx + dx, y0 + j + 1, bein[3])
    else:
        for x, y in m['rumpf']:                               # Brustkorb: dunkel, Rippen hell
            seite = (x - 1, y) not in m['rumpf'] or (x + 1, y) not in m['rumpf']
            put(px, x, y, bein[3] if seite else rgb(NACHT))
        for y in range(y0, y1 + 1):
            put(px, cx, y, bein[2] if y % 2 else bein[1])     # Brustbein mit Segmenten
        for j in (0, 2, 4):
            for dx in (1, 2, 3):
                yy = y0 + j + (1 if dx == 3 else 0)
                if (cx - dx, yy) in m['rumpf']:
                    put(px, cx - dx, yy, bein[1] if dx < 3 else bein[2])
                if (cx + dx, yy) in m['rumpf']:
                    put(px, cx + dx, yy, bein[0] if dx < 3 else bein[1])
        put(px, cx - 1, y0, bein[0]); put(px, cx + 1, y0, bein[0])            # Schluesselbein
    # Schaedel
    kx0, ky0, kx1, ky1 = kasten(m['kopf'])
    cx = (kx0 + kx1) // 2
    saum = rand(m['kopf'])
    flaeche(px, m['kopf'], bein, hals=False)
    tupfen(px, m['kopf'], ((3, 2), (4, 2), (3, 3)), bein[0], kx0, ky0)          # Stirnwoelbung
    if not hinten:
        for ex in (cx - 2 + seitlich, cx + 2 + seitlich):
            if kx0 < ex < kx1:
                for dx in (0, 1 if ex > cx else -1):
                    put(px, ex + dx, ky0 + 2, rgb(NACHT))
                    put(px, ex + dx, ky0 + 3, rgb(SCHWARZ))
                    put(px, ex + dx, ky0 + 4, bein[2])       # Wangenknochen
                put(px, ex, ky0 + 3, rgb('b25266'))           # Glimmen
        put(px, cx + seitlich // 2, ky0 + 4, bein[3])         # Nasenloch
        for x in range(cx - 2, cx + 3):
            put(px, x + seitlich // 2, ky0 + 5, bein[3] if x % 2 else bein[0])
        put(px, cx - 3 + seitlich // 2, ky0 + 5, bein[2])     # Kieferwinkel
        put(px, cx + 3 + seitlich // 2, ky0 + 5, bein[3])
        for x in range(cx - 2, cx + 3):                       # Unterkieferzeile
            if (x + seitlich // 2, ky0 + 6) in m['kopf']:
                put(px, x + seitlich // 2, ky0 + 6, bein[2] if x % 2 else bein[3])
    tupfen(px, m['kopf'], ((1, 2), (2, 3), (2, 4)), bein[3], kx0, ky0)          # Riss links
    if hinten:
        tupfen(px, m['kopf'], ((6, 3), (7, 4), (7, 5), (3, 5), (4, 6)), bein[3], kx0, ky0)   # Naehte
    rost = ton('rost')
    for x, y in m['kopf']:                                    # Rostkappe: obere zwei Zeilen
        if y <= ky0 + 1:
            put(px, x, y, rost[3] if (x, y) in saum else (rost[0] if x < cx - 1 and y == ky0 else (rost[1] if x < cx + 2 else rost[2])))
    tupfen(px, m['kopf'], ((3, 1), (7, 1), (8, 0)), rgb('b47538'), kx0, ky0)   # Rostflecken
    tupfen(px, m['kopf'], ((5, 0),), rgb('c5c7dd'), kx0, ky0)                  # Niete
    put(px, cx + 2, ky0, rost[2])


def ghoul(px, m, seitlich, hinten, frame):
    haut = ton('ghul')
    beine_malen(px, m['beine'], ton('ghulhose'), ton('stiefel'))
    flaeche(px, m['rumpf'], haut, falten=())
    x0, y0, x1, y1 = kasten(m['rumpf'])
    cx = (x0 + x1) // 2
    hh, hm, hd, hk = haut
    if hinten:                                                # Wirbelhoecker
        for y in range(y0, y1 + 1):
            put(px, cx, y, hk if y % 2 else hd)
            put(px, cx + 1, y, hd if y % 2 else hm)
    else:                                                     # Rippen scheinen durch, eingefallener Bauch
        for j in (1, 3):
            for dx in (1, 2, 3):
                if (cx - dx, y0 + j) in m['rumpf']:
                    put(px, cx - dx, y0 + j, hd)
                if (cx + dx, y0 + j) in m['rumpf']:
                    put(px, cx + dx, y0 + j, hk)
        tupfen(px, m['rumpf'], ((3, 4), (4, 4), (3, 5)), hd, x0, y0)
    tupfen(px, m['rumpf'], ((1, 2), (6, 1), (2, 4)), hk, x0, y0)               # Flecken
    gesicht(px, m['kopf'], haut, seitlich, hinten, haar=haut)
    kx0, ky0, kx1, ky1 = kasten(m['kopf'])
    cx = (kx0 + kx1) // 2
    tupfen(px, m['kopf'], ((1, 1), (8, 1), (2, 5), (7, 5), (4, 0)), hk, kx0, ky0)   # fleckige Haut
    if hinten:
        tupfen(px, m['kopf'], ((4, 3), (5, 4), (3, 5)), hd, kx0, ky0)          # Hinterkopf
    else:
        for ex in (cx - 2 + seitlich, cx + 2 + seitlich):
            if kx0 < ex < kx1:
                put(px, ex, ky0 + 3, rgb(GLUT))
                put(px, ex + (1 if ex > cx else -1), ky0 + 3, rgb(NACHT))
                put(px, ex, ky0 + 4, hd)
                put(px, ex + (1 if ex > cx else -1), ky0 + 4, hk)   # tiefe Augenhoehle
        for x in range(cx - 2, cx + 3):
            put(px, x + seitlich // 2, ky0 + 5, rgb(KRALLE) if x % 2 else rgb(NACHT))
        put(px, cx - 3 + seitlich // 2, ky0 + 5, rgb(NACHT))    # breites Maul
        put(px, cx + 3 + seitlich // 2, ky0 + 5, rgb(NACHT))
    put(px, kx0 - 1, ky0 + 2, hd); put(px, kx0 - 1, ky0 + 1, hm); put(px, kx0 - 2, ky0 + 1, hk)   # Ohren
    put(px, kx1 + 1, ky0 + 2, hd); put(px, kx1 + 1, ky0 + 1, hd); put(px, kx1 + 2, ky0 + 1, hk)
    # lange Arme neben dem Rumpf, Krallen; im Schritt schwingt einer
    schwung = 1 if frame in (2, 3, 8, 9) else 0
    for sgn, ax in ((-1, x0 - 2), (1, x1 + 2)):
        laenge = (y1 - y0) + 3 + (schwung if sgn > 0 else 0)
        for j in range(laenge):
            put(px, ax, y0 + 1 + j, hm if sgn < 0 else hd)
            put(px, ax + sgn, y0 + 1 + j, hd if sgn < 0 else hk)
            if j % 3 == 2:                                    # Sehnen
                put(px, ax, y0 + 1 + j, hd if sgn < 0 else hk)
        put(px, ax, y0 + 1, hh if sgn < 0 else hm)
        hy = y0 + 1 + laenge
        for k in range(3):
            put(px, ax + sgn * (k - 1), hy + (1 if k == 1 else 0), rgb(KRALLE))
        put(px, ax + sgn, hy + 1, hk)


def cultist(px, m, seitlich, hinten, frame):
    robe = ton('robe')
    rh, rm, rd, rk = robe
    beine_malen(px, m['beine'], robe, ton('stiefel'))
    if m['beine']:                                            # Robensaum: haengende Falten
        bx0, by0, bx1, by1 = kasten(m['beine'])
        for x, y in m['beine']:
            if (x - 1, y) in m['beine'] and (x + 1, y) in m['beine']:
                put(px, x, y, rd if (x - bx0) % 2 else rm)
    flaeche(px, m['rumpf'], robe)
    x0, y0, x1, y1 = kasten(m['rumpf'])
    cx = (x0 + x1) // 2
    for x, y in m['rumpf']:                                   # haengende Falten: senkrechte Rinnen
        if y > y0 and (x - 1, y) in m['rumpf'] and (x + 1, y) in m['rumpf']:
            if (x - x0) in (2, 5):
                put(px, x, y, rd)
            elif (x - x0) in (1, 4):
                put(px, x, y, rh if y < y0 + 3 else rm)
    lh, lm, ld, lk = ton('leder')
    for x in range(x0 + 1, x1):                               # Strick als Guertel
        if (x, y0 + 3) in m['rumpf']:
            put(px, x, y0 + 3, lm if x % 2 else ld)
    put(px, cx - 1, y0 + 3, lh); put(px, cx - 1, y0 + 4, ld); put(px, cx - 1, y0 + 5, lk)   # Knoten, Ende
    if not hinten:                                            # Augensymbol
        put(px, cx - 1, y0 + 1, rk); put(px, cx + 2, y0 + 1, rk)
        put(px, cx, y0 + 1, rgb(GLUT_DK)); put(px, cx + 1, y0 + 1, rgb(GLUT))
        for x in range(cx - 1, cx + 3):
            put(px, x, y0 + 2, rk)
        put(px, cx, y0, rk); put(px, cx + 1, y0, rk)
    kx0, ky0, kx1, ky1 = kasten(m['kopf'])
    cx = (kx0 + kx1) // 2
    saum = rand(m['kopf'])
    for x, y in m['kopf']:                                    # Kapuze mit Schattengesicht
        innen = (not hinten) and (kx0 + 1 < x < kx1 - 1) and (ky0 + 2 <= y <= ky1 - 1)
        if innen:
            col = rgb(NACHT) if y > ky0 + 2 or x > kx0 + 2 else rgb('2d1b1e')
        elif (x, y) in saum:
            col = rk if x > cx or y == ky1 else rd
        else:
            col = rh if x < cx - 1 and y < ky0 + 3 else (rm if x < cx + 2 else rd)
        put(px, x, y, col)
    for dx, dy in ((1, 2), (1, 3), (1, 4), (8, 3), (8, 4), (8, 5)):                # Kapuzenrand
        if (kx0 + dx, ky0 + dy) in m['kopf']:
            put(px, kx0 + dx, ky0 + dy, rh if dx == 1 else rd)
    tupfen(px, m['kopf'], ((3, 1), (4, 1), (6, 1)), rh, kx0, ky0)              # Stofflicht oben
    tupfen(px, m['kopf'], ((5, 2), (7, 2)), rk, kx0, ky0)                      # Falte am Scheitel
    if hinten:
        tupfen(px, m['kopf'], ((3, 3), (3, 4), (3, 5), (6, 3), (6, 4), (6, 5)), rd, kx0, ky0)   # Faltenrinnen
    if not hinten:
        for ex in (cx - 2 + seitlich, cx + 2 + seitlich):
            if kx0 + 1 < ex < kx1 - 1:
                put(px, ex, ky0 + 3, rgb(GLUT)); put(px, ex, ky0 + 4, rgb(GLUT_DK))
    put(px, cx, ky0 - 1, rm); put(px, cx + 1, ky0 - 1, rd)      # Kapuzenspitze
    put(px, cx + 1, ky0 - 2, rd)


def mummy(px, m, seitlich, hinten, frame):
    binde = ton('binde')
    bh, bm, bd, bk = binde
    beine_malen(px, m['beine'], binde, ton('bindestiefel'))
    flaeche(px, m['rumpf'], binde)
    flaeche(px, m['kopf'], binde, hals=False)
    fleck = rgb('886e6a')
    for teil in ('kopf', 'rumpf', 'beine'):                   # Bandagen: jede Lage mit heller
        for x, y in m[teil]:                                  # Oberkante und dunkler Unterkante
            if teil == 'beine' and (x - 1, y) not in m[teil]:
                continue
            r = (y + x // 4) % 3                              # Wickellinien, leicht schraeg
            if r == 0:
                put(px, x, y, bd if (x + y) % 5 else bk)
            elif r == 1 and (x - y) % 3 == 0:
                put(px, x, y, bh)
    tupfen(px, m['rumpf'], ((2, 2), (6, 1), (3, 5)), fleck)                    # Flecken
    tupfen(px, m['kopf'], ((7, 1), (2, 5)), fleck)
    kx0, ky0, kx1, ky1 = kasten(m['kopf'])
    cx = (kx0 + kx1) // 2
    if not hinten:                                            # Augenschlitz, ein Auge
        for x in range(kx0 + 1 + max(0, seitlich), kx1):
            put(px, x, ky0 + 3, rgb(NACHT))
            put(px, x, ky0 + 2, bd)                           # Bandage haengt ueber den Schlitz
        put(px, cx + 1 + seitlich, ky0 + 3, rgb(AUGE)); put(px, cx + 2 + seitlich, ky0 + 3, rgb(AUGE))
        put(px, cx + 1 + seitlich, ky0 + 4, rgb(AUGE))
        put(px, cx + 2 + seitlich, ky0 + 2, bh)
        put(px, cx - 2 + seitlich, ky0 + 4, rgb('2d1b1e'))    # Schatten unter dem Schlitz
    for j in range(3):                                        # lose Enden
        put(px, kx0 - 1, ky0 + 4 + j, bd if j < 2 else bk)
    put(px, kx0 - 2, ky0 + 6, bk)
    x0, y0, x1, y1 = kasten(m['rumpf'])
    put(px, x1 + 1, y0 + 3, bd); put(px, x1 + 1, y0 + 4, bk); put(px, x1 + 2, y0 + 5, bk)


def bandit(px, m, seitlich, hinten, frame):
    beine_malen(px, m['beine'], ton('hosen'), ton('leder'))
    flaeche(px, m['rumpf'], ton('lumpen'), falten=((0, 0, 3, 1), (7, 0, 3, -1)))
    x0, y0, x1, y1 = kasten(m['rumpf'])
    cx = (x0 + x1) // 2
    lh, lm, ld, lk = ton('leder')
    if not hinten:                                            # Weste mit Naht, Guertel, Dolch
        for y in range(y0, y1 - 1):
            for dx in (-2, -1, 1, 2):
                if (cx + dx, y) in m['rumpf']:
                    col = lm if abs(dx) == 1 else ld
                    if abs(dx) == 2 and y % 2:
                        col = lk                              # Stiche am Westenrand
                    put(px, cx + dx, y, col)
        put(px, cx - 1, y0, lh)                               # Lichtkante Schulter
        for x in range(x0 + 1, x1):
            if (x, y1 - 1) in m['rumpf']:
                put(px, x, y1 - 1, lk)
        put(px, cx + 1, y1 - 1, rgb('f8c53a')); put(px, cx, y1 - 1, rgb('e88a36'))
        put(px, x1, y1, rgb('c5c7dd')); put(px, x1, y1 + 1, rgb('9a97b9')); put(px, x1, y1 - 1, lk)
    else:                                                     # Weste von hinten, Rueckennaht
        for y in range(y0, y1 - 1):
            for dx in (-2, -1, 0, 1, 2):
                if (cx + dx, y) in m['rumpf']:
                    put(px, cx + dx, y, ld if dx == 0 else (lm if dx < 0 else ld))
        for x in range(x0 + 1, x1):
            if (x, y1 - 1) in m['rumpf']:
                put(px, x, y1 - 1, lk)
    gesicht(px, m['kopf'], ton('haut'), seitlich, hinten, haar=ton('haar'))
    kx0, ky0, kx1, ky1 = kasten(m['kopf'])
    cx = (kx0 + kx1) // 2
    th, tm, td, tk = ton('tuch')
    saum = rand(m['kopf'])
    if not hinten:
        for x in range(kx0 + 1, kx1):                         # Halstuch ueber dem Mund, gemustert
            if (x, ky0 + 5) in m['kopf']:
                put(px, x, ky0 + 5, th if x < cx else tm)
            if (x, ky0 + 6) in m['kopf']:
                put(px, x, ky0 + 6, tm if x < cx + 1 else td)
        put(px, cx - 2, ky0 + 6, td)                          # Falte im Tuch
        put(px, kx1 - 1, ky0 + 5, td); put(px, kx1 - 1, ky0 + 6, tk)         # Schattenseite
        if seitlich == 0:                                     # Augenklappe links mit Band
            put(px, cx - 2, ky0 + 3, rgb(NACHT)); put(px, cx - 3, ky0 + 3, rgb(NACHT))
            put(px, cx - 2, ky0 + 4, rgb(NACHT)); put(px, cx - 4, ky0 + 2, rgb(NACHT))
        tupfen(px, m['kopf'], ((7, 4),), rgb('e27285'), kx0, ky0)              # Narbe / Wange
    for x, y in m['kopf']:                                    # Kopftuch: obere zwei Zeilen
        if y <= ky0 + 1:
            put(px, x, y, tk if (x, y) in saum else (th if x < cx - 1 and y == ky0 else (tm if x < cx + 2 else td)))
    tupfen(px, m['kopf'], ((3, 1), (6, 0)), td, kx0, ky0)                     # Falten im Tuch
    put(px, kx1 + 1, ky0 + 1, td); put(px, kx1 + 1, ky0 + 2, tm); put(px, kx1 + 2, ky0 + 2, tk)   # Knoten, Zipfel


GEGNER = {'zombie': zombie, 'skeleton_warrior': skeleton, 'ghoul': ghoul,
          'cultist': cultist, 'mummy': mummy, 'bandit': bandit}


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
    seitlich = 1 if richtung in ('FSide', 'BSide') else 0
    if m['kopf'] and m['rumpf']:
        bauen(px, m, seitlich, hinten, nr if anim == 'walk' else 1)
    return duel_anpassen(img)


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
            blatt = Image.new('RGBA', (10 * 34 * sc, len(zeilen) * 34 * sc), (23, 21, 22, 255))
            for r, reihe in enumerate(zeilen):
                for i, im in enumerate(reihe):
                    blatt.alpha_composite(im.resize((32 * sc, 32 * sc), Image.NEAREST), (i * 34 * sc + sc, r * 34 * sc + sc))
            blatt.save(ziel / '_sheet.png')
        print('  %-18s %d Frames -> %s' % (name, gesamt, ziel))


if __name__ == '__main__':
    main()
