#!/usr/bin/env python3
"""Waffenfamilien in vier Stufen - jede Familie mit eigener Form.

Vorbild sind Sprites/Weapons/BoneSword und SlimeSword: dort ist ein Material
kein Anstrich, sondern bestimmt die Bauart. Das Schleimschwert hat in Stufe 2
eine Knolle, in Stufe 3 ein Blatt voller Blasen, in Stufe 4 eine Stahlklinge
mit Schleimheft. Darum baut hier jede Familie ihre Stufen selbst:

    IronSword     schwer und grob: gerade Stange, Klotzknauf, Nieten, Scharten
    SteelSword    ritterlich: schmale Spitzklinge, geschwungene Stange mit
                  Rubin, Radknauf, Golddraht
    CrystalSword  Kristall: Zacken am Ruecken, Splitter statt Parierstange,
                  Kristallbueschel als Knauf, Facetten quer
    EmberSword    nach OiledCoalSword: geoelter dunkler Stahl, Feuer entlang
                  der Schneide, Lava in der Kehle, Glutkugel als Knauf
    VenomSword    Reisszahn-Klinge mit Kruemmung, Giftkern mit Blasen, Tropfen
                  am Ruecken, zwei Knochenzaehne als Parier, Giftblase als Knauf

Alle Waffen halten die 3-Pixel-Regel und haengen aus einem Stueck.

    python tools/generate_families.py --out C:/Users/maxst/Desktop/Sprites/claude/Weapons
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from generate_weapons_aap import (
    AAP, C, EISEN_TON, GIFT, GRIFF_KOHLE, GRIFF_LEDER, GRIFF_STAHL, KRISTALL,
    STAHL, STUFEN, blank, feuer_deko, gift_deko, griff, klinge, knauf, parier,
    pruefen, put, schlagschatten, speck, to_uv, to_xy, troddel, zuschneiden,
)
from pixelregeln import entflechten
from palette import duel_anpassen


LICHT = (-0.707, -0.707)        # Licht von oben links, wie bei allen Waffen


def _lit(nx, ny):
    return nx * LICHT[0] + ny * LICHT[1]


# --- Bausteine in Bildkoordinaten -------------------------------------------
# Die Klinge lebt im u/v-Raster der Diagonale. Alles, was in andere
# Richtungen zeigt (Splitter, Zaehne, Kugeln), wird direkt in x/y gesetzt.

def keil(img, cx, cy, dx, dy, laenge, breite, toene, kruemmung=0.0,
         spitz=True):
    """Zulaufender Keil von (cx, cy) in Richtung (dx, dy).

    kruemmung biegt die Spitze seitwaerts (positiv = im Uhrzeigersinn).
    Schattiert nach Weltlicht: die Seite, deren Normale nach oben links
    zeigt, ist hell.
    """
    hell, mitte, dunkel, kante = toene
    n = math.hypot(dx, dy)
    dx, dy = dx / n, dy / n
    nx, ny = -dy, dx
    r = int(laenge + breite + 3)
    for y in range(int(cy) - r, int(cy) + r + 1):
        for x in range(int(cx) - r, int(cx) + r + 1):
            px, py = x - cx, y - cy
            t = px * dx + py * dy
            s = px * nx + py * ny
            if t < -0.5 or t > laenge:
                continue
            versatz = kruemmung * (max(t, 0.0) / laenge) ** 2
            hw = breite * (1.0 - t / laenge) if spitz else breite
            s -= versatz
            if abs(s) > hw + 0.3:
                continue
            if hw - abs(s) < 0.75 or t > laenge - 1.0:
                col = kante
            else:
                seite = _lit(nx * s, ny * s) if abs(s) > 0.4 else 0.0
                col = hell if seite > 0.25 else (dunkel if seite < -0.25 else mitte)
            put(img, x, y, C(col))


def raute(img, cx, cy, dx, dy, laenge, breite, toene):
    """Kristallsplitter: Raute entlang (dx, dy), zwei Facetten und Mittelgrat."""
    hell, mitte, dunkel, kante = toene
    n = math.hypot(dx, dy)
    dx, dy = dx / n, dy / n
    nx, ny = -dy, dx
    r = int(laenge + breite + 3)
    for y in range(int(cy) - r, int(cy) + r + 1):
        for x in range(int(cx) - r, int(cx) + r + 1):
            px, py = x - cx, y - cy
            t = px * dx + py * dy
            s = px * nx + py * ny
            if t < -0.3 or t > laenge:
                continue
            hw = breite * (1.0 - abs(t - laenge / 2.0) / (laenge / 2.0))
            if abs(s) > hw + 0.3:
                continue
            if hw - abs(s) < 0.7:
                col = kante
            elif abs(s) < 0.45:
                col = hell                     # Grat faengt Licht
            else:
                col = hell if _lit(nx * s, ny * s) > 0 else dunkel
                if col == 'hell' and abs(s) > hw * 0.6:
                    col = mitte
            put(img, x, y, C(col))


def kugel(img, cx, cy, rad, toene, glanz=None):
    """Kugel, radial schattiert; optional ein Glanzpunkt oben links."""
    hell, mitte, dunkel, kante = toene
    for y in range(int(cy - rad) - 1, int(cy + rad) + 2):
        for x in range(int(cx - rad) - 1, int(cx + rad) + 2):
            ddx, ddy = x - cx, y - cy
            d = math.hypot(ddx, ddy)
            if d > rad:
                continue
            nx, ny = ddx / rad, ddy / rad
            nz = math.sqrt(max(0.0, 1.0 - nx * nx - ny * ny))
            h = _lit(nx, ny) + nz * 0.71
            # Saum nur auf der Schattenseite - eine kleine Kugel mit Saum
            # rundum ist nur ein dunkler Klecks
            if d > rad - 0.8 and not (h > 0.55 and rad < 2.6):
                col = kante
            elif h > 0.88:
                col = hell
            elif h > 0.5:
                col = mitte
            else:
                col = dunkel
            put(img, x, y, C(col))
    if glanz and rad >= 1.8:
        put(img, int(round(cx - rad * 0.4)), int(round(cy - rad * 0.4)), C(glanz))


def block(img, ox, oy, u_c, halb_u, halb_v, toene):
    """Klotz im u/v-Raster - der Knauf einer groben Waffe."""
    hell, mitte, dunkel, kante = toene
    for y in range(img.height):
        for x in range(img.width):
            u, v = to_uv(x, y, ox, oy)
            if abs(u - u_c) > halb_u or abs(v) > halb_v:
                continue
            if halb_u - abs(u - u_c) < 0.55 or halb_v - abs(v) < 0.55:
                col = kante
            elif v < -halb_v * 0.3:
                col = hell
            elif v < halb_v * 0.3:
                col = mitte
            else:
                col = dunkel
            put(img, x, y, C(col))


def tropfen(img, x, y, toene):
    """Haengender Tropfen, 3 breit, 5 hoch, Spitze oben an (x, y)."""
    hell, mitte, dunkel, kante = toene
    form = ((0, 0, mitte), (0, 1, mitte),
            (-1, 2, hell), (0, 2, mitte), (1, 2, dunkel),
            (-1, 3, mitte), (0, 3, dunkel), (1, 3, dunkel),
            (0, 4, kante))
    for dx, dy, col in form:
        put(img, x + dx, y + dy, C(col))
    put(img, x - 1, y + 2, C(hell))


def nieten(img, ox, oy, punkte, col='stahl_kante', licht='stahl_licht'):
    for u, v in punkte:
        speck(img, ox, oy, u, v, col)
        speck(img, ox, oy, u + 0.5, v - 0.5, licht)


def inseln(img):
    """Zusammenhaengende Teile (8er-Nachbarschaft) - eine Waffe ist eins."""
    px = img.load()
    w, h = img.size
    gesehen = set()
    n = 0
    for y in range(h):
        for x in range(w):
            if (x, y) in gesehen or not px[x, y][3]:
                continue
            n += 1
            stapel = [(x, y)]
            gesehen.add((x, y))
            while stapel:
                cx, cy = stapel.pop()
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = cx + dx, cy + dy
                        if (0 <= nx < w and 0 <= ny < h and (nx, ny) not in gesehen
                                and px[nx, ny][3]):
                            gesehen.add((nx, ny))
                            stapel.append((nx, ny))
    return n


# --- Toene --------------------------------------------------------------------

EISEN_BESCHLAG = ('stahl_licht', 'stahl_mitte', 'stahl_dunkel', 'stahl_kante')
GOLD_BESCHLAG = ('gold', 'gold_mitte', 'gold_dunkel', 'rost_dk')
RUBIN = ('rubin_hell', 'kupfer', 'feuer_rot', 'feuer_dk')
EISEN_DUNKEL = ('stahl_mitte', 'stahl_dunkel', 'stahl_tief', 'stahl_kante')
KRISTALL_TON = ('kristall_hell', 'kristall_licht', 'kristall_mitte', 'kristall_tief')
GLUT = ('gold', 'gold_dunkel', 'feuer_rot', 'feuer_dk')
KOHLE_BESCHLAG = ('stahl_dunkel', 'stahl_tief', 'stahl_kante', 'tiefschwarz')
GIFT_TON = ('gift_hell', 'gift', 'gift_dk', 'stahl_kante')
KNOCHEN_TON = ('creme', 'knochen_mitte', 'knochen_fase', 'knochen_kante')
GRIFF_GIFT = ('gift_hell', 'gift', 'gift_dk', 'stahl_kante')
GRIFF_DUNKELLEDER = ('leder_mitte', 'leder_dunkel', 'leder_tief', 'rost_dk')

# Geoelter Stahl wie beim OiledCoalSword: fast alles dunkel, ein Glanz.
OEL = {'kante': 'stahl_kante', 'glanz': 'stahl_licht', 'hell': 'stahl_mitte',
       'fase': 'stahl_tief', 'mitte': 'stahl_dunkel', 'licht': 'stahl_fase',
       'rinne': 'gold_dunkel', 'ruecken': 'stahl_kante'}


# Die Stufen muessen nicht proportional wachsen. Das Schleimschwert der
# Vorlage ist in Stufe 2 eine Knolle und in Stufe 4 schlank - die Form darf
# je Stufe kippen. Je Familie: Stufe -> (Laengenfaktor, Breitenfaktor).
PROPORTION = {
    'iron': {1: (0.95, 1.35), 2: (1.0, 1.2)},              # frueh klobig
    'steel': {1: (1.05, 1.0), 3: (1.08, 0.9), 4: (1.05, 0.72)},   # spaet schlank
    'crystal': {2: (0.9, 1.4), 4: (1.0, 1.1)},              # Stufe 2 ein Brocken
    'ember': {3: (0.95, 1.2), 4: (0.9, 1.4)},               # Hackmesser
    'venom': {1: (0.95, 1.3), 4: (1.05, 0.78)},             # Zahn wird zur Nadel
    'thorn': {3: (0.95, 1.3), 4: (1.0, 1.15)},              # Knueppel
    'obsidian': {2: (1.0, 1.3), 4: (1.05, 0.72)},           # Splitter wird Nadel
    'holy': {4: (1.05, 0.8)},
    'scrap': {2: (0.9, 1.45), 4: (0.95, 1.2)},              # Stufe 2 ein Hackbeil
    'frost': {2: (0.95, 1.3), 4: (1.05, 0.85)},
    'storm': {1: (1.1, 0.9), 4: (1.08, 0.8)},
    'shadow': {3: (1.0, 0.85), 4: (1.05, 0.75)},           # wird zur Sichel
    'royal': {4: (1.05, 0.85)},
    'axe': {}, 'spear': {},
    'rune': {1: (0.95, 1.3), 4: (0.95, 1.15)},
    'coral': {2: (0.95, 1.3)}, 'dragon': {4: (1.05, 0.85)},
}


def masse(stufe, familie=None):
    laenge, halb, spitze, ricasso, (pd, pw), glen, knauf_r, _ = STUFEN[stufe - 1]
    fl, fb = PROPORTION.get(familie, {}).get(stufe, (1.0, 1.0))
    return dict(laenge=laenge * fl, halb=halb * fb, spitze=spitze * fl,
                ricasso=ricasso, pd=pd, pw=pw, glen=glen, knauf=knauf_r)


def ursprung(img, laenge, stufe=None):
    """Klingenansatz so legen, dass das ganze Heft in die Leinwand passt."""
    if stufe is None:
        return (int(round(4 + laenge * 0.18)),
                int(round(img.height - 6 - laenge * 0.22)))
    m = masse(stufe)
    heft = m['pd'] * 1.1 + m['glen'] * 1.4 + m['knauf'] * 3.5 + 3.0
    return (int(round(2 + heft)), int(round(img.height - 4 - heft)))


# --- Familien -----------------------------------------------------------------

def iron(img, stufe):
    """Grob und schwer: breitere Klinge, gerade Stange, Klotzknauf."""
    m = masse(stufe, 'iron')
    L, halb = m['laenge'], m['halb'] * 1.05
    ox, oy = ursprung(img, L, stufe)
    scharten = {1: (), 2: (), 3: (L * 0.55,), 4: (L * 0.35, L * 0.65)}[stufe]
    klinge(img, ox, oy, L, halb, EISEN_TON, spitze=m['spitze'] * 0.8,
           ricasso=m['ricasso'] * 1.3, rinne_bis=0.7, scharten=scharten,
           glanz=(L * 0.45,), marken=(L * 0.3, L * 0.55) if stufe >= 3 else ())
    pd, pw = m['pd'] * 1.3, m['pw'] * 1.5
    schlagschatten(img, ox, oy, EISEN_TON, 0.0, 1.2 + 0.3 * stufe, halb)
    parier(img, ox, oy, -pd * 1.1, pd, pw, *EISEN_DUNKEL, schwung=0.0)
    if stufe >= 2:
        nieten(img, ox, oy, ((-pd * 1.1, -pw * 0.7), (-pd * 1.1, pw * 0.7)))
    if stufe >= 3:                                # Nieten am Ricasso
        nieten(img, ox, oy, ((m['ricasso'] * 0.6, -halb * 0.5),
                             (m['ricasso'] * 0.6, halb * 0.5)))
    glen = m['glen'] * 1.25
    griff(img, ox, oy, -(pd * 1.1 + glen + 0.4), -(pd * 1.1 + 0.9),
          0.45 + stufe * 0.07, *GRIFF_LEDER)
    kn = m['knauf']
    ende = -(pd * 1.1 + glen + 0.4)
    block(img, ox, oy, ende - kn * 0.7, kn * 0.75 + 0.2, kn * 1.1 + 0.4,
          EISEN_DUNKEL)
    if stufe >= 2:
        troddel(img, ox, oy, ende - kn * 0.7, 2 + stufe * 2)
    return ox, oy, L, halb, EISEN_TON


def steel(img, stufe):
    """Ritterlich: schmale lange Spitzklinge, Schwung, Rubin, Radknauf."""
    m = masse(stufe, 'steel')
    L, halb = m['laenge'] * 1.08, m['halb'] * 0.85
    ox, oy = ursprung(img, L, stufe)
    ox += 1
    glanz = (L * 0.35, L * 0.7) if stufe < 3 else (L * 0.25, L * 0.5, L * 0.75)
    klinge(img, ox, oy, L, halb, STAHL, spitze=m['spitze'] * 1.4,
           ricasso=m['ricasso'], rinne_bis=0.8, glanz=glanz,
           marken=tuple(L * f for f in (0.2, 0.4, 0.6)) if stufe >= 2 else (),
           stumpf=False)
    if stufe >= 3:                                # Goldeinlage am Ricasso
        for i in range(int(m['ricasso'])):
            speck(img, ox, oy, 0.6 + i, 0.0, 'gold_mitte')
    pd, pw = m['pd'] * 0.85, m['pw'] * (1.5 if stufe < 3 else 1.7)
    schlagschatten(img, ox, oy, STAHL, 0.0, 1.0 + 0.3 * stufe, halb)
    parier(img, ox, oy, -pd * 1.1, pd, pw, *GOLD_BESCHLAG, schwung=0.45 * stufe)
    # Rubin im Stangenkreuz, Kugelenden an der Stange
    cx, cy = to_xy(-pd * 1.1, 0.0, ox, oy)
    if stufe >= 2:
        kugel(img, cx, cy, 1.0 + stufe * 0.3, RUBIN, glanz='creme' if stufe >= 3 else None)
    else:
        put(img, cx, cy, C('feuer_rot'))
    for s in (-1, 1):
        ex, ey = to_xy(-pd * 1.1 + 0.45 * stufe, s * pw, ox, oy)
        kugel(img, ex, ey, 0.9 + stufe * 0.25, GOLD_BESCHLAG)
    glen = m['glen'] * 1.25
    griff(img, ox, oy, -(pd * 1.1 + glen + 0.4), -(pd * 1.1 + 0.9),
          0.42 + stufe * 0.06, *GRIFF_DUNKELLEDER)
    for i in range(1, int(glen), 2):               # Golddraht
        speck(img, ox, oy, -(pd * 1.1 + 0.9 + i), -0.2, 'gold')
    kn = m['knauf'] * 1.15
    kx, ky = to_xy(-(pd * 1.1 + glen + 0.4) - kn * 0.6, 0.0, ox, oy)
    kugel(img, kx, ky, kn, GOLD_BESCHLAG, glanz='gold_hell')
    if stufe >= 3:
        put(img, kx, ky, C('feuer_rot'))
    return ox, oy, L, halb, STAHL


def crystal(img, stufe):
    """Kristall: Zacken am Ruecken, Splitter als Parier, Bueschel als Knauf."""
    m = masse(stufe, 'crystal')
    L, halb = m['laenge'], m['halb'] * 1.05
    ox, oy = ursprung(img, L, stufe)
    zacken = {1: ((0.55, 3.0),), 2: ((0.4, 3.5), (0.7, 4.0)),
              3: ((0.3, 4.5), (0.55, 6.0), (0.78, 4.0)),
              4: ((0.28, 6.0), (0.5, 8.0), (0.7, 7.0), (0.86, 4.0))}[stufe]
    klinge(img, ox, oy, L, halb, KRISTALL, spitze=m['spitze'] * 1.3,
           ricasso=m['ricasso'] * 0.7, rinne_bis=0.7,
           glanz=(L * 0.3, L * 0.65), stumpf=False)
    # Funkeln auf der Flaeche - ein weisser Punkt mit hellem Nachbarn
    if stufe >= 2:
        for i in range(int(m['ricasso']) + 3, int(L) - 3, 6):
            speck(img, ox, oy, float(i), -halb * 0.3, 'weiss')
            speck(img, ox, oy, i + 0.5, -halb * 0.3 + 0.5, 'kristall_hell')
    # Zacken am Ruecken: Splitter, die aus der Klinge wachsen und zur
    # Spitze lehnen. Sie beginnen 1 px in der Klinge, damit sie anhaengen.
    for f, zl in zacken:
        u = min(L * f, L - m['spitze'] * 1.3 - 1.0)   # nicht in die Spitze, sonst lose
        zx, zy = to_xy(u, halb - 0.6, ox, oy)
        raute(img, zx, zy, 1.7, 0.5, zl * 1.2, 0.7 + stufe * 0.2, KRISTALL_TON)
    # Parier: zwei Splitter, nach aussen und leicht zur Klinge geneigt
    pd = m['pd']
    schlagschatten(img, ox, oy, KRISTALL, 0.0, 0.8 + 0.3 * stufe, halb)
    cx, cy = to_xy(-pd * 0.6, 0.0, ox, oy)
    sl = 2.5 + stufe * 1.3
    sb = 0.9 + stufe * 0.25
    raute(img, cx, cy, -1.0, -0.55, sl, sb, KRISTALL_TON)
    raute(img, cx, cy, 0.55, 1.0, sl, sb, KRISTALL_TON)
    kugel(img, cx, cy, 0.8 + stufe * 0.2, EISEN_BESCHLAG)
    glen = m['glen']
    griff(img, ox, oy, -(pd * 1.1 + glen + 0.4), -(pd * 1.1 + 0.6),
          0.45 + stufe * 0.07, *GRIFF_STAHL)
    # Knauf: Bueschel aus drei Splittern
    kx, ky = to_xy(-(pd * 1.1 + glen + 0.8), 0.0, ox, oy)
    kl = 2.5 + stufe * 1.0
    raute(img, kx, ky, -1.0, 1.0, kl, 0.8 + stufe * 0.25, KRISTALL_TON)
    if stufe >= 2:
        raute(img, kx, ky, -1.0, 0.2, kl * 0.6, 0.6 + stufe * 0.15, KRISTALL_TON)
        raute(img, kx, ky, -0.2, 1.0, kl * 0.6, 0.6 + stufe * 0.15, KRISTALL_TON)
    kugel(img, kx, ky, 0.7 + stufe * 0.2, EISEN_BESCHLAG)
    return ox, oy, L, halb, KRISTALL


def ember(img, stufe):
    """Nach OiledCoalSword: dunkler Stahl, Feuer an der Schneide, Glutknauf."""
    m = masse(stufe, 'ember')
    L, halb = m['laenge'], m['halb'] * (1.0 if stufe < 3 else 1.15)
    ox, oy = ursprung(img, L, stufe)
    oy -= 1 + stufe
    klinge(img, ox, oy, L, halb, OEL, spitze=m['spitze'] * 0.9,
           ricasso=m['ricasso'], rinne_bis=0.72,
           scharten=(L * 0.6,) if stufe >= 3 else (),
           glanz=(L * 0.5,), marken=tuple(L * f for f in (0.25, 0.4, 0.55)))
    if stufe >= 2:                                 # Lava-Adern in der Kehle
        for i in range(int(m['ricasso']) + 1, int(L * 0.7), 2):
            speck(img, ox, oy, float(i), 0.0, 'gold_mitte' if i % 4 else 'gold')
    feuer_deko(img, ox, oy, L, halb, stufe)
    pd, pw = m['pd'] * 1.05, m['pw']
    schlagschatten(img, ox, oy, OEL, 0.0, 1.0 + 0.3 * stufe, halb)
    parier(img, ox, oy, -pd * 1.1, pd, pw * 1.3, *EISEN_BESCHLAG, schwung=0.15 * stufe)
    for k in range(-1, 2):                         # Glutrisse in der Stange
        if abs(k) <= stufe // 2 or k == 0:
            speck(img, ox, oy, -pd * 1.1 + k * 0.3, pw * 0.45 * k, 'gold_dunkel')
            speck(img, ox, oy, -pd * 1.1 - k * 0.3, pw * 0.45 * k + 0.5, 'kupfer')
    glen = m['glen'] * 1.4
    griff(img, ox, oy, -(pd * 1.1 + glen + 0.4), -(pd * 1.1 + 0.9),
          0.45 + stufe * 0.07, *GRIFF_KOHLE)
    if stufe >= 3:                                 # Glut zwischen den Wicklungen
        for i in range(1, int(glen), 2):
            speck(img, ox, oy, -(pd * 1.1 + 0.9 + i), 0.0, 'gold_dunkel')
    kn = m['knauf'] * 1.3
    kx, ky = to_xy(-(pd * 1.1 + glen + 0.4) - kn * 0.6, 0.0, ox, oy)
    kugel(img, kx, ky, kn, GLUT, glanz='gold_hell')
    return ox, oy, L, halb, OEL


def venom(img, stufe):
    """Reisszahn: gekruemmte Klinge, Giftkern, Tropfen, Knochenzaehne."""
    m = masse(stufe, 'venom')
    L, halb = m['laenge'], m['halb']
    ox, oy = ursprung(img, L, stufe)
    ox -= 1
    kr = 0.6 + stufe * 0.55
    scharten = (L * 0.45, L * 0.68) if stufe >= 3 else ()
    klinge(img, ox, oy, L, halb, GIFT, spitze=m['spitze'] * 1.5, kruemmung=kr,
           ricasso=m['ricasso'] * 0.8, rinne_bis=0.75, scharten=scharten,
           glanz=(L * 0.4, L * 0.7), stumpf=False)
    gift_deko(img, ox, oy, L, halb, stufe)
    # Tropfen haengen am Ruecken (der zeigt nach unten rechts)
    for f in ((0.4,), (0.35, 0.65), (0.3, 0.55, 0.8), (0.25, 0.5, 0.75))[stufe - 1]:
        u = L * f
        v = halb + kr * (u / L) ** 2 - 0.2
        x, y = to_xy(u, v, ox, oy)
        tropfen(img, x, y + 1, GIFT_TON)
    # Parier: zwei Knochenzaehne, nach aussen und zur Klinge gebogen
    pd = m['pd']
    schlagschatten(img, ox, oy, GIFT, 0.0, 0.8 + 0.3 * stufe, halb)
    cx, cy = to_xy(-pd * 0.7, 0.0, ox, oy)
    zl = 2.5 + stufe * 1.4
    zb = 0.8 + stufe * 0.3
    keil(img, cx, cy, -1.0, -0.6, zl, zb, KNOCHEN_TON, kruemmung=1.2)
    keil(img, cx, cy, 0.6, 1.0, zl, zb, KNOCHEN_TON, kruemmung=-1.2)
    block(img, ox, oy, -pd * 0.7, 0.6 + stufe * 0.15, 1.0 + stufe * 0.25, KNOCHEN_TON)
    glen = m['glen']
    griff(img, ox, oy, -(pd * 1.1 + glen + 0.4), -(pd * 1.1 + 0.6),
          0.45 + stufe * 0.07, *GRIFF_GIFT)
    kn = m['knauf'] * 1.2
    kx, ky = to_xy(-(pd * 1.1 + glen + 0.4) - kn * 0.6, 0.0, ox, oy)
    kugel(img, kx, ky, kn, GIFT_TON, glanz='gift_hell')
    if stufe >= 3:
        tropfen(img, kx, ky + int(kn) - 1, GIFT_TON)
    return ox, oy, L, halb, GIFT


def ring(img, cx, cy, rad, dicke, toene, glanz=None):
    """Ring (Heiligenschein, Radknauf): Torus, radial schattiert."""
    hell, mitte, dunkel, kante = toene
    for y in range(int(cy - rad) - 1, int(cy + rad) + 2):
        for x in range(int(cx - rad) - 1, int(cx + rad) + 2):
            ddx, ddy = x - cx, y - cy
            d = math.hypot(ddx, ddy)
            if d > rad or d < rad - dicke:
                continue
            nx, ny = ddx / rad, ddy / rad
            h = _lit(nx, ny)
            if d > rad - 0.7 or d < rad - dicke + 0.7:
                col = kante if h < 0.3 else mitte
            elif h > 0.4:
                col = hell
            elif h > -0.3:
                col = mitte
            else:
                col = dunkel
            put(img, x, y, C(col))
    if glanz:
        put(img, int(round(cx - rad * 0.7)), int(round(cy - rad * 0.7)), C(glanz))


def flecken(img, ox, oy, stellen, toene):
    """Rostflecken: 3x3 mit hellem Kern und dunklem Rand, versetzt."""
    hell, mitte, dunkel = toene
    muster = ((None, dunkel, dunkel), (dunkel, mitte, hell), (None, mitte, dunkel))
    for u, v in stellen:
        cx, cy = to_xy(u, v, ox, oy)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                col = muster[dy + 1][dx + 1]
                if col:
                    put(img, cx + dx, cy + dy, C(col))


# --- Toene der neuen Familien -----------------------------------------------

HOLZ = {'kante': 'leder_tief', 'glanz': 'leder_hell', 'hell': 'leder_licht',
        'fase': 'leder_dunkel', 'mitte': 'leder_mitte', 'licht': 'leder_licht',
        'rinne': 'leder_tief', 'ruecken': 'leder_dunkel'}
BLATT_TON = ('gruen_hell', 'gruen', 'gruen_dk', 'gruen_tief')
DORN_TON = ('creme', 'knochen_mitte', 'leder_dunkel', 'leder_tief')
GRIFF_RANKE = ('gruen', 'leder_mitte', 'leder_dunkel', 'gruen_tief')

# Obsidian: Vulkanglas - fast schwarz, Kante glasig hell, Kern lila
OBSIDIAN = {'kante': 'tiefschwarz', 'glanz': 'stahl_hell', 'hell': 'stahl_mitte',
            'fase': 'stahl_kante', 'mitte': 'gift_dk', 'licht': 'stahl_dunkel',
            'rinne': 'gift', 'ruecken': 'stahl_kante'}
OBSIDIAN_TON = ('stahl_dunkel', 'stahl_kante', 'tiefschwarz', 'schwarz')
GRIFF_OBSIDIAN = ('gift', 'gift_dk', 'stahl_kante', 'tiefschwarz')

# Heilig: Elfenbein mit goldener Kehle
HEILIG = {'kante': 'knochen_dunkel', 'glanz': 'weiss', 'hell': 'creme',
          'fase': 'knochen_mitte', 'mitte': 'knochen_licht', 'licht': 'creme',
          'rinne': 'gold', 'ruecken': 'knochen_fase'}
ELFENBEIN = ('weiss', 'creme', 'knochen_licht', 'knochen_fase')
SAPHIR = ('kristall_hell', 'saphir', 'kristall_dunkel', 'kristall_tief')
GRIFF_WEISS = ('creme', 'knochen_licht', 'knochen_mitte', 'knochen_fase')

# Schrott: Eisen mit Rost
ROST_TON = ('leder_licht', 'rost', 'rost_dk')
GRIFF_SEIL = ('leder_hell', 'leder_licht', 'leder_mitte', 'leder_dunkel')


# --- Neue Familien -----------------------------------------------------------

def thorn(img, stufe):
    """Dornholz: Rindenklinge, Dornen an beiden Kanten, Blaetter als Parier,
    Rankengriff, Astknoten als Knauf."""
    m = masse(stufe, 'thorn')
    L, halb = m['laenge'], m['halb'] * 1.1
    ox, oy = ursprung(img, L, stufe)
    oy -= 1
    klinge(img, ox, oy, L, halb, HOLZ, spitze=m['spitze'] * 1.1,
           ricasso=m['ricasso'], rinne_bis=0.8, glanz=(),
           marken=tuple(L * f for f in (0.25, 0.4, 0.55, 0.7)), stumpf=False)
    # Dornen: an der Schneide nach vorn-aussen, am Ruecken nach hinten-aussen
    n = 1 + stufe
    for i in range(n):
        u = m['ricasso'] + 1.5 + (L - m['ricasso'] - m['spitze'] * 1.1 - 1.5) * (i + 0.5) / n
        dl = 1.8 + stufe * 0.5
        x, y = to_xy(u, -halb + 0.4, ox, oy)
        keil(img, x, y, -0.4, -1.0, dl, 0.7 + stufe * 0.15, DORN_TON, kruemmung=0.6)
        if stufe >= 2 and i % 2 == 0:
            x, y = to_xy(u + 1.0, halb - 0.4, ox, oy)
            keil(img, x, y, 0.6, 1.0, dl * 0.8, 0.6 + stufe * 0.12, DORN_TON,
                 kruemmung=-0.6)
    pd = m['pd']
    schlagschatten(img, ox, oy, HOLZ, 0.0, 0.8 + 0.3 * stufe, halb)
    # Parier: zwei Blaetter, schraeg nach vorn
    cx, cy = to_xy(-pd * 0.6, 0.0, ox, oy)
    bl = 3.0 + stufe * 1.4
    bb = 1.0 + stufe * 0.35
    raute(img, cx, cy, -1.0, -0.35, bl, bb, BLATT_TON)
    raute(img, cx, cy, 0.35, 1.0, bl, bb, BLATT_TON)
    kugel(img, cx, cy, 0.8 + stufe * 0.25, ('leder_licht', 'leder_mitte',
                                             'leder_dunkel', 'leder_tief'))
    glen = m['glen'] * 1.2
    griff(img, ox, oy, -(pd * 1.1 + glen + 0.4), -(pd * 1.1 + 0.6),
          0.45 + stufe * 0.07, *GRIFF_RANKE)
    kn = m['knauf'] * 1.2
    kx, ky = to_xy(-(pd * 1.1 + glen + 0.4) - kn * 0.6, 0.0, ox, oy)
    kugel(img, kx, ky, kn, ('leder_licht', 'leder_mitte', 'leder_dunkel', 'leder_tief'),
          glanz='leder_hell')
    if stufe >= 2:                                 # kleines Blatt am Knoten
        raute(img, kx, ky + 1, -0.6, 1.0, 2.0 + stufe * 0.5, 0.6 + stufe * 0.15, BLATT_TON)
    return ox, oy, L, halb, HOLZ


def obsidian(img, stufe):
    """Vulkanglas: gezackte Schneide, klobige Fassung, Splitterknauf."""
    m = masse(stufe, 'obsidian')
    L, halb = m['laenge'], m['halb'] * 1.15
    ox, oy = ursprung(img, L, stufe)
    schritt = 3.0 if stufe < 3 else 4.5
    scharten = tuple(u for u in (m['ricasso'] + 2.0 + i * schritt for i in range(12))
                     if u < L - 3.5) if stufe >= 2 else ()
    klinge(img, ox, oy, L, halb, OBSIDIAN, spitze=m['spitze'] * 1.2,
           ricasso=m['ricasso'] * 1.2, rinne_bis=0.7, scharten=scharten,
           glanz=(L * 0.3, L * 0.6, L * 0.8), stumpf=False,
           scharte=0.7)
    if stufe >= 3:                                 # lila Glut in der Kehle
        for i in range(int(m['ricasso']) + 2, int(L * 0.7), 3):
            speck(img, ox, oy, float(i), 0.0, 'gift_hell')
    pd, pw = m['pd'] * 1.2, m['pw'] * 1.1
    schlagschatten(img, ox, oy, OBSIDIAN, 0.0, 0.8 + 0.3 * stufe, halb)
    # Fassung: zwei Kloetze statt einer Stange, Glasglanz oben
    block(img, ox, oy, -pd * 1.1, pd, pw, OBSIDIAN_TON)
    for v in (-pw * 0.8, pw * 0.8):
        speck(img, ox, oy, -pd * 1.1 + pd * 0.4, v, 'stahl_licht')
    glen = m['glen'] * 1.15
    griff(img, ox, oy, -(pd * 1.1 + glen + 0.4), -(pd * 1.1 + 0.9),
          0.45 + stufe * 0.07, *GRIFF_OBSIDIAN)
    kn = m['knauf']
    kx, ky = to_xy(-(pd * 1.1 + glen + 0.4), 0.0, ox, oy)
    raute(img, kx, ky, -1.0, 1.0, 2.5 + stufe * 1.1, 0.8 + stufe * 0.25,
          ('stahl_licht', 'stahl_dunkel', 'tiefschwarz', 'schwarz'))
    return ox, oy, L, halb, OBSIDIAN


def holy(img, stufe):
    """Heilig: Elfenbeinklinge mit Goldkehle, Fluegel als Parier, Saphir,
    Heiligenschein als Knauf."""
    m = masse(stufe, 'holy')
    L, halb = m['laenge'] * 1.05, m['halb'] * 0.95
    ox, oy = ursprung(img, L, stufe)
    ox += 1
    klinge(img, ox, oy, L, halb, HEILIG, spitze=m['spitze'] * 1.4,
           ricasso=m['ricasso'], rinne_bis=0.8,
           glanz=(L * 0.3, L * 0.55, L * 0.8), stumpf=False)
    pd = m['pd']
    schlagschatten(img, ox, oy, HEILIG, 0.0, 0.8 + 0.3 * stufe, halb)
    # Fluegel: zwei Keile, die von der Mitte nach aussen und leicht zur
    # Spitze schwingen, mit Federkerben
    cx, cy = to_xy(-pd * 0.5, 0.0, ox, oy)
    fl = 3.5 + stufe * 1.6
    fb = 1.1 + stufe * 0.4
    keil(img, cx, cy, -1.0, -0.7, fl, fb, ELFENBEIN, kruemmung=-1.0, spitz=True)
    keil(img, cx, cy, 0.7, 1.0, fl, fb, ELFENBEIN, kruemmung=1.0, spitz=True)
    for i in range(1, int(fl) - 1, 2):             # Federkerben
        put(img, int(cx - i * 0.75), int(cy - i * 0.5) + 1, C('knochen_mitte'))
        put(img, int(cx + i * 0.55) + 1, int(cy + i * 0.8), C('knochen_mitte'))
    kugel(img, cx, cy, 1.0 + stufe * 0.35, SAPHIR, glanz='weiss')
    glen = m['glen'] * 1.2
    griff(img, ox, oy, -(pd * 1.1 + glen + 0.4), -(pd * 1.1 + 0.8),
          0.42 + stufe * 0.06, *GRIFF_WEISS)
    for i in range(1, int(glen), 2):               # Golddraht
        speck(img, ox, oy, -(pd * 1.1 + 0.8 + i), 0.2, 'gold_mitte')
    kn = m['knauf'] * (1.5 if stufe < 3 else 1.9)
    kx, ky = to_xy(-(pd * 1.1 + glen + 0.4) - kn * 0.7, 0.0, ox, oy)
    if stufe >= 2:
        ring(img, kx, ky, kn, 1.1 + stufe * 0.1, GOLD_BESCHLAG, glanz='gold_hell')
    else:
        kugel(img, kx, ky, kn * 0.8, GOLD_BESCHLAG, glanz='gold_hell')
    return ox, oy, L, halb, HEILIG


def scrap(img, stufe):
    """Schrott: zusammengeflicktes Eisen - Rostflecken, ausgebrochene
    Schneide, Bolzen, Stange aus zwei Platten, Seilgriff, Bolzenknauf."""
    m = masse(stufe, 'scrap')
    L, halb = m['laenge'], m['halb'] * 1.1
    ox, oy = ursprung(img, L, stufe)
    scharten = {1: (L * 0.5,), 2: (L * 0.3, L * 0.65), 3: (L * 0.25, L * 0.5, L * 0.72),
                4: (L * 0.2, L * 0.38, L * 0.6, L * 0.78)}[stufe]
    klinge(img, ox, oy, L, halb, EISEN_TON, spitze=m['spitze'] * 0.7,
           ricasso=m['ricasso'] * 1.4, rinne_bis=0.6, scharten=scharten,
           glanz=(L * 0.45,))
    stellen = [(L * 0.35, halb * 0.3), (L * 0.62, -halb * 0.2)][:stufe]
    if stufe >= 3:
        stellen += [(L * 0.15, -halb * 0.4), (L * 0.8, halb * 0.4)]
    flecken(img, ox, oy, stellen, ROST_TON)
    # Bolzen durch die Klinge (Ricasso) und ueber die Scharten
    nieten(img, ox, oy, ((m['ricasso'] * 0.7, 0.0),) +
           tuple((su + 1.0, halb * 0.45) for su in scharten[:2]),
           col='stahl_kante', licht='stahl_hell')
    pd, pw = m['pd'] * 1.1, m['pw'] * 1.3
    schlagschatten(img, ox, oy, EISEN_TON, 0.0, 1.0 + 0.3 * stufe, halb)
    # Stange: zwei ungleich lange Platten uebereinander
    block(img, ox, oy, -pd * 1.1 + pd * 0.5, pd * 0.5, pw, EISEN_DUNKEL)
    block(img, ox, oy, -pd * 1.1 - pd * 0.5, pd * 0.5, pw * 0.7, EISEN_BESCHLAG)
    flecken(img, ox, oy, ((-pd * 1.1 + pd * 0.5, pw * 0.5),), ROST_TON)
    glen = m['glen'] * 1.2
    griff(img, ox, oy, -(pd * 1.1 + glen + 0.4), -(pd * 1.1 + 1.0),
          0.45 + stufe * 0.07, *GRIFF_SEIL)
    kn = m['knauf']
    ende = -(pd * 1.1 + glen + 0.4)
    block(img, ox, oy, ende - kn * 0.6, kn * 0.6 + 0.2, kn * 0.8 + 0.3, EISEN_DUNKEL)
    speck(img, ox, oy, ende - kn * 0.6, 0.0, 'stahl_kante')
    troddel(img, ox, oy, ende - kn * 0.6, 2 + stufe)


# --- Axtkopf und Speerblatt im u/v-Raster -------------------------------------
    return ox, oy, L, halb, EISEN_TON


def axtkopf(img, ox, oy, u_c, rad, ton, doppelt=False, bart=0.0):
    """Axtblatt: Halbellipse quer zum Schaft, Schneide zur Lichtseite
    (v < 0). Baender von der Schneide nach innen wie bei der Klinge; am
    Schaft eine dunkle Fassung. bart zieht die Unterkante zum Griff."""
    seiten = (-1, 1) if doppelt else (-1,)
    a_u = rad * 0.62
    for y in range(img.height):
        for x in range(img.width):
            u, v = to_uv(x, y, ox, oy)
            for seite in seiten:
                vv = v * seite
                if vv > -0.2:
                    continue
                t = -vv / rad                        # 0 am Schaft, 1 an der Schneide
                if t > 1.0:
                    continue
                mitte_u = u_c - bart * t * t * rad * 0.5
                rn = math.sqrt(((u - mitte_u) / a_u) ** 2 + t * t)
                if rn > 1.0:
                    continue
                tiefe = (1.0 - rn) * rad * 2.0       # Pixel von der Schneide
                if tiefe < 1.0 or t < 0.12:
                    name = 'kante'
                elif tiefe < 2.0:
                    name = 'glanz'
                elif tiefe < 3.0:
                    name = 'hell'
                elif tiefe < 4.0:
                    name = 'fase'
                else:
                    # Flaeche als Baender parallel zum Schaft (diagonal, also
                    # ohne Flaechen): vom Schaft zur Schneide heller
                    k = int(-vv * 2.0)
                    folge = ('ruecken', 'fase') if k < 3 else (
                        ('fase', 'mitte') if k < 7 else (
                            ('mitte', 'licht') if k < 11 else ('licht', 'hell')))
                    name = folge[k % 2]
                put(img, x, y, C(ton[name]))


def speerblatt(img, ox, oy, u0, laenge, halb, ton):
    """Blattspitze: Raute entlang der Achse mit Mittelgrat; Lichtseite
    (v < 0) hell, Schattenseite dunkel, Grat als Glanzlinie."""
    for y in range(img.height):
        for x in range(img.width):
            u, v = to_uv(x, y, ox, oy)
            t = (u - u0) / laenge
            if t < 0.0 or t > 1.0:
                continue
            hw = halb * (1.0 - abs(t - 0.4) / (0.6 if t > 0.4 else 0.4))
            if abs(v) > hw + 0.01:
                continue
            if hw - abs(v) < 0.5 or t > 0.95:
                name = 'kante'
            elif abs(v) < 0.35:
                name = 'glanz'
            elif v < 0:
                name = 'hell' if hw - abs(v) < 1.2 else 'licht'
            else:
                name = 'fase' if hw - abs(v) < 1.2 else 'ruecken'
            put(img, x, y, C(ton[name]))


def blitz(img, ox, oy, u0, u1, v0, amplitude, col_a, col_b):
    """Zickzack-Linie entlang der Klinge - Blitz auf dem Sturmschwert."""
    u = u0
    k = 0
    while u < u1:
        v = v0 + (amplitude if k % 2 else -amplitude)
        speck(img, ox, oy, u, v, col_a if k % 2 else col_b)
        speck(img, ox, oy, u + 0.5, (v + v0) / 2, col_a)
        u += 1.5
        k += 1


def rauch(img, ox, oy, laenge, halb, stufe, toene):
    """Rauchfahnen vom Ruecken: haengen an der Klinge, winden sich nach
    unten aus und werden zur Spitze hin lichter (lila statt schwarz)."""
    stellen = ((0.5,), (0.35, 0.65), (0.3, 0.55, 0.8), (0.25, 0.45, 0.65, 0.85))[stufe - 1]
    for i, f in enumerate(stellen):
        u = laenge * f
        x, y = to_xy(u, halb - 0.4, ox, oy)
        laenge_r = 3 + stufe + (i % 2)
        for j in range(laenge_r):
            dx = int(round(0.8 * math.sin(j * 0.9 + i)))   # hoechstens 1 Versatz je Zeile
            col = toene[0] if j < laenge_r // 3 else (toene[1] if j < 2 * laenge_r // 3 else toene[2])
            put(img, x + dx, y + 1 + j, C(col))
            if j < laenge_r - 2:
                put(img, x + dx + 1, y + 1 + j, C(toene[min(2, j // 2 + 1)]))


# --- Toene ---------------------------------------------------------------------

FROST = {'kante': 'eis_nacht', 'glanz': 'weiss', 'hell': 'eis_hell',
         'fase': 'eis_dk', 'mitte': 'eis', 'licht': 'eis_hell',
         'rinne': 'eis_tief', 'ruecken': 'eis_dk'}
EIS_TON = ('weiss', 'eis_hell', 'eis', 'eis_nacht')
GRIFF_EIS = ('eis_hell', 'eis', 'eis_dk', 'eis_nacht')

STURM = {'kante': 'stahl_kante', 'glanz': 'weiss', 'hell': 'stahl_hell',
         'fase': 'kristall_dunkel', 'mitte': 'stahl_mitte', 'licht': 'stahl_licht',
         'rinne': 'kristall_tief', 'ruecken': 'stahl_dunkel'}
STURM_BESCHLAG = ('gold', 'gold_mitte', 'gold_dunkel', 'rost_dk')

SCHATTEN = {'kante': 'schatten_dk', 'glanz': 'lila_hell', 'hell': 'gift',
            'fase': 'schatten', 'mitte': 'gift_dk', 'licht': 'stahl_kante',
            'rinne': 'schatten_dk', 'ruecken': 'schatten'}
SCHATTEN_TON = ('gift', 'gift_dk', 'schatten', 'schatten_dk')
RAUCH = ('gift', 'gift_dk', 'lila_hell')

GOLDKLINGE = {'kante': 'rost_dk', 'glanz': 'gold_hell', 'hell': 'gold',
              'fase': 'gold_dunkel', 'mitte': 'gold_mitte', 'licht': 'gold',
              'rinne': 'kupfer', 'ruecken': 'gold_dunkel'}
SMARAGD = ('gruen_hell', 'smaragd', 'smaragd_dk', 'gruen_tief')
GRIFF_SAMT = ('feuer_rot', 'feuer_dk', 'feuer_tief', 'schatten_dk')

AXT_STAHL = STAHL
GRIFF_HOLZ = ('leder_licht', 'leder_mitte', 'leder_dunkel', 'leder_tief')


# --- Neue Familien -------------------------------------------------------------

def frost(img, stufe):
    """Eisklinge: weisse Schneide, Eiszapfen haengen vom Ruecken, Splitter
    als Parier, Schneeflocke als Knauf."""
    m = masse(stufe, 'frost')
    L, halb = m['laenge'], m['halb']
    ox, oy = ursprung(img, L, stufe)
    klinge(img, ox, oy, L, halb, FROST, spitze=m['spitze'] * 1.3,
           ricasso=m['ricasso'], rinne_bis=0.75, glanz=(L * 0.3, L * 0.6),
           stumpf=False)
    # Eiszapfen: Keile vom Ruecken nach unten, ungleich lang
    for i, f in enumerate(((0.35, 0.65), (0.3, 0.5, 0.72), (0.25, 0.45, 0.62, 0.8),
                           (0.2, 0.36, 0.52, 0.68, 0.84))[stufe - 1]):
        u = L * f
        x, y = to_xy(u, halb - 0.3, ox, oy)
        zl = 2.0 + stufe * 0.7 + (1.5 if i % 2 else 0.0)
        keil(img, x, y, 0.15, 1.0, zl, 0.6 + stufe * 0.15, EIS_TON)
    pd = m['pd']
    schlagschatten(img, ox, oy, FROST, 0.0, 0.8 + 0.3 * stufe, halb)
    cx, cy = to_xy(-pd * 0.6, 0.0, ox, oy)
    sl = 2.5 + stufe * 1.2
    raute(img, cx, cy, -1.0, -0.5, sl, 0.8 + stufe * 0.25, EIS_TON)
    raute(img, cx, cy, 0.5, 1.0, sl, 0.8 + stufe * 0.25, EIS_TON)
    kugel(img, cx, cy, 0.8 + stufe * 0.2, EIS_TON)
    glen = m['glen'] * 1.2
    griff(img, ox, oy, -(pd * 1.1 + glen + 0.4), -(pd * 1.1 + 0.6),
          0.45 + stufe * 0.07, *GRIFF_EIS)
    kn = m['knauf'] * 1.2
    kx, ky = to_xy(-(pd * 1.1 + glen + 0.4) - kn * 0.7, 0.0, ox, oy)
    # Schneeflocke: drei kurze Rauten ueber Kreuz
    for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1)):
        raute(img, kx - dx * kn, ky - dy * kn, dx, dy, kn * 2.0, 0.5 + stufe * 0.12, EIS_TON)
    kugel(img, kx, ky, 0.7 + stufe * 0.2, EIS_TON, glanz='weiss')
    return ox, oy, L, halb, FROST


def storm(img, stufe):
    """Sturmschwert: Stahl mit blauer Kehle, ein Blitz zuckt ueber die
    Klinge, die Parierstange sind zwei Blitze, Knauf eine Wolke."""
    m = masse(stufe, 'storm')
    L, halb = m['laenge'], m['halb'] * 0.95
    ox, oy = ursprung(img, L, stufe)
    ox += 1
    klinge(img, ox, oy, L, halb, STURM, spitze=m['spitze'] * 1.3,
           ricasso=m['ricasso'], rinne_bis=0.8, glanz=(L * 0.7,), stumpf=False)
    blitz(img, ox, oy, m['ricasso'] + 1.0, L - 3.0, 0.0, min(halb * 0.55, 1.5),
          'blitz', 'weiss')
    pd, pw = m['pd'], m['pw'] * 1.3
    schlagschatten(img, ox, oy, STURM, 0.0, 0.8 + 0.3 * stufe, halb)
    cx, cy = to_xy(-pd * 0.7, 0.0, ox, oy)
    # Blitz-Parier: zwei Keile mit Knick
    for sgn in (-1, 1):
        zl = 2.0 + stufe * 0.9
        keil(img, cx, cy, -sgn * 1.0, -sgn * 0.3, zl, 0.6 + stufe * 0.2, STURM_BESCHLAG)
        if stufe >= 2:                               # Knick des Blitzes
            ex, ey = cx - sgn * zl * 0.85, cy - sgn * zl * 0.25
            keil(img, ex, ey, -sgn * 0.5, -sgn * 1.0, zl * 0.8, 0.5 + stufe * 0.15, STURM_BESCHLAG)
    kugel(img, cx, cy, 0.9 + stufe * 0.3, ('kristall_hell', 'kristall_licht', 'kristall_mitte', 'kristall_tief'), glanz='weiss')
    glen = m['glen'] * 1.2
    griff(img, ox, oy, -(pd * 1.1 + glen + 0.4), -(pd * 0.7 + 0.4),
          0.42 + stufe * 0.06, *GRIFF_DUNKELLEDER)
    kn = m['knauf'] * 1.2
    kx, ky = to_xy(-(pd * 1.1 + glen + 0.4) - kn * 0.4, 0.0, ox, oy)
    # Wolke: drei Kugeln nebeneinander
    wolke = ('weiss', 'stahl_hell', 'stahl_licht', 'stahl_mitte')
    kugel(img, kx, ky, max(1.4, kn), wolke)
    if stufe >= 2:
        kugel(img, kx - kn * 0.9, ky + kn * 0.3, kn * 0.7, wolke)
        kugel(img, kx + kn * 0.7, ky + kn * 0.5, kn * 0.6, wolke)
    return ox, oy, L, halb, STURM


def shadow(img, stufe):
    """Schattenschwert: fast schwarze Klinge mit lila Saum, Rauch steigt
    vom Ruecken auf, Krallen als Parier, Totenschaedel als Knauf."""
    m = masse(stufe, 'shadow')
    L, halb = m['laenge'], m['halb'] * 1.05
    ox, oy = ursprung(img, L, stufe)
    oy -= 2 + stufe
    klinge(img, ox, oy, L, halb, SCHATTEN, spitze=m['spitze'] * 1.5,
           ricasso=m['ricasso'], rinne_bis=0.7, glanz=(L * 0.35, L * 0.7),
           stumpf=False, kruemmung=0.3 * stufe)
    rauch(img, ox, oy, L, halb, stufe, RAUCH)
    pd = m['pd']
    schlagschatten(img, ox, oy, SCHATTEN, 0.0, 0.8 + 0.3 * stufe, halb)
    cx, cy = to_xy(-pd * 0.7, 0.0, ox, oy)
    zl = 2.5 + stufe * 1.2
    keil(img, cx, cy, -1.0, -0.4, zl, 0.7 + stufe * 0.25, SCHATTEN_TON, kruemmung=-1.4)
    keil(img, cx, cy, 0.4, 1.0, zl, 0.7 + stufe * 0.25, SCHATTEN_TON, kruemmung=1.4)
    block(img, ox, oy, -pd * 0.7, 0.5 + stufe * 0.12, 0.9 + stufe * 0.2, SCHATTEN_TON)
    glen = m['glen'] * 1.15
    griff(img, ox, oy, -(pd * 1.1 + glen + 0.4), -(pd * 1.1 + 0.6),
          0.45 + stufe * 0.07, *('gift_dk', 'schatten', 'schatten_dk', 'schatten_dk'))
    kn = max(1.6, m['knauf'] * 1.3)
    kx, ky = to_xy(-(pd * 1.1 + glen + 0.4) - kn * 0.7, 0.0, ox, oy)
    kugel(img, kx, ky, kn, KNOCHEN_TON)
    if kn >= 1.8:                                   # Augenhoehlen, lila gluehend
        put(img, int(kx) - 1, int(ky), C('schatten_dk'))
        put(img, int(kx) + 1, int(ky), C('schatten_dk'))
        put(img, int(kx) - 1, int(ky) + 1, C('lila_hell'))
        put(img, int(kx) + 1, int(ky) + 1, C('lila_hell'))
    return ox, oy, L, halb, SCHATTEN


def royal(img, stufe):
    """Koenigsschwert: Goldklinge mit Gravur, Stange mit gerollten Enden,
    Smaragd, Samtgriff mit Golddraht, Kronenknauf."""
    m = masse(stufe, 'royal')
    L, halb = m['laenge'] * 1.05, m['halb'] * 0.9
    ox, oy = ursprung(img, L, stufe)
    ox += 1
    klinge(img, ox, oy, L, halb, GOLDKLINGE, spitze=m['spitze'] * 1.4,
           ricasso=m['ricasso'] * 1.2, rinne_bis=0.75,
           glanz=(L * 0.3, L * 0.55, L * 0.8),
           marken=tuple(L * f for f in (0.2, 0.3, 0.4, 0.5, 0.6)) if stufe >= 2 else (),
           stumpf=False)
    pd, pw = m['pd'], m['pw'] * 1.5
    schlagschatten(img, ox, oy, GOLDKLINGE, 0.0, 0.8 + 0.3 * stufe, halb)
    parier(img, ox, oy, -pd * 1.1, pd, pw, *GOLD_BESCHLAG, schwung=0.5 * stufe)
    for sgn in (-1, 1):                              # gerollte Enden
        ex, ey = to_xy(-pd * 1.1 + 0.5 * stufe, sgn * pw, ox, oy)
        kugel(img, ex, ey, 0.9 + stufe * 0.3, GOLD_BESCHLAG, glanz='gold_hell')
    cx, cy = to_xy(-pd * 1.1, 0.0, ox, oy)
    kugel(img, cx, cy, 1.0 + stufe * 0.35, SMARAGD, glanz='weiss')
    glen = m['glen'] * 1.25
    griff(img, ox, oy, -(pd * 1.1 + glen + 0.4), -(pd * 1.1 + 0.9),
          0.42 + stufe * 0.06, *GRIFF_SAMT)
    for i in range(1, int(glen), 2):
        speck(img, ox, oy, -(pd * 1.1 + 0.9 + i), -0.2, 'gold')
    kn = m['knauf'] * 1.3
    ku = -(pd * 1.1 + glen + 0.4) - kn * 0.6
    block(img, ox, oy, ku, kn * 0.5, kn * 0.9, GOLD_BESCHLAG)
    for k in (-1, 0, 1):                             # Kronenzacken
        speck(img, ox, oy, ku - kn * 0.5 - 0.7, k * kn * 0.7, 'gold')
        speck(img, ox, oy, ku - kn * 0.5 - 1.2, k * kn * 0.7, 'gold_mitte')
    speck(img, ox, oy, ku, 0.0, 'feuer_rot')
    return ox, oy, L, halb, GOLDKLINGE


def axe(img, stufe):
    """Streitaxt: Holzschaft, Stahlblatt als Sichel, ab Stufe 3 doppelt,
    Bart zum Griff, Schaftringe, Lederwicklung."""
    m = masse(stufe, 'axe')
    L = m['laenge'] * 1.05
    rad = 3.0 + stufe * 1.6
    ox, oy = ursprung(img, L, stufe)
    ox -= 2
    schaft = ('leder_licht', 'leder_mitte', 'leder_dunkel', 'leder_tief')
    # Schaft ueber die ganze Laenge, oben mit Zwinge
    griff(img, ox, oy, -(m['glen'] * 1.2 + 1.0), L - 0.5, 0.45 + stufe * 0.1, *schaft)
    for u in (L - 1.5, L * 0.55, -(m['glen'] * 0.6)):
        block(img, ox, oy, u, 0.6, 0.7 + stufe * 0.12, EISEN_BESCHLAG)
    u_c = L - rad * 0.62 - 1.0
    axtkopf(img, ox, oy, u_c, rad, AXT_STAHL, doppelt=(stufe >= 3), bart=0.6 + stufe * 0.15)
    # Lederwicklung unten, Knauf als Kappe, Troddel
    ende = -(m['glen'] * 1.2 + 1.0)
    griff(img, ox, oy, ende, ende + m['glen'] * 0.8, 0.5 + stufe * 0.1, *GRIFF_LEDER)
    block(img, ox, oy, ende - 0.6, 0.6, 0.7 + stufe * 0.12, EISEN_DUNKEL)
    troddel(img, ox, oy, ende - 0.6, 2 + stufe)
    # Glanzstern auf dem Blatt
    x, y = to_xy(u_c, -rad * 0.55, ox, oy)
    funkeln(img, x, y, 'weiss', 'stahl_hell', gross=(stufe >= 3))
    return None


def spear(img, stufe):
    """Speer: langer Schaft, Blattspitze mit Grat, Tuelle, ab Stufe 2
    Seitenfluegel, ab Stufe 3 Federbund unter der Spitze."""
    m = masse(stufe, 'spear')
    L = m['laenge'] * 1.25
    bl = 4.0 + stufe * 2.2
    halb = 0.9 + stufe * 0.45
    ox, oy = ursprung(img, L, stufe)
    ox -= 2
    schaft = ('leder_licht', 'leder_mitte', 'leder_dunkel', 'leder_tief')
    griff(img, ox, oy, -(m['glen'] * 1.0 + 1.0), L - bl + 0.5, 0.4 + stufe * 0.08, *schaft)
    speerblatt(img, ox, oy, L - bl, bl, halb, STAHL)
    block(img, ox, oy, L - bl - 0.3, 0.8 + stufe * 0.15, 0.6 + stufe * 0.15, EISEN_BESCHLAG)
    if stufe >= 2:                                   # Seitenfluegel an der Tuelle
        x, y = to_xy(L - bl - 0.3, 0.0, ox, oy)
        fl = 1.5 + stufe * 0.6
        keil(img, x, y, -0.6, -1.0, fl, 0.5 + stufe * 0.15, EISEN_BESCHLAG)
        keil(img, x, y, 1.0, 0.6, fl, 0.5 + stufe * 0.15, EISEN_BESCHLAG)
    if stufe >= 3:                                   # Federbund
        for k in range(3):
            x, y = to_xy(L - bl - 1.5 - k * 0.5, 0.9 + k * 0.4, ox, oy)
            keil(img, x, y, 0.3, 1.0, 3.0 + k, 0.7, ('feuer_rot', 'kupfer', 'feuer_dk', 'feuer_tief'))
    ende = -(m['glen'] * 1.0 + 1.0)
    block(img, ox, oy, ende - 0.5, 0.6, 0.6 + stufe * 0.1, EISEN_DUNKEL)
    x, y = to_xy(L - bl * 0.55, -halb * 0.3, ox, oy)
    funkeln(img, x, y, 'weiss', 'stahl_hell', gross=(stufe >= 3))
    return None


# --- Rune, Koralle, Drache -----------------------------------------------------

RUNENSTEIN = {'kante': 'stahl_kante', 'glanz': 'stahl_licht', 'hell': 'stein_hell',
              'fase': 'stein_tief', 'mitte': 'stein', 'licht': 'stein_hell',
              'rinne': 'stahl_kante', 'ruecken': 'stein_tief'}
KORALLE = {'kante': 'koralle_tief', 'glanz': 'perle', 'hell': 'koralle_hell',
           'fase': 'koralle_dk', 'mitte': 'koralle', 'licht': 'koralle_hell',
           'rinne': 'koralle_tief', 'ruecken': 'koralle_dk'}
KORALLE_TON = ('koralle_hell', 'koralle', 'koralle_dk', 'koralle_tief')
PERLE_TON = ('weiss', 'perle', 'knochen_mitte', 'knochen_fase')
# sechs verschiedene Toene, sonst legt die Band-Entdopplung Streifen an
DRACHE = {'kante': 'feuer_tief', 'glanz': 'gold', 'hell': 'gold_dunkel',
          'fase': 'drache_dk', 'mitte': 'drache', 'licht': 'drache_hell',
          'rinne': 'feuer_tief', 'ruecken': 'schatten_dk'}
DRACHE_TON = ('drache_hell', 'drache', 'drache_dk', 'feuer_tief')
HORN_TON = ('creme', 'knochen_mitte', 'knochen_fase', 'knochen_kante')


def schuppen(img, ox, oy, laenge, halb, stufe, ton):
    """Schuppenmuster auf der Klinge: versetzte Boegen in Kante und Licht."""
    ricasso = STUFEN[stufe - 1][3]
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            if not px[x, y][3]:
                continue
            u, v = to_uv(x, y, ox, oy)
            if u < ricasso + 1 or u > laenge - 3 or abs(v) > halb - 0.8:
                continue
            reihe = int((v + halb) // 1.0)
            phase = (u + (0.5 if reihe % 2 else 0.0)) % 2.0
            if phase < 0.5:
                put(img, x, y, C(ton['kante']))
            elif phase < 1.0 and (v + halb) % 1.0 < 0.5:
                put(img, x, y, C(ton['glanz']))


def rune(img, stufe):
    """Runenstein: eine breite Steinplatte mit gerade abgeschlagener Spitze
    und gemeisselten Kanten - keine Klinge, ein Schlagstein. Glyphenreihe
    leuchtet, Fassung aus Stein, Schaft mit Lederwicklung."""
    m = masse(stufe, 'rune')
    L, halb = m['laenge'] * 0.95, m['halb'] * 1.35
    ox, oy = ursprung(img, L, stufe)
    klinge(img, ox, oy, L, halb, RUNENSTEIN, spitze=1.2, ricasso=m['ricasso'] * 1.3,
           rinne_bis=0.82, glanz=(), stumpf=True)
    # gemeisselte Kanten: eine zweite dunkle Linie innen entlang der Schneide
    for i in range(int(m['ricasso']) + 1, int(L) - 2):
        speck(img, ox, oy, float(i), -halb + 1.4, 'stein_tief')
    anzahl = min(5, 2 + stufe)
    schritt = (L * 0.8 - m['ricasso'] - 2.0) / anzahl
    for k in range(anzahl):
        u = m['ricasso'] + 2.0 + k * schritt
        bx, by = to_xy(u, 0.0, ox, oy)
        for dx, dy in RUNEN[k % len(RUNEN)]:
            put(img, bx + dx, by + dy - 1, C('kristall_licht'))
        put(img, bx, by, C('kristall_hell'))
    pd, pw = m['pd'] * 1.3, m['pw'] * 1.1
    schlagschatten(img, ox, oy, RUNENSTEIN, 0.0, 0.8 + 0.3 * stufe, halb)
    stein = ('stein_hell', 'stein', 'stein_dk', 'stahl_kante')
    block(img, ox, oy, -pd * 1.1, pd, pw, stein)
    for sgn in (-1, 1):                                # Kerben in der Fassung
        speck(img, ox, oy, -pd * 1.1, sgn * pw * 0.5, 'stahl_kante')
    glen = m['glen'] * 1.2
    griff(img, ox, oy, -(pd * 1.1 + glen + 0.4), -(pd * 1.1 + 0.9),
          0.45 + stufe * 0.07, *GRIFF_LEDER)
    kn = m['knauf'] * 1.1
    ku = -(pd * 1.1 + glen + 0.4) - kn * 0.6
    block(img, ox, oy, ku, kn * 0.7, kn * 0.8, stein)
    speck(img, ox, oy, ku, 0.0, 'kristall_licht')
    return None


def coral(img, stufe):
    """Korallen-Falchion: gekruemmte Klinge, die sich zur Spitze weitet und
    dort schraeg abgeschnitten ist; Muschel als Parier, Perlenknauf,
    Seegras. Eine andere Silhouette als jedes gerade Schwert."""
    m = masse(stufe, 'coral')
    L, halb = m['laenge'], m['halb'] * 0.85
    ox, oy = ursprung(img, L, stufe)
    oy -= 1 + stufe
    klinge(img, ox, oy, L, halb, KORALLE, spitze=2.5 + stufe * 0.5,
           ricasso=m['ricasso'], rinne_bis=0.6, kruemmung=0.35 * stufe, bauch=0.6,
           glanz=(L * 0.5, L * 0.8), stumpf=True)
    pd = m['pd']
    schlagschatten(img, ox, oy, KORALLE, 0.0, 0.8 + 0.3 * stufe, halb)
    cx, cy = to_xy(-pd * 0.7, 0.0, ox, oy)
    r = 1.6 + stufe * 0.6
    kugel(img, cx, cy, r, PERLE_TON)
    for k in range(-1, 2):                             # Rillen der Muschel
        put(img, int(cx + k), int(cy - r * 0.5), C('knochen_fase'))
        put(img, int(cx + k * 2), int(cy + r * 0.3), C('knochen_fase'))
    glen = m['glen'] * 1.15
    griff(img, ox, oy, -(pd * 1.1 + glen + 0.4), -(pd * 0.7 + 0.6),
          0.45 + stufe * 0.07, *('koralle', 'koralle_dk', 'koralle_tief', 'feuer_tief'))
    kn = m['knauf'] * 1.2
    kx, ky = to_xy(-(pd * 1.1 + glen + 0.4) - kn * 0.6, 0.0, ox, oy)
    kugel(img, kx, ky, kn, PERLE_TON, glanz='weiss')
    for i in range(2 + stufe * 2):
        put(img, kx - i // 2, ky + int(kn) + i, C('gruen' if i % 2 else 'gruen_dk'))
    return ox, oy, L, halb, KORALLE


def dragon(img, stufe):
    """Drachen-Flamberge: die ganze Klinge wellt sich, Goldschneide,
    Hornzaehne als Parier, Klauenknauf. Die Welle ist die Silhouette."""
    m = masse(stufe, 'dragon')
    L, halb = m['laenge'], m['halb']
    ox, oy = ursprung(img, L, stufe)
    klinge(img, ox, oy, L, halb, DRACHE, spitze=m['spitze'] * 1.3,
           ricasso=m['ricasso'], rinne_bis=0.7, welle=(0.35 + 0.12 * stufe, 4.0 + stufe * 0.5),
           glanz=(L * 0.3, L * 0.6), stumpf=False)
    pd = m['pd']
    schlagschatten(img, ox, oy, DRACHE, 0.0, 0.8 + 0.3 * stufe, halb)
    cx, cy = to_xy(-pd * 0.7, 0.0, ox, oy)
    zl = 2.5 + stufe * 1.3
    keil(img, cx, cy, -1.0, -0.5, zl, 0.8 + stufe * 0.3, HORN_TON, kruemmung=-1.0)
    keil(img, cx, cy, 0.5, 1.0, zl, 0.8 + stufe * 0.3, HORN_TON, kruemmung=1.0)
    block(img, ox, oy, -pd * 0.7, 0.5 + stufe * 0.12, 1.0 + stufe * 0.25, DRACHE_TON)
    glen = m['glen'] * 1.2
    griff(img, ox, oy, -(pd * 1.1 + glen + 0.4), -(pd * 0.7 + 0.6),
          0.45 + stufe * 0.07, *('drache', 'drache_dk', 'feuer_tief', 'schatten_dk'))
    kn = m['knauf'] * 1.2
    kx, ky = to_xy(-(pd * 1.1 + glen + 0.4) - kn * 0.6, 0.0, ox, oy)
    kugel(img, kx, ky, kn, ('gold', 'gold_mitte', 'gold_dunkel', 'rost_dk'), glanz='gold_hell')
    for sgn in (-1, 1):
        keil(img, kx + sgn * kn * 0.6, ky - kn * 0.4, sgn * 0.6, 1.0, kn + 1.0, 0.6, HORN_TON, kruemmung=-sgn * 0.8)
    return ox, oy, L, halb, DRACHE


NAMEN_TYP = {
    'axe': ('%s_axe', '%s_broadaxe', 'giant_%s_axe', 'great_%s_axe'),
    'spear': ('%s_spear', '%s_pike', 'giant_%s_spear', 'great_%s_spear'),
}


# --- Veredelung ----------------------------------------------------------------
# Was jede Waffe am Ende bekommt: einen Glanzstern nahe der Spitze, ab Stufe 3
# eingravierte Runen auf der Lichtseite, einen weissen Spitzenblitz.

RUNEN = (
    ((0, 0), (1, 0), (0, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (1, 1), (0, 2)),
    ((1, 0), (0, 1), (1, 1), (1, 2)),
)


def funkeln(img, x, y, kern='weiss', arm=None, gross=False, arme=True):
    """Glanzstern: Kreuz aus fuenf Pixeln, bei gross mit laengeren Armen.
    Sitzt der Zielpunkt neben der Waffe (gekruemmte Klinge, kleines Blatt),
    rueckt der Stern auf das naechste gesetzte Pixel."""
    px = img.load()
    if not (0 <= x < img.width and 0 <= y < img.height and px[x, y][3]):
        kandidaten = [(dx * dx + dy * dy, x + dx, y + dy)
                      for dx in range(-4, 5) for dy in range(-4, 5)
                      if 0 <= x + dx < img.width and 0 <= y + dy < img.height
                      and px[x + dx, y + dy][3]]
        if not kandidaten:
            return
        _, x, y = min(kandidaten)
    put(img, x, y, C(kern))
    if not arme:
        return
    a = C(arm) if arm else C(kern)
    arme = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if gross:
        arme += [(2, 0), (-2, 0), (0, 2), (0, -2)]
    for dx, dy in arme:                              # Arme nur auf der Waffe
        if 0 <= x + dx < img.width and 0 <= y + dy < img.height and px[x + dx, y + dy][3]:
            put(img, x + dx, y + dy, a)


def runen(img, ox, oy, stellen, v, col):
    """Kleine Glyphen, eingraviert auf der Lichtseite der Klinge."""
    px = img.load()
    for k, u in enumerate(stellen):
        form = RUNEN[k % len(RUNEN)]
        bx, by = to_xy(u, v, ox, oy)
        for dx, dy in form:
            x, y = bx + dx, by + dy - 1
            if 0 <= x < img.width and 0 <= y < img.height and px[x, y][3]:
                put(img, x, y, C(col))


def veredeln(img, stufe, ox, oy, L, halb, ton):
    """Schlussarbeiten fuer Klingenwaffen."""
    glanz = ton.get('glanz', 'weiss')
    # Spitzenblitz (rueckt bei gekruemmter Klinge auf die Klinge)
    x, y = to_xy(L - 1.5, 0.0, ox, oy)
    funkeln(img, x, y, 'weiss', arme=False)
    # Glanzstern bei 78 % der Laenge, an der Schneide - Stufe 4 zwei Sterne
    x, y = to_xy(L * 0.78, -halb * 0.35, ox, oy)
    funkeln(img, x, y, 'weiss', glanz, gross=(stufe >= 3))
    if stufe >= 4:
        x, y = to_xy(L * 0.45, -halb * 0.5, ox, oy)
        funkeln(img, x, y, 'weiss', glanz)
    # Runen ab Stufe 3 auf der Lichtseite, zwischen Ricasso und Stern
    if stufe >= 3 and halb >= 1.6:
        stellen = [L * f for f in (0.28, 0.4, 0.52, 0.64)][:stufe]
        runen(img, ox, oy, stellen, -halb * 0.45, ton['kante'])



FAMILIEN = {
    'IronSword': ('iron', iron),
    'SteelSword': ('steel', steel),
    'CrystalSword': ('crystal', crystal),
    'EmberSword': ('ember', ember),
    'VenomSword': ('venom', venom),
    'ThornSword': ('thorn', thorn),
    'ObsidianSword': ('obsidian', obsidian),
    'HolySword': ('holy', holy),
    'ScrapSword': ('scrap', scrap),
    'FrostSword': ('frost', frost),
    'StormSword': ('storm', storm),
    'ShadowSword': ('shadow', shadow),
    'RoyalSword': ('royal', royal),
    'BattleAxe': ('iron', axe),
    'Spear': ('iron', spear),
    'RuneSword': ('rune', rune),
    'CoralSword': ('coral', coral),
    'DragonSword': ('dragon', dragon),
}
STUFEN_NAMEN = ('%s_sword', '%s_broadsword', 'giant_%s_sword', 'great_%s_sword')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--nur', help='nur diese Familie')
    args = ap.parse_args()
    wurzel = Path(args.out)
    for ordner, (kurz, bauen) in FAMILIEN.items():
        if args.nur and args.nur != ordner:
            continue
        ziel = wurzel / ordner
        ziel.mkdir(parents=True, exist_ok=True)
        for stufe in (1, 2, 3, 4):
            leinwand = STUFEN[stufe - 1][-1] + 16
            img = blank(leinwand, leinwand)
            rueck = bauen(img, stufe)
            if rueck:
                veredeln(img, stufe, *rueck)
            img = zuschneiden(img)
            entflechten(img)
            namen = NAMEN_TYP.get(bauen.__name__, STUFEN_NAMEN)
            datei = ziel / ('%d_%s.png' % (stufe, namen[stufe - 1] % kurz))
            img.save(datei)
            mangel = pruefen(img)
            teile = inseln(img)
            if teile != 1:
                mangel.append('%d lose Teile' % (teile - 1))
            print('  %-40s %2dx%-2d %s' % (datei.relative_to(wurzel.parent),
                                          img.width, img.height,
                                          ', '.join(mangel) or 'ok'))
            duel_anpassen(img).save(datei)          # Pruefung auf AAP, Ausgabe in Duel


if __name__ == '__main__':
    main()
