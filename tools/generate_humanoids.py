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


def flaeche(px, punkte, toene):
    """Fuellt eine Maske: Licht links, Mitte, Schatten rechts, unterste Zeile
    dunkel, Seitenrand als Kante. Symmetrische Form, gerichtetes Licht."""
    hell, mitte, dunkel, kante = toene
    x0, y0, x1, y1 = kasten(punkte)
    for x, y in punkte:
        seite = (x - 1, y) not in punkte or (x + 1, y) not in punkte
        u = (x - x0 + 0.5) / (x1 - x0 + 1)
        if seite:
            col = kante
        elif (x, y + 1) not in punkte:
            col = dunkel
        elif u < 0.3:
            col = hell
        elif u > 0.72:
            col = dunkel
        else:
            col = mitte
        put(px, x, y, col)


def beine_malen(px, punkte, hose, stiefel):
    """Beinblock in Hosenfarbe, die duennen Striche als Stiefel, der unterste
    Pixel je Strich als Sohle."""
    if not punkte:                                          # Tod: im Boden versunken
        return
    hh, hm, hd, hk = hose
    sh, sm, sd, sk = stiefel
    x0, y0, x1, y1 = kasten(punkte)
    breit = {y: sum(1 for (x, yy) in punkte if yy == y) for y in range(y0, y1 + 1)}
    for x, y in punkte:
        if breit[y] >= 5:                                   # Block: Hose
            seite = (x - 1, y) not in punkte or (x + 1, y) not in punkte
            put(px, x, y, hk if seite else (hm if x < (x0 + x1) / 2 else hd))
        else:                                               # Strich: Stiefel
            unten = (x, y + 1) not in punkte
            put(px, x, y, sk if unten else sm)


