#!/usr/bin/env python3
"""Waffen im Stil von assets/sprites/weapons/giant_bone_sword.png.

Eigener Generator, weil dieser Stil an drei Stellen anders arbeitet als
tools/generate_weapons.py:

  * Palette AAP-64 statt Resurrect 64. Die eigenen Sprites im Projekt
    (giant_bone_sword.png, gras_sword.png) liegen vollstaendig auf AAP-64.
  * Die Klinge hat eine dunkle Hohlkehle in der Mitte, keinen hellen Grat.
    Der Querschnitt ist aus dem Knochengrossschwert Pixel fuer Pixel
    abgelesen: Kante, Weiss, Hell, harter Abfall, Mitte, Licht, drei Pixel
    Rinne, und dieselbe Folge zurueck zum dunklen Ruecken.
  * Die dunkle Materialkante ist eingebacken. Der schwarze Rand aus dem
    Spiel legt sich darueber, statt sie zu ersetzen.

Groessen richten sich nach der Waffenart, nicht nach einer festen Leinwand:
ein Grossschwert ist deutlich groesser als ein Dolch.

    python tools/generate_weapons_aap.py            # -> assets/sprites/weapons/
    python tools/generate_weapons_aap.py --out DIR --sheet
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image

from pixelregeln import bericht as flaechen_bericht, entflechten

MARGIN = 1

# --- Palette: AAP-64 (lospec.com/palette-list/aap-64) -----------------------

AAP = {
    'schwarz': '060608', 'tiefschwarz': '141013',
    'stahl_hell': 'dae0ea', 'stahl_licht': 'b3b9d1', 'stahl_mitte': '8b93af',
    'stahl_fase': '6d758d', 'stahl_dunkel': '4a5462', 'stahl_tief': '333941',
    'stahl_kante': '242234',
    'weiss': 'ffffff', 'creme': 'fef3c0',
    'knochen_licht': 'e4d2aa', 'knochen_mitte': 'c7b08b',
    'knochen_fase': 'a08662', 'knochen_dunkel': '796755',
    'knochen_tief': '5a4e44', 'knochen_kante': '423934',
    'leder_hell': 'f4d29c', 'leder_licht': 'dba463', 'leder_mitte': 'bb7547',
    'leder_dunkel': '71413b', 'leder_tief': '5b3138',
    'gold_hell': 'fffc40', 'gold': 'ffd541', 'gold_mitte': 'f9a31b',
    'gold_dunkel': 'fa6a0a', 'kupfer': 'df3e23',
    'stein_gruen': '59c135', 'stein_gruen_dk': '1a7a3e',
    'stein_blau': '249fde', 'stein_blau_dk': '285cc4',
    'rost': '8e5252', 'rost_dk': '5b3138',
    'kristall_hell': 'a6fcdb', 'kristall_licht': '20d6c7',
    'kristall_mitte': '249fde', 'kristall_dunkel': '285cc4',
    'kristall_tief': '143464',
    'feuer_rot': 'b4202a', 'feuer_dk': '73172d', 'feuer_tief': '3b1725',
    'gift_hell': 'bc4a9b', 'gift': '793a80', 'gift_dk': '403353',
    'rubin_hell': 'e86a73', 'gift_glanz': 'e86a73', 'gift_schaum': 'f5a097',
    'gruen_hell': '9cdb43', 'gruen': '59c135', 'gruen_mitte': '14a02e',
    'gruen_dk': '1a7a3e', 'gruen_tief': '24523b', 'saphir': '249fde',
    'eis_hell': 'a6fcdb', 'eis': '20d6c7', 'eis_dk': '249fde', 'eis_tief': '285cc4',
    'eis_nacht': '143464', 'blitz': 'fffc40', 'smaragd': '59c135', 'smaragd_dk': '1a7a3e',
    'schatten': '242234', 'schatten_dk': '141013', 'lila_hell': 'bc4a9b',
}


def C(name):
    h = AAP[name]
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


PALETTE_RGB = {tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for h in AAP.values()}


# --- Zeichenkern ------------------------------------------------------------

def blank(w, h=None):
    return Image.new('RGBA', (w, h or w), (0, 0, 0, 0))


def put(img, x, y, col):
    if MARGIN <= x < img.width - MARGIN and MARGIN <= y < img.height - MARGIN:
        img.putpixel((int(x), int(y)), col)


def to_uv(x, y, ox, oy):
    dx, dy = x - ox, y - oy
    return ((dx - dy) / 2.0, (dx + dy) / 2.0)


def to_xy(u, v, ox, oy):
    return (int(round(ox + u + v)), int(round(oy - u + v)))


def speck(img, ox, oy, u, v, col):
    x, y = to_xy(u, v, ox, oy)
    put(img, x, y, C(col))


# --- Klinge -----------------------------------------------------------------
# Querschnitt aus giant_bone_sword.png, Zeile 12, abgelesen. Die Zahlen sind
# Anteile der Klingenbreite von der Schneide zum Ruecken.

# Der Querschnitt aus giant_bone_sword.png in ABSOLUTEN Pixeln, nicht in
# Anteilen. Die Schneidenfase ist dort 1 px weiss und 1 px hell - egal wie
# breit die Klinge ist. Rechnet man in Anteilen, wird die Fase bei breiten
# Klingen mitskaliert und die Klinge verliert ihre Schaerfe.
#
#   von der Schneide:  1 Kante | 1 Weiss | 1 Hell | 1 Fase
#   von hinten:        1 Kante | 1 Ruecken | 1 Fase
#   in der Mitte:      3 px Hohlkehle
#   dazwischen:        Flaechen, die die restliche Breite aufnehmen

STAHL = {'kante': 'stahl_kante', 'glanz': 'weiss', 'hell': 'stahl_hell',
         'fase': 'stahl_fase', 'mitte': 'stahl_mitte', 'licht': 'stahl_licht',
         'rinne': 'stahl_tief', 'ruecken': 'stahl_dunkel'}

KNOCHEN = {'kante': 'knochen_kante', 'glanz': 'weiss', 'hell': 'creme',
           'fase': 'knochen_dunkel', 'mitte': 'knochen_mitte',
           'licht': 'knochen_licht', 'rinne': 'knochen_tief',
           'ruecken': 'knochen_tief'}

KUPFER = {'kante': 'rost_dk', 'glanz': 'gold_hell', 'hell': 'gold',
          'fase': 'leder_dunkel', 'mitte': 'leder_mitte',
          'licht': 'leder_licht', 'rinne': 'rost_dk', 'ruecken': 'rost'}


# Querschnitt als Folge von 1-px-Baendern. Beim great_bone_sword der Vorlage
# ist die Klinge 12 px breit und hat KEINE Flaeche: von der Schneide her
#   Kante | Weiss | Creme | dunkle Linie | Mitte | Licht | Kehle x3 |
#   Licht | Mitte | Fase | Ruecken | Kante
# Jedes Band ist ein Pixel breit. Breite Klingen bekommen also mehr Baender,
# nicht groessere Flaechen - und weil die Klinge diagonal liegt, beruehren
# sich die Pixel eines Bandes nur ueber Eck.

_BAENDER = {}


def baender(breite, rinne, ricasso):
    key = (breite, rinne, ricasso)
    if key in _BAENDER:
        return _BAENDER[key]
    vorn = ['kante', 'glanz', 'hell', 'fase', 'mitte', 'licht']
    # Kehle: drei dunkle Baender, das mittlere am dunkelsten - drei gleiche
    # Diagonalen waeren eine Flaeche und wuerden zerlegt
    kehle = ['rinne', 'kante', 'rinne'] if rinne else []
    hinten = ['licht', 'mitte', 'fase', 'ruecken', 'kante']
    # Reihenfolge, in der Baender wegfallen, wenn die Klinge schmaler ist
    weg = [(vorn, 'licht'), (hinten, 'licht'), (vorn, 'fase'), (hinten, 'mitte'),
           (vorn, 'mitte'), (kehle, 'kante'), (kehle, 'rinne'), (hinten, 'fase'),
           (kehle, 'rinne'), (vorn, 'hell'), (hinten, 'ruecken'), (vorn, 'glanz')]
    while len(vorn) + len(kehle) + len(hinten) > breite and weg:
        liste, name = weg.pop(0)
        if name in liste:
            liste.remove(name)
    if len(kehle) == 2:                     # ohne dunkle Mitte: Kehle und Wand
        kehle[:] = ['rinne', 'fase']
    # breiter als das volle Muster: die Schneidenseite liegt zum Licht, die
    # Rueckenseite im Schatten. Vorn kommen helle Baender dazu (Hell | Licht),
    # hinten dunkle (Fase | Ruecken). So bekommt eine breite Klinge eine
    # Lichtseite und eine Schattenseite - einen Koerper, keine Streifen.
    fehlt = breite - len(vorn) - len(kehle) - len(hinten)
    i = 0
    while fehlt > 0:
        if i % 2 == 0:
            vorn.append(('hell', 'licht')[(i // 2) % 2])
        else:
            hinten.insert(hinten.index('ruecken') + 1 + (i // 2), ('fase', 'ruecken')[(i // 2) % 2])
        fehlt -= 1
        i += 1
    reihe = vorn + kehle + hinten
    for i in range(1, len(reihe) - 1):     # ohne Kehle stossen zwei Licht aneinander
        if reihe[i] == reihe[i - 1]:
            reihe[i] = next(n for n in ('mitte', 'licht', 'fase')
                            if n not in (reihe[i - 1], reihe[i + 1]))
    if ricasso:                            # ungeschliffen: kein Glanz, keine Kehle
        reihe = ['fase' if n == 'glanz' else 'mitte' if n == 'hell' else
                 'mitte' if n == 'rinne' else n for n in reihe]
    _BAENDER[key] = reihe
    return reihe


_FARBBAENDER = {}


def farbbaender(ton, breite, rinne, ricasso):
    """Baender als Farbnamen der Rampe. Zwei Baender mit derselben Farbe
    (etwa Kehle und Kante beider aus stahl_kante) wuerden zur Flaeche -
    das zweite bekommt den naechsten anderen Ton."""
    key = (id(ton), breite, rinne, ricasso)
    if key in _FARBBAENDER:
        return _FARBBAENDER[key]
    reihe = [ton[n] for n in baender(breite, rinne, ricasso)]
    ersatz = [ton[n] for n in ('fase', 'mitte', 'licht', 'ruecken', 'hell', 'rinne')]
    for i in range(1, len(reihe)):
        if reihe[i] == reihe[i - 1]:
            rechts = reihe[i + 1] if i + 1 < len(reihe) else None
            reihe[i] = next(c for c in ersatz if c not in (reihe[i - 1], rechts))
    _FARBBAENDER[key] = reihe
    return reihe


def klinge(img, ox, oy, laenge, halb, ton, spitze=6.0, kruemmung=0.0,
           ricasso=2.5, rinne_bis=0.74, scharten=(), zaehne=(),
           glanz=(), marken=(), stumpf=True, scharte=0.55):
    """Klinge mit Hohlkehle, Ricasso und Scharten.

    ricasso   ungeschliffenes Stueck ueber der Parierstange - dort fehlt die
              helle Fase, das setzt die Klinge vom Heft ab
    rinne_bis wo die Hohlkehle endet (Anteil der Laenge). Eine Kehle, die bis
              in die Spitze laeuft, sieht aus wie ein Strich statt wie eine
              Nut
    scharten  u-Werte, an denen die Schneide eine Kerbe hat
    zaehne    (u, laenge) - Zacken am Klingenruecken
    """
    koerper = max(0.001, laenge - spitze)
    for y in range(img.height):
        for x in range(img.width):
            u, v = to_uv(x, y, ox, oy)
            if u < -0.001 or u > laenge:
                continue
            w = halb
            for su in scharten:
                if abs(u - su) < 0.7:
                    w -= scharte
            vv = v - kruemmung * (max(0.0, u) / laenge) ** 2
            # Spitze: bei der Vorlage einseitig abgeschraegt - die Schneide
            # laeuft zum Ruecken hoch, der Ruecken bleibt gerade. Eine
            # beidseitig zulaufende Spitze sieht daneben aus wie ein Dolch.
            if u > koerper and stumpf:
                untergrenze = -w + 2.0 * w * (u - koerper) / spitze
                if vv < untergrenze - 0.001:
                    continue
            elif u > koerper:
                w = halb * (laenge - u) / spitze
            if w <= 0.05:
                continue
            if not -w - 0.001 <= vv <= w + 0.001:
                continue

            vorn = (vv + w) * 2.0          # Pixel von der Schneide
            am_ricasso = u < ricasso
            hat_rinne = ricasso <= u <= laenge * rinne_bis and w > 0.6
            # Pixel quer ueber die Klinge: auf einer Bildzeile steigt vorn um
            # genau 1 pro Pixel; der Nachkommateil ist auf der Zeile konstant.
            # So trifft jedes Band genau eine Pixelreihe - keine doppelte Kante.
            breite = max(1, int(math.floor(4.0 * w - (vorn - math.floor(vorn)) + 1e-6)) + 1)
            reihe = farbbaender(ton, breite, hat_rinne, am_ricasso)
            if u > laenge - 1.2:
                col = ton['kante']
            else:
                col = reihe[min(len(reihe) - 1, max(0, int(vorn)))]
            put(img, x, y, C(col))

    # Kehlenende rund abschliessen, sonst franst die Nut aus
    if halb > 0.6:
        ende = laenge * rinne_bis
        for dv in (-0.5, 0.0, 0.5):
            speck(img, ox, oy, ende + 0.5, dv + kruemmung * (ende / laenge) ** 2,
                  ton['fase'])

    for gu in glanz:                       # Lichtblitze auf der Schneidenfase
        v = -halb + 0.6 + kruemmung * (gu / laenge) ** 2
        speck(img, ox, oy, gu, v, ton['glanz'])
        speck(img, ox, oy, gu + 0.5, v + 0.5, ton['hell'])
    for mu in marken:                      # dunkle Marken in der Hohlkehle
        speck(img, ox, oy, mu, kruemmung * (mu / laenge) ** 2, ton['kante'])

    for zu, zl in zaehne:                  # Zacken am Ruecken
        for i in range(zl):
            speck(img, ox, oy, zu + i * 0.4, halb + 0.5 + i * 0.5,
                  ton['ruecken'] if i else ton['mitte'])


def schlagschatten(img, ox, oy, ton, u_von, u_bis, halb):
    """Die Parierstange wirft Schatten auf den Klingenansatz: jedes Pixel
    dort wandert eine Stufe die Rampe hinab. Das setzt Heft und Klinge
    voneinander ab - ohne Schatten kleben sie flach aneinander."""
    reihe = [C(ton[n]) for n in ('glanz', 'hell', 'licht', 'mitte', 'fase',
                                 'ruecken', 'kante')]
    dunkler = {}
    for i, c in enumerate(reihe):
        dunkler.setdefault(c, reihe[min(i + 1, len(reihe) - 1)])
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            u, v = to_uv(x, y, ox, oy)
            if u_von <= u <= u_bis and abs(v) <= halb + 0.6 and px[x, y][3]:
                px[x, y] = dunkler.get(px[x, y], px[x, y])


def kante_ziehen(img, ox, oy, laenge, halb, ton, kruemmung=0.0):
    """Zieht die dunkle Materialkante am Ruecken nach - bei schmalen Klingen
    faellt sie sonst durch das Raster."""
    for i in range(int(laenge)):
        v = halb + kruemmung * (i / max(1.0, laenge)) ** 2
        speck(img, ox, oy, float(i), v, ton['ruecken'])


# --- Heft -------------------------------------------------------------------

def parier(img, ox, oy, u_c, dick, weite, hell, mitte, dunkel, kante,
           schwung=0.0):
    """Parierstange quer zur Klinge, mit eigener dunkler Kante."""
    for y in range(img.height):
        for x in range(img.width):
            u, v = to_uv(x, y, ox, oy)
            if abs(v) > weite:
                continue
            mitte_u = u_c + schwung * (abs(v) / weite) ** 2
            d = abs(u - mitte_u)
            if d > dick:
                continue
            if d > dick - 0.55 or abs(v) > weite - 0.55:
                col = kante
            else:
                # Die Stange ist ein Rundstab: Schattierung QUER zur Achse
                # (Flanke zur Klinge oben im Licht, Flanke zum Griff im
                # Schatten) macht sie rund. Ein Verlauf laengs der Stange
                # saehe aus wie ein flacher Streifen. Laengs nur eine
                # kleine Stufe: das Ende zum Licht heller.
                d_u = u - mitte_u
                stufe = 0 if d_u > dick * 0.2 else (1 if d_u > -dick * 0.25 else 2)
                if v < -weite * 0.45:
                    stufe -= 1
                elif v > weite * 0.45:
                    stufe += 1
                col = (hell, hell, mitte, dunkel, kante)[stufe + 1]
            put(img, x, y, C(col))


GRIFF_LEDER = ('leder_licht', 'leder_mitte', 'leder_dunkel', 'leder_tief')
GRIFF_STAHL = ('stahl_licht', 'stahl_mitte', 'stahl_dunkel', 'stahl_kante')
GRIFF_KNOCHEN = ('knochen_licht', 'knochen_mitte', 'knochen_dunkel',
                 'knochen_kante')


def griff(img, ox, oy, u_von, u_bis, halb, hell, mitte, dunkel, kante):
    """Griff mit Wicklung und dunkler Kante."""
    for y in range(img.height):
        for x in range(img.width):
            u, v = to_uv(x, y, ox, oy)
            if not (u_von <= u <= u_bis and abs(v) <= halb):
                continue
            # Kreuzwicklung: zwei schraege Baender, die sich ueberlagern -
            # dort, wo sie sich kreuzen, liegt der Riemen doppelt (hell)
            a_ = int(math.floor(u + 0.6 * v)) % 2 == 0
            b_ = int(math.floor(u - 0.6 * v + 1.0)) % 2 == 0
            if abs(v) > halb - 0.55:
                col = kante
            elif a_ and b_:
                col = hell
            elif a_ or b_:
                col = mitte if v < 0 else dunkel
            else:
                col = dunkel if v < 0 else kante
            put(img, x, y, C(col))


def knauf(img, ox, oy, u_c, rad, hell, mitte, dunkel, kante):
    """Knauf - radial schattiert, mit dunklem Saum."""
    cx, cy = ox + u_c, oy - u_c
    for y in range(img.height):
        for x in range(img.width):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            if d > rad:
                continue
            nx, ny = dx / rad, dy / rad
            nz = math.sqrt(max(0.0, 1.0 - nx * nx - ny * ny))
            h = nx * -0.5 + ny * -0.5 + nz * 0.71
            if d > rad - 0.8:
                col = kante
            elif h > 0.88:
                col = hell
            elif h > 0.55:
                col = mitte
            else:
                col = dunkel
            put(img, x, y, C(col))


def troddel(img, ox, oy, u_start, laenge):
    """Herabhaengender Riemen am Knauf - das Detail, das dem Knochenschwert
    seinen Charakter gibt."""
    x, y = to_xy(u_start, 0.6, ox, oy)
    toene = ('leder_licht', 'leder_mitte', 'leder_dunkel', 'leder_mitte',
             'leder_hell')
    for i in range(laenge):
        put(img, x - i // 2, y + i, C(toene[i % len(toene)]))
        if i % 3 == 0:
            put(img, x - i // 2 - 1, y + i, C('leder_tief'))


# --- Waffen -----------------------------------------------------------------

def w_greatsword_iron(img):
    """Eisen-Grossschwert. Schmales Heft, breite Klinge - das Verhaeltnis
    macht die Groesse lesbar. 48x46."""
    ox, oy = 13, 28
    klinge(img, ox, oy, 26.0, 3.6, STAHL, spitze=4.5, ricasso=2.6,
           rinne_bis=0.74, scharten=(9.0, 16.5),
           glanz=(6.0, 13.0, 19.0), marken=(5.0, 11.0, 17.0))
    parier(img, ox, oy, -1.3, 1.25, 3.4, 'stahl_licht', 'stahl_mitte',
           'stahl_fase', 'stahl_kante', schwung=1.1)
    for v in (-3.0, 3.0):                        # Nieten in der Parierstange
        speck(img, ox, oy, -1.2, v, 'gold')
    speck(img, ox, oy, 1.4, 0.0, 'gold')         # Klingennagel am Ricasso
    speck(img, ox, oy, 2.6, 0.0, 'gold_mitte')
    griff(img, ox, oy, -6.6, -2.8, 0.7, *GRIFF_LEDER)
    knauf(img, ox, oy, -7.6, 1.7, 'stahl_hell', 'stahl_mitte', 'stahl_dunkel',
          'stahl_kante')
    troddel(img, ox, oy, -8.2, 8)


def w_sword_iron(img):
    """Eisenschwert - Einhaender. 36x34."""
    ox, oy = 10, 21
    klinge(img, ox, oy, 18.0, 2.4, STAHL, spitze=3.5, ricasso=2.0,
           rinne_bis=0.72, scharten=(11.0,),
           glanz=(5.0, 10.5), marken=(4.0, 9.0))
    parier(img, ox, oy, -1.1, 1.05, 2.5, 'stahl_licht', 'stahl_mitte',
           'stahl_fase', 'stahl_kante', schwung=0.8)
    for v in (-2.1, 2.1):
        speck(img, ox, oy, -1.0, v, 'gold')
    speck(img, ox, oy, 1.2, 0.0, 'gold')
    griff(img, ox, oy, -5.0, -2.3, 0.62, *GRIFF_LEDER)
    knauf(img, ox, oy, -5.8, 1.45, 'stahl_hell', 'stahl_mitte', 'stahl_dunkel',
          'stahl_kante')


def w_dagger_iron(img):
    """Eisendolch - kurz, schmal, spitz. 26x24."""
    ox, oy = 7, 15
    klinge(img, ox, oy, 11.0, 1.6, STAHL, spitze=2.8, ricasso=1.4,
           rinne_bis=0.70, glanz=(4.0,), marken=(3.0, 6.0))
    parier(img, ox, oy, -0.9, 0.9, 1.8, 'stahl_licht', 'stahl_mitte',
           'stahl_fase', 'stahl_kante', schwung=0.5)
    speck(img, ox, oy, 0.9, 0.0, 'gold')
    griff(img, ox, oy, -3.6, -1.7, 0.55, *GRIFF_LEDER)
    knauf(img, ox, oy, -4.1, 1.1, 'stahl_hell', 'stahl_mitte', 'stahl_dunkel',
          'stahl_kante')


def w_sword_bone(img):
    """Knochenschwert - Einhaender aus demselben Material wie dein
    Grossschwert, mit Zaehnen am Ruecken. 36x34."""
    ox, oy = 10, 21
    klinge(img, ox, oy, 18.0, 2.4, KNOCHEN, spitze=3.5, ricasso=2.0,
           rinne_bis=0.70, scharten=(8.0, 13.0),
           glanz=(5.0, 11.0), marken=(4.0, 9.0),
           zaehne=((7.0, 2), (12.0, 2)))
    parier(img, ox, oy, -1.1, 1.05, 2.5, 'knochen_licht', 'knochen_mitte',
           'knochen_dunkel', 'knochen_kante', schwung=0.8)
    speck(img, ox, oy, 1.2, 0.0, 'gold')
    griff(img, ox, oy, -5.0, -2.3, 0.62, *GRIFF_STAHL)
    knauf(img, ox, oy, -5.8, 1.45, 'stahl_hell', 'stahl_mitte',
          'stahl_dunkel', 'stahl_kante')
    troddel(img, ox, oy, -6.4, 6)


def w_dagger_bone(img):
    """Knochendolch. 26x24."""
    ox, oy = 7, 15
    klinge(img, ox, oy, 11.0, 1.6, KNOCHEN, spitze=2.8, ricasso=1.4,
           rinne_bis=0.68, glanz=(4.0,), marken=(3.0, 6.0))
    parier(img, ox, oy, -0.9, 0.9, 1.8, 'knochen_licht', 'knochen_mitte',
           'knochen_dunkel', 'knochen_kante', schwung=0.5)
    griff(img, ox, oy, -3.6, -1.7, 0.55, *GRIFF_STAHL)
    knauf(img, ox, oy, -4.1, 1.1, 'stahl_hell', 'stahl_mitte',
          'stahl_dunkel', 'stahl_kante')


def w_greatsword_copper(img):
    """Kupfer-Grossschwert - waermere Rampe, sonst wie das eiserne. 48x46."""
    ox, oy = 13, 28
    klinge(img, ox, oy, 26.0, 3.6, KUPFER, spitze=4.5, ricasso=2.6,
           rinne_bis=0.74, scharten=(9.0, 16.5),
           glanz=(6.0, 13.0, 19.0), marken=(5.0, 11.0, 17.0))
    parier(img, ox, oy, -1.3, 1.25, 3.4, 'leder_licht', 'leder_mitte',
           'leder_dunkel', 'rost_dk', schwung=1.1)
    for v in (-3.0, 3.0):
        speck(img, ox, oy, -1.3, v, 'gold_hell')
    speck(img, ox, oy, 1.4, 0.0, 'gold')
    speck(img, ox, oy, 2.6, 0.0, 'gold_mitte')
    griff(img, ox, oy, -6.6, -2.8, 0.7, *GRIFF_STAHL)
    knauf(img, ox, oy, -7.6, 1.7, 'stahl_hell', 'stahl_mitte',
          'stahl_dunkel', 'stahl_kante')
    troddel(img, ox, oy, -8.2, 8)


# --- Waffenfamilien --------------------------------------------------------
# Die Vorlagen im Sprites-Ordner kommen in vier Stufen je Material:
#   1 Sword        16 px   2 Broadsword   23 px
#   3 Giant        29 px   4 Great        46 px
# Die Masse je Stufe stehen hier; die Bauart je Familie in generate_families.py.

STUFEN = (
    # laenge, halb, spitze, ricasso, (parier dick, weite), griff_len, knauf, leinwand
    (9.0, 1.2, 2.2, 1.0, (0.6, 1.6), 2.6, 0.9, 20),
    (13.0, 1.45, 3.0, 1.6, (0.8, 2.3), 3.4, 1.1, 28),
    (18.0, 1.75, 3.8, 2.2, (1.0, 2.6), 4.2, 1.4, 34),
    (29.0, 3.9, 4.8, 2.8, (1.3, 3.6), 6.4, 1.8, 52),
)


def feuer_deko(img, ox, oy, laenge, halb, stufe):
    """Feuer entlang der Schneide wie bei OiledCoalSword/Sprite-0001.

    Dort ist die Flamme so breit wie die Klinge selbst - 4-5 px - mit
    hohen Zungen, die zur Spitze lehnen. Toene von der Klinge nach aussen:
    gelb (am heissesten), orange, rotorange, rot, dunkelroter Saum.
    """
    grund = 2.0 + 0.9 * stufe
    ricasso = STUFEN[stufe - 1][3]

    def tiefe(u):
        t = grund + 0.6 * math.sin(u * 1.3 + 0.3)
        zunge = math.sin(u * 0.62 + 0.9)          # alle ~10 px eine Zunge
        if zunge > 0.3:
            t += (1.2 + 0.5 * stufe) * (zunge - 0.3) / 0.7
        return max(2.0, t)

    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            if px[x, y][3]:
                continue
            u, v = to_uv(x, y, ox, oy)
            if not ricasso + 0.5 <= u <= laenge - 1.0:
                continue
            d = (-halb - v) * 2.0        # Pixel von der Schneide nach aussen
            if d < 0.5:
                continue
            t = tiefe(u + 0.45 * d)      # Versatz: Zungen lehnen nach vorn
            # zur Spitze hin laeuft das Feuer aus
            t *= min(1.0, (laenge - u) / 3.0)
            if d > t:
                continue
            if d > t - 1.0:
                name = 'feuer_dk'
            elif d < 1.5:
                name = 'gold'
            elif d < 2.5:
                name = 'gold_mitte'
            elif d < 4.0:
                name = 'gold_dunkel'
            elif d < 5.5:
                name = 'kupfer'
            else:
                name = 'feuer_rot'
            put(img, x, y, C(name))


def gift_deko(img, ox, oy, laenge, halb, stufe):
    """Giftblasen auf der Klinge: 3x3-Pusteln mit Licht oben links und
    Schatten unten rechts, versetzt entlang der Klinge. Jede Farbgruppe
    bleibt bei drei Pixeln, die Blase ist trotzdem rund schattiert."""
    muster = (('gift_glanz', 'gift_glanz', 'gift_hell'),
              ('gift_glanz', 'gift_hell', 'gift_dk'),
              ('gift_hell', 'gift_dk', 'gift_dk'))
    ricasso = STUFEN[stufe - 1][3]
    px = img.load()
    schritt = 4.0 if stufe >= 3 else 3.0
    u = ricasso + 2.0
    k = 0
    while u < laenge - 3.0:
        v = (-0.35, 0.3, 0.0)[k % 3] * halb
        cx, cy = to_xy(u, v, ox, oy)
        if all(px[cx + dx, cy + dy][3] for dx in (-1, 0, 1) for dy in (-1, 0, 1)
               if 0 <= cx + dx < img.width and 0 <= cy + dy < img.height):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    put(img, cx + dx, cy + dy, C(muster[dy + 1][dx + 1]))
        u += schritt
        k += 1


GRIFF_KOHLE = ('stahl_tief', 'stahl_kante', 'tiefschwarz', 'schwarz')

EISEN_TON = {'kante': 'stahl_kante', 'glanz': 'stahl_hell',
             'hell': 'stahl_licht', 'fase': 'stahl_dunkel',
             'mitte': 'stahl_fase', 'licht': 'stahl_mitte',
             'rinne': 'stahl_kante', 'ruecken': 'stahl_tief'}
# Wie SlimeSword: ein Kern aus anderem Material in einem Stahlrahmen - nur
# Kante, Schneidenglanz und Ruecken bleiben Stahl, der Rest ist das Gift.
# Reisszahn aus Gift: eine Rampe von Nacht ueber Lila zu Rosa - wie beim
# SlimeSword ist das Material die Klinge, nicht ein Anstrich.
GIFT = {'kante': 'gift_dk', 'glanz': 'gift_schaum',
        'hell': 'gift_glanz', 'fase': 'gift_dk',
        'mitte': 'gift', 'licht': 'gift_hell',
        'rinne': 'gift_dk', 'ruecken': 'gift'}
KRISTALL = {'kante': 'kristall_tief', 'glanz': 'weiss',
            'hell': 'kristall_hell', 'fase': 'kristall_dunkel',
            'mitte': 'kristall_mitte', 'licht': 'kristall_licht',
            'rinne': 'kristall_tief', 'ruecken': 'kristall_dunkel'}

# Die vier Stufen je Familie baut tools/generate_families.py.


WAFFEN = [
    ('greatsword_iron', 'Eisen-Grossschwert', w_greatsword_iron, 48, 46),
    ('greatsword_copper', 'Kupfer-Grossschwert', w_greatsword_copper, 48, 46),
    ('sword_bone', 'Knochenschwert', w_sword_bone, 36, 34),
    ('dagger_bone', 'Knochendolch', w_dagger_bone, 26, 24),
    ('sword_iron', 'Eisenschwert', w_sword_iron, 36, 34),
    ('dagger_iron', 'Eisendolch', w_dagger_iron, 26, 24),
]


def zuschneiden(img):
    kasten = img.getbbox()
    if not kasten:
        return img
    inhalt = img.crop(kasten)
    eng = Image.new('RGBA', (inhalt.width + 2, inhalt.height + 2), (0, 0, 0, 0))
    eng.paste(inhalt, (1, 1))
    return eng


def pruefen(img):
    daten = list(img.getdata())
    voll = [p for p in daten if p[3]]
    mangel = []
    if any(0 < p[3] < 255 for p in daten):
        mangel.append('Teiltransparenz')
    if {p[:3] for p in voll} - PALETTE_RGB:
        mangel.append('Farbe ausserhalb AAP-64')
    satz = flaechen_bericht(img)
    if satz:
        mangel.append(satz)
    if len({p[:3] for p in voll}) < 8:
        mangel.append('nur %d Farben' % len({p[:3] for p in voll}))
    return mangel


def bogen(bilder, scale=6):
    zelle = max(max(b.size) for b in bilder) + 2
    blatt = Image.new('RGBA', (len(bilder) * zelle * scale, zelle * scale),
                      (36, 34, 52, 255))
    for i, b in enumerate(bilder):
        gross = b.resize((b.width * scale, b.height * scale), Image.NEAREST)
        blatt.alpha_composite(gross, (i * zelle * scale +
                                      (zelle * scale - gross.width) // 2,
                                      (zelle * scale - gross.height) // 2))
    return blatt


def main():
    wurzel = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(wurzel / 'assets' / 'sprites' / 'weapons'))
    ap.add_argument('--sheet', action='store_true')
    args = ap.parse_args()

    aus = Path(args.out)
    aus.mkdir(parents=True, exist_ok=True)

    gemacht = []
    beanstandet = []
    for wid, name, fn, bx, by in WAFFEN:
        img = blank(bx, by)
        fn(img)
        img = zuschneiden(img)
        entflechten(img)        # hoechstens 3 gleiche Pixel zusammenhaengend
        for satz in pruefen(img):
            beanstandet.append((wid, satz))
        img.save(aus / ('%s.png' % wid))
        gemacht.append(img)
        farben = len({p[:3] for p in img.getdata() if p[3]})
        print('  %-20s %-22s %2dx%-2d %2d Farben'
              % (wid + '.png', name, img.width, img.height, farben))

    if args.sheet:
        bogen(gemacht).save(aus / '_aap_sheet.png')

    print('\nFertig: %d Sprites in %s' % (len(gemacht), aus))
    if beanstandet:
        print('Beanstandungen:')
        for wid, satz in beanstandet:
            print('  %-20s %s' % (wid, satz))
    else:
        print('Pruefung: alles sauber')


if __name__ == '__main__':
    main()