def gesicht(px, kopf, haut, seitlich, hinten, haar=None):
    """Gesicht in die Kopfmaske: Haut mit Licht links, Augen als 2x2 in
    Wein, Mund. seitlich rueckt die Zuege, hinten zeigt Haar/Hinterkopf."""
    hh, hm, hd, hk = haut
    x0, y0, x1, y1 = kasten(kopf)
    cx = (x0 + x1) // 2
    saum = rand(kopf)
    for x, y in kopf:
        u = (x - x0 + 0.5) / (x1 - x0 + 1)
        col = hk if (x, y) in saum else (hh if u < 0.3 and y < y1 - 1 else (hd if u > 0.72 or y >= y1 - 1 else hm))
        put(px, x, y, col)
    if hinten:
        if haar:
            bh, bm, bd, bk = haar
            for x, y in kopf:
                u = (x - x0 + 0.5) / (x1 - x0 + 1)
                put(px, x, y, bk if (x, y) in saum else (bm if u < 0.6 else bd))
        return
    ey = y0 + 3
    for ex in (cx - 2 + seitlich, cx + 2 + seitlich):
        if x0 < ex < x1:
            put(px, ex, ey, rgb(AUGE))
            put(px, ex + (1 if ex > cx else -1), ey, rgb(AUGE))
            put(px, ex, ey + 1, rgb(AUGE))
    if seitlich:                                            # hinteres Auge verdeckt
        put(px, cx - 2 + seitlich, ey, hm)
        put(px, cx - 3 + seitlich, ey, hm)
        put(px, cx - 2 + seitlich, ey + 1, hm)
    for dx in (0, 1):
        put(px, cx + dx + seitlich // 2, y0 + 5, hk)


# --- Gegner: Kopf, Rumpf, Extras ------------------------------------------------------

def zombie(px, m, seitlich, hinten, frame):
    haut = ton('moder')
    beine_malen(px, m['beine'], ton('hosen'), ton('stiefel'))
    flaeche(px, m['rumpf'], ton('lumpen'))
    x0, y0, x1, y1 = kasten(m['rumpf'])
    for dx, dy in ((1, 1), (5, 2), (3, 4), (6, 4)):         # Loecher, Haut scheint durch
        if (x0 + dx, y0 + dy) in m['rumpf']:
            put(px, x0 + dx, y0 + dy, haut[2])
    gesicht(px, m['kopf'], haut, seitlich, hinten, haar=ton('haar'))
    kx0, ky0, kx1, ky1 = kasten(m['kopf'])
    cx = (kx0 + kx1) // 2
    if not hinten:
        for ex, dy in ((cx - 2 + seitlich, 0), (cx + 2 + seitlich, 1)):   # hohle Augen, eins tiefer
            if kx0 < ex < kx1:
                put(px, ex, ky0 + 3 + dy, rgb(NACHT))
                put(px, ex + (1 if ex > cx else -1), ky0 + 3 + dy, rgb(NACHT))
                put(px, ex, ky0 + 4 + dy, haut[3])
        for dx in (0, 1, 2):                                  # offener Mund
            put(px, cx - 1 + dx + seitlich // 2, ky0 + 5, rgb(NACHT))
    bh, bm, bd, bk = ton('haar')
    for dx, dy, t in ((-4, 0, 1), (-3, -1, 0), (-2, 0, 1), (-1, -1, 0), (0, 0, 1), (1, -1, 0),
                      (2, 0, 1), (3, -1, 1), (4, 0, 2), (-5, 1, 2), (5, 1, 2)):
        put(px, cx + dx, ky0 + dy, (bh, bm, bd, bk)[t])


def skeleton(px, m, seitlich, hinten, frame):
    bein = ton('bein')
    beine_malen(px, m['beine'], ton('beinhose'), ton('beinstiefel'))
    x0, y0, x1, y1 = kasten(m['rumpf'])
    cx = (x0 + x1) // 2
    if hinten:
        flaeche(px, m['rumpf'], bein)
        for y in range(y0, y1 + 1):                           # Wirbelsaeule
            put(px, cx, y, bein[3])
    else:
        for x, y in m['rumpf']:                               # Brustkorb: dunkel, Rippen hell
            seite = (x - 1, y) not in m['rumpf'] or (x + 1, y) not in m['rumpf']
            put(px, x, y, bein[3] if seite else rgb(NACHT))
        for y in range(y0, y1 + 1):
            put(px, cx, y, bein[2])
        for j in (0, 2, 4):
            for dx in (1, 2, 3):
                yy = y0 + j + (1 if dx == 3 else 0)
                if (cx - dx, yy) in m['rumpf']:
                    put(px, cx - dx, yy, bein[1])
                if (cx + dx, yy) in m['rumpf']:
                    put(px, cx + dx, yy, bein[0])
    # Schaedel
    kx0, ky0, kx1, ky1 = kasten(m['kopf'])
    cx = (kx0 + kx1) // 2
    saum = rand(m['kopf'])
    for x, y in m['kopf']:
        u = (x - kx0 + 0.5) / (kx1 - kx0 + 1)
        put(px, x, y, bein[3] if (x, y) in saum else (bein[0] if u < 0.35 and y < ky1 - 1 else (bein[2] if u > 0.75 else bein[1])))
    if not hinten:
        for ex in (cx - 2 + seitlich, cx + 2 + seitlich):
            if kx0 < ex < kx1:
                for dx in (0, 1 if ex > cx else -1):
                    put(px, ex + dx, ky0 + 2, rgb(NACHT))
                    put(px, ex + dx, ky0 + 3, rgb(SCHWARZ))
                put(px, ex, ky0 + 3, rgb('b25266'))           # Glimmen
        put(px, cx + seitlich // 2, ky0 + 4, bein[3])
        for x in range(cx - 2, cx + 3):
            put(px, x + seitlich // 2, ky0 + 5, bein[3] if x % 2 else bein[0])
    rost = ton('rost')
    for x, y in m['kopf']:                                    # Rostkappe: obere zwei Zeilen
        if y <= ky0 + 1:
            put(px, x, y, rost[3] if (x, y) in saum else (rost[0] if x < cx else rost[1]))
    put(px, cx + 2, ky0, rost[2])


def ghoul(px, m, seitlich, hinten, frame):
    haut = ton('ghul')
    beine_malen(px, m['beine'], ton('ghulhose'), ton('stiefel'))
    flaeche(px, m['rumpf'], haut)
    x0, y0, x1, y1 = kasten(m['rumpf'])
    gesicht(px, m['kopf'], haut, seitlich, hinten, haar=haut)
    kx0, ky0, kx1, ky1 = kasten(m['kopf'])
    cx = (kx0 + kx1) // 2
    if not hinten:
        for ex in (cx - 2 + seitlich, cx + 2 + seitlich):
            if kx0 < ex < kx1:
                put(px, ex, ky0 + 3, rgb(GLUT))
                put(px, ex + (1 if ex > cx else -1), ky0 + 3, rgb(NACHT))
                put(px, ex, ky0 + 4, haut[1])
        for x in range(cx - 2, cx + 3):
            put(px, x + seitlich // 2, ky0 + 5, rgb(KRALLE) if x % 2 else rgb(NACHT))
    put(px, kx0 - 1, ky0 + 2, haut[2]); put(px, kx0 - 1, ky0 + 1, haut[1])      # Ohren
    put(px, kx1 + 1, ky0 + 2, haut[2]); put(px, kx1 + 1, ky0 + 1, haut[1])
    # lange Arme neben dem Rumpf, Krallen; im Schritt schwingt einer
    hh, hm, hd, hk = haut
    schwung = 1 if frame in (2, 3, 8, 9) else 0
    for sgn, ax in ((-1, x0 - 2), (1, x1 + 2)):
        laenge = (y1 - y0) + 3 + (schwung if sgn > 0 else 0)
        for j in range(laenge):
            put(px, ax, y0 + 1 + j, hm if sgn < 0 else hd)
            put(px, ax + sgn, y0 + 1 + j, hd if sgn < 0 else hk)
        put(px, ax, y0 + 1, hh)
        hy = y0 + 1 + laenge
        for k in range(3):
            put(px, ax + sgn * (k - 1), hy + (1 if k == 1 else 0), rgb(KRALLE))


def cultist(px, m, seitlich, hinten, frame):
    robe = ton('robe')
    beine_malen(px, m['beine'], robe, ton('stiefel'))
    flaeche(px, m['rumpf'], robe)
    x0, y0, x1, y1 = kasten(m['rumpf'])
    cx = (x0 + x1) // 2
    if not hinten:                                            # Augensymbol
        put(px, cx - 1, y0 + 1, robe[3]); put(px, cx + 2, y0 + 1, robe[3])
        put(px, cx, y0 + 1, rgb(GLUT_DK)); put(px, cx + 1, y0 + 1, rgb(GLUT))
        for x in range(cx - 1, cx + 3):
            put(px, x, y0 + 2, robe[3])
    kx0, ky0, kx1, ky1 = kasten(m['kopf'])
    cx = (kx0 + kx1) // 2
    saum = rand(m['kopf'])
    for x, y in m['kopf']:                                    # Kapuze mit Schattengesicht
        innen = (not hinten) and (kx0 + 1 < x < kx1 - 1) and (ky0 + 2 <= y <= ky1 - 1)
        put(px, x, y, rgb(NACHT) if innen else (robe[3] if (x, y) in saum else (robe[0] if x < cx - 1 and y < ky0 + 3 else robe[1])))
    if not hinten:
        for ex in (cx - 2 + seitlich, cx + 2 + seitlich):
            if kx0 + 1 < ex < kx1 - 1:
                put(px, ex, ky0 + 3, rgb(GLUT)); put(px, ex, ky0 + 4, rgb(GLUT_DK))
    put(px, cx, ky0 - 1, robe[1]); put(px, cx + 1, ky0 - 1, robe[2])      # Kapuzenspitze


def mummy(px, m, seitlich, hinten, frame):
    binde = ton('binde')
    beine_malen(px, m['beine'], binde, ton('bindestiefel'))
    flaeche(px, m['rumpf'], binde)
    saum = rand(m['kopf'])
    for x, y in m['kopf']:
        put(px, x, y, binde[3] if (x, y) in saum else binde[1])
    for teil in ('kopf', 'rumpf'):                            # schraege Bandagen
        for x, y in m[teil]:
            r = (x + y * 2) % 6
            if r == 0:
                put(px, x, y, binde[3])
            elif r == 1:
                put(px, x, y, binde[2])
    kx0, ky0, kx1, ky1 = kasten(m['kopf'])
    cx = (kx0 + kx1) // 2
    if not hinten:                                            # Augenschlitz, ein Auge
        for x in range(kx0 + 1 + max(0, seitlich), kx1):
            put(px, x, ky0 + 3, rgb(NACHT))
        put(px, cx + 1 + seitlich, ky0 + 3, rgb(AUGE)); put(px, cx + 2 + seitlich, ky0 + 3, rgb(AUGE))
        put(px, cx + 1 + seitlich, ky0 + 4, rgb(AUGE))
        put(px, cx + 2 + seitlich, ky0 + 2, binde[0])
    for j in range(3):                                        # lose Enden
        put(px, kx0 - 1, ky0 + 4 + j, binde[2] if j < 2 else binde[3])
    x0, y0, x1, y1 = kasten(m['rumpf'])
    put(px, x1 + 1, y0 + 3, binde[2]); put(px, x1 + 1, y0 + 4, binde[3])


def bandit(px, m, seitlich, hinten, frame):
    beine_malen(px, m['beine'], ton('hosen'), ton('leder'))
    flaeche(px, m['rumpf'], ton('lumpen'))
    x0, y0, x1, y1 = kasten(m['rumpf'])
    cx = (x0 + x1) // 2
    lh, lm, ld, lk = ton('leder')
    if not hinten:                                            # Weste, Guertel, Dolch
        for y in range(y0, y1 - 1):
            for dx in (-2, -1, 1, 2):
                if (cx + dx, y) in m['rumpf']:
                    put(px, cx + dx, y, lm if abs(dx) == 1 else ld)
        for x in range(x0 + 1, x1):
            if (x, y1 - 1) in m['rumpf']:
                put(px, x, y1 - 1, lk)
        put(px, cx + 1, y1 - 1, rgb('f8c53a'))
        put(px, x1, y1, rgb('c5c7dd')); put(px, x1, y1 + 1, rgb('9a97b9'))
    gesicht(px, m['kopf'], ton('haut'), seitlich, hinten, haar=ton('haar'))
    kx0, ky0, kx1, ky1 = kasten(m['kopf'])
    cx = (kx0 + kx1) // 2
    th, tm, td, tk = ton('tuch')
    saum = rand(m['kopf'])
    if not hinten:
        for x in range(kx0 + 1, kx1):                         # Halstuch ueber dem Mund
            if (x, ky0 + 5) in m['kopf']:
                put(px, x, ky0 + 5, th)
            if (x, ky0 + 6) in m['kopf']:
                put(px, x, ky0 + 6, tm)
        if seitlich == 0:                                     # Augenklappe links
            put(px, cx - 2, ky0 + 3, rgb(NACHT)); put(px, cx - 3, ky0 + 3, rgb(NACHT))
            put(px, cx - 2, ky0 + 2, rgb(NACHT)); put(px, cx - 4, ky0 + 2, rgb(NACHT))
    for x, y in m['kopf']:                                    # Kopftuch: obere zwei Zeilen
        if y <= ky0 + 1:
            put(px, x, y, tk if (x, y) in saum else (th if x < cx else tm))
    put(px, kx1 + 1, ky0 + 1, td); put(px, kx1 + 1, ky0 + 2, tm)            # Knoten


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
