#!/usr/bin/env python3
"""Pixelart-Generator fuer Waffen-Sprites (32x32, Resurrect-64-Palette).

Methode nach github.com/dbinky/claude-fairy-pixel-art: keine Bildgenerierung,
sondern Code, der Pixel setzt - deterministisch, exakte Masse, sauberer
Alphakanal. Gleicher Lauf = gleiches Bild.

STIL: Tonwerte aus resources/weapons/gras_sword.png abgelesen, Formensprache
an den Terraria-Waffen orientiert (terraria.wiki.gg/wiki/Weapons).

  * KEINE eingebackene Kontur - den schwarzen Rand bekommen die Sprites
    spaeter im Spiel. Darum bleibt rundum 1 px frei.
  * Jedes Material laeuft ueber eine Rampe aus sechs Stufen: glanz, kante,
    hell, mitte, dunkel, tief. Die Klinge legt daraus einen Querverlauf von
    der Schneide zum Ruecken an, die Uebergaenge sind gedithert - so bekommt
    eine 5 px breite Klinge drei Tiefenstufen statt einer Flaeche.
  * Jede Waffe hat ihr eigenes Heft. Parierstange, Griff, Knauf und Stein
    sind eigene Bauteile mit eigener Rampe.
  * Fernkampf: aus Kaesten aufgebaut, Lauf nach rechts, Griff unten links -
    passend zu hold_rotation_degrees = -90 in weapon_data.gd.

    python tools/generate_weapons.py            # -> assets/sprites/weapons/
    python tools/generate_weapons.py --out DIR --sheet
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageOps

MARGIN = 1  # bleibt frei, damit der spaetere schwarze Rand hineinpasst
GROESSE = 32  # Richtwert - jede Waffe bringt ihre eigene Leinwand mit

# --- Palette: Resurrect 64 -------------------------------------------------

RES64 = {
    'ink': '2e222f', 'plum': '3e3546', 'mauve': '625565', 'dust': '966c6c',
    'tan': 'ab947a', 'wine': '694f62', 'lilac': '7f708a', 'steel': '9babb2',
    'mint': 'c7dcd0', 'white': 'ffffff',
    'blood_dk': '6e2727', 'blood': 'b33831', 'ember': 'ea4f36', 'flame': 'f57d4a',
    'crimson_dk': 'ae2334', 'crimson': 'e83b3b', 'orange': 'fb6b1d',
    'amber': 'f79617', 'gold': 'f9c22b',
    'maroon': '7a3045', 'rust_dk': '9e4539', 'rust': 'cd683d', 'copper': 'e6904e',
    'sand': 'fbb954',
    'olive_dk': '4c3e24', 'olive': '676633', 'moss': 'a2a947', 'lime': 'd5e04b',
    'pale_yellow': 'fbff86',
    'green_dk': '165a4c', 'green': '239063', 'green_br': '1ebc73',
    'green_lt': '91db69', 'green_pl': 'cddf6c',
    'slate_dk': '313638', 'slate': '374e4a', 'slate_gr': '547e64',
    'sage': '92a984', 'sage_lt': 'b2ba90',
    'teal_dk': '0b5e65', 'teal': '0b8a8f', 'teal_br': '0eaf9b',
    'aqua': '30e1b9', 'aqua_lt': '8ff8e2',
    'navy': '323353', 'indigo': '484a77', 'blue': '4d65b4', 'blue_br': '4d9be6',
    'sky': '8fd3ff',
    'purple_dk': '45293f', 'purple': '6b3e75', 'violet': '905ea9',
    'lavender': 'a884f3', 'pink_pl': 'eaaded',
    'rose_dk': '753c54', 'rose': 'a24b6f', 'pink': 'cf657f', 'pink_lt': 'ed8099',
    'magenta_dk': '831c5d', 'magenta': 'c32454', 'pink_hot': 'f04f78',
    'salmon': 'f68181', 'peach': 'fca790', 'cream': 'fdcbb0',
}


def C(name: str):
    """Palettenfarbe als RGBA. Farben werden ueberall per Name referenziert."""
    h = RES64[name]
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


# --- Zeichenkern -----------------------------------------------------------

def blank(w=GROESSE, h=None) -> Image.Image:
    return Image.new('RGBA', (w, h or w), (0, 0, 0, 0))


def put(img: Image.Image, x: int, y: int, col) -> None:
    """Setzt ein Pixel und haelt den Rand frei."""
    if MARGIN <= x < img.width - MARGIN and MARGIN <= y < img.height - MARGIN:
        img.putpixel((int(x), int(y)), col)


def to_uv(x: int, y: int, ox: int, oy: int):
    """Bildkoordinate -> Klingenkoordinate (u entlang, v quer)."""
    dx, dy = x - ox, y - oy
    return ((dx - dy) / 2.0, (dx + dy) / 2.0)


def to_xy(u: float, v: float, ox: int, oy: int):
    return (int(round(ox + u + v)), int(round(oy - u + v)))


def speck(img, ox, oy, u, v, col):
    """Einzelnes Pixel in Klingenkoordinaten - fuer Rost, Scharten, Glut."""
    x, y = to_xy(u, v, ox, oy)
    put(img, x, y, C(col))


# --- Materialrampen --------------------------------------------------------
# Sechs Stufen von der Lichtkante bis zum tiefsten Schatten. Alles, was
# gezeichnet wird, greift auf diese Stufen zu - dadurch bleiben die Waffen
# untereinander stimmig, obwohl jede ihre eigenen Farben hat.

STUFEN = ('glanz', 'kante', 'hell', 'mitte', 'dunkel', 'tief')


def rampe(glanz, kante, hell, mitte, dunkel, tief):
    return dict(zip(STUFEN, (glanz, kante, hell, mitte, dunkel, tief)))


# Klingenrampen
STAHL = rampe('white', 'lilac', 'mint', 'steel', 'mauve', 'plum')
EISEN = rampe('mint', 'mauve', 'steel', 'lilac', 'plum', 'ink')
KNOCHEN = rampe('white', 'wine', 'cream', 'tan', 'dust', 'purple_dk')
MOND = rampe('aqua_lt', 'blue', 'sky', 'blue_br', 'indigo', 'navy')
STURM = rampe('pale_yellow', 'teal', 'aqua_lt', 'aqua', 'teal_br', 'teal_dk')
FLAMME = rampe('pale_yellow', 'copper', 'sand', 'amber', 'rust', 'maroon')
FANG = rampe('cream', 'rust_dk', 'sand', 'copper', 'rust', 'maroon')
BLUT = rampe('peach', 'crimson_dk', 'salmon', 'crimson', 'blood', 'blood_dk')

# Stufenrampen nach Calamity-Vorbild: dieselbe Form, hoehere Stufe, andere
# Farbwelt. Pre-Hardmode bleibt erdig, Hardmode wird kuehl und metallisch,
# Post-Moon-Lord leuchtet.
KUPFER = rampe('pale_yellow', 'rust_dk', 'sand', 'copper', 'rust', 'maroon')
KOBALT = rampe('aqua_lt', 'indigo', 'sky', 'blue_br', 'blue', 'navy')
ASTRAL = rampe('white', 'violet', 'aqua_lt', 'lavender', 'violet', 'purple_dk')
LEERE = rampe('pink_pl', 'purple_dk', 'lavender', 'violet', 'purple', 'magenta_dk')
ABGRUND = rampe('aqua_lt', 'navy', 'teal_br', 'teal', 'teal_dk', 'ink')

# Heft- und Beschlagrampen
GOLD = rampe('pale_yellow', 'amber', 'sand', 'gold', 'copper', 'rust_dk')
SILBER = rampe('white', 'mauve', 'mint', 'steel', 'lilac', 'plum')
LEDER = rampe('cream', 'wine', 'tan', 'dust', 'wine', 'purple_dk')
DUNKELLEDER = rampe('tan', 'purple_dk', 'dust', 'wine', 'purple_dk', 'ink')
HOLZ = rampe('sand', 'rust_dk', 'copper', 'rust', 'rust_dk', 'maroon')


# --- Klinge ----------------------------------------------------------------

def blade(img, ox, oy, length, half, r, curve_amp=0.0, tip=3.0, serr=None,
          fuller=False):
    """Klinge mit gedithertem Querverlauf von der Schneide zum Ruecken.

    half 0.75 -> 3 px pro Zeile, 1.0 -> 5 px (wie gras_sword), 1.5 -> 7 px.
    Der Verlauf laeuft ueber glanz -> hell -> mitte -> dunkel -> tief, die
    Uebergaenge sind im Schachbrett gedithert wie in der Vorlage.
    """
    hell_parity = (ox + oy + 1) % 2
    leiter = [C(r['glanz']), C(r['hell']), C(r['mitte']), C(r['dunkel']), C(r['tief'])]
    body = max(0.001, length - tip)

    def w_at(u):
        w = half if u <= body else half * (length - u) / tip
        if serr and u < body - 1.0:      # nicht in die Spitze schneiden,
            w += serr(u)                 # sonst haengt sie lose in der Luft
        return w

    def cur(u):
        return curve_amp * (max(0.0, u) / length) ** 2

    for y in range(img.height):
        for x in range(img.width):
            u, v = to_uv(x, y, ox, oy)
            if u < -0.001 or u > length:
                continue
            w = w_at(u)
            vv = v - cur(u)
            if not -w - 0.001 <= vv <= w + 0.001:
                continue

            am_heft = u < 2.5             # Schatten des Hefts auf der Klinge
            an_spitze = u > length - 2.0

            if vv <= -w + 0.25:           # Schneidenlinie
                col = C(r['tief']) if u > length - 1.5 else C(r['kante'])
            elif vv >= w - 0.25 and w >= 0.9:
                col = C(r['tief'])        # Ruecken liegt im Schatten
            elif fuller and w >= 1.25 and abs(vv) <= 0.3 and 1.5 < u < body - 1.0:
                col = C(r['dunkel'])      # Hohlkehle
            else:
                t = (vv + w) / (2.0 * w)  # 0 = Schneide, 1 = Ruecken
                stufe = 0 if t < 0.30 else (1 if t < 0.55 else (2 if t < 0.80 else 3))
                if (x + y) % 2 != hell_parity:
                    stufe += 1            # Dither: jede zweite Lage eine Stufe tiefer
                if am_heft or an_spitze:
                    stufe += 1
                col = leiter[min(stufe, 4)]
            put(img, x, y, col)


def schliff(img, ox, oy, length, half, r, curve_amp=0.0, von=3, bis=None, schritt=2):
    """Hamon: helle Haertelinie dicht an der Schneide."""
    bis = bis if bis is not None else int(length) - 4
    for u in range(von, bis, schritt):
        v = -half + 0.5 + curve_amp * (u / length) ** 2
        speck(img, ox, oy, u, v, r['glanz'])


# --- Heftbauteile ----------------------------------------------------------
# Licht kommt aus -v (oben links): das v_lo-Ende der Parierstange ist hell,
# das v_hi-Ende liegt im Schatten.

def guard(img, ox, oy, u_c, thick, v_lo, v_hi, r,
          flare=0.0, spitze=None, niete=None):
    """Parierstange quer zur Klinge, fuenf Tonstufen entlang ihrer Laenge."""
    spanne = max(0.001, v_hi - v_lo)
    for y in range(img.height):
        for x in range(img.width):
            u, v = to_uv(x, y, ox, oy)
            if not v_lo - 0.001 <= v <= v_hi + 0.001:
                continue
            t = thick
            if flare and (v <= v_lo + 0.75 or v >= v_hi - 0.75):
                t += flare
            if abs(u - u_c) > t + 0.001:
                continue
            f = (v - v_lo) / spanne
            if f < 0.25:
                col = r['hell']
            elif f < 0.55:
                col = r['mitte']
            elif f < 0.82:
                col = r['dunkel']
            else:
                col = r['tief']
            put(img, x, y, C(col))
    if spitze:                                   # dicht am Balken, sonst lose
        speck(img, ox, oy, u_c, v_lo - 0.45, spitze)
        speck(img, ox, oy, u_c, v_hi + 0.45, spitze)
    if niete:
        speck(img, ox, oy, u_c, -0.5, niete)
        speck(img, ox, oy, u_c, 0.5, niete)


def grip(img, ox, oy, u_from, u_to, half, r):
    """Griff: Wicklungsringe entlang der Achse, quer dazu eine Rundung."""
    for y in range(img.height):
        for x in range(img.width):
            u, v = to_uv(x, y, ox, oy)
            if not (u_from - 0.001 <= u <= u_to + 0.001 and abs(v) <= half + 0.001):
                continue
            ring = int(math.floor(u)) % 2 == 0
            if v <= -half + 0.5:
                col = r['hell'] if ring else r['mitte']
            elif v >= half - 0.5:
                col = r['tief']
            else:
                col = r['mitte'] if ring else r['dunkel']
            put(img, x, y, C(col))


def pommel(img, ox, oy, u_c, rad, r):
    """Knauf mit Glanzpunkt, Kernton und Schattenrand."""
    cx, cy = ox + u_c, oy - u_c
    for y in range(img.height):
        for x in range(img.width):
            if math.hypot(x - cx, y - cy) > rad:
                continue
            licht = (x - cx) + (y - cy)
            if licht < -1.2:
                col = r['glanz']
            elif licht < 0.0:
                col = r['hell']
            elif licht < 1.2:
                col = r['mitte']
            else:
                col = r['dunkel']
            put(img, x, y, C(col))


def gem(img, ox, oy, u_c, hell, mitte, dunkel, glanz='white'):
    """Edelstein: Glanzpunkt, Kern, Schattenseite - der Akzent aus der Vorlage."""
    x, y = to_xy(u_c, 0, ox, oy)
    put(img, x, y - 1, C(glanz))
    put(img, x, y, C(hell))
    put(img, x + 1, y, C(mitte))
    put(img, x + 1, y + 1, C(dunkel))


# --- Nahkampf --------------------------------------------------------------
# (ox, oy) ist der Klingenansatz - wie in gras_sword.png bei (11, 20).
# Die Klinge laeuft nach oben rechts, das Heft nach unten links.

OX, OY = 11, 20


def w_sword_melee(img):
    """Kurzschwert, Startwaffe. Gerade Parierstange, Hohlkehle, Niete."""
    blade(img, OX, OY, 15.0, 1.0, STAHL, fuller=True)
    guard(img, OX, OY, -0.8, 0.9, -2.6, 2.6, SILBER, niete='gold')
    grip(img, OX, OY, -4.6, -1.8, 1.0, LEDER)
    pommel(img, OX, OY, -5.4, 1.5, SILBER)


def w_shortsword_bone(img):
    """Knochen-Kurzschwert: Fangzaehne als Parier, Risse in der Klinge."""
    def teeth(u):
        return -0.5 if u > 3.5 and int(math.floor(u)) % 4 == 1 else 0.0

    blade(img, OX, OY, 14.0, 1.0, KNOCHEN, serr=teeth)
    for u, v in ((5.0, 0.0), (5.5, 0.5), (8.0, -0.5), (8.5, 0.0), (11.0, 0.5)):
        speck(img, OX, OY, u, v, KNOCHEN['dunkel'])   # Risse
    guard(img, OX, OY, -0.8, 0.8, -2.0, 2.0, KNOCHEN, spitze='white')
    gem(img, OX, OY, -0.8, 'green_lt', 'green', 'green_dk', glanz='green_pl')
    grip(img, OX, OY, -4.4, -1.8, 1.0, DUNKELLEDER)
    speck(img, OX, OY, -3.0, 0.0, 'sand')            # Wickelring
    pommel(img, OX, OY, -5.2, 1.4, KNOCHEN)


def w_broadsword_iron(img):
    """Eisen-Breitschwert: lange Parierstange, Hohlkehle, blauer Stein."""
    blade(img, OX, OY, 15.5, 1.5, STAHL, tip=4.0, fuller=True)
    guard(img, OX, OY, -1.0, 1.0, -3.6, 3.6, SILBER)
    gem(img, OX, OY, -1.0, 'sky', 'blue_br', 'indigo')
    grip(img, OX, OY, -5.0, -2.2, 1.05, LEDER)
    pommel(img, OX, OY, -5.9, 1.8, SILBER)


def w_broadsword_titan(img):
    """Titanen-Breitschwert: kolossal, Scharten, Rostnarben in zwei Toenen."""
    def chips(u):
        return -0.5 if (4.5 <= u <= 5.5 or 10.5 <= u <= 11.5) else 0.0

    blade(img, OX, OY, 16.0, 2.0, EISEN, tip=4.5, serr=chips, fuller=True)
    for u, v in ((4.0, 1.5), (8.5, 0.5), (12.5, 1.0)):
        speck(img, OX, OY, u, v, 'rust_dk')
        speck(img, OX, OY, u + 0.5, v + 0.5, 'maroon')
    guard(img, OX, OY, -1.2, 1.1, -3.8, 3.8, EISEN, flare=0.4, spitze='rust_dk')
    gem(img, OX, OY, -1.2, 'rust', 'rust_dk', 'maroon', glanz='sand')
    grip(img, OX, OY, -5.4, -2.6, 1.05, DUNKELLEDER)
    pommel(img, OX, OY, -6.2, 1.7, EISEN)


def w_katana_moon(img):
    """Mond-Katana: runde Tsuba, Haertelinie, Runen auf der Klinge."""
    blade(img, OX, OY, 17.0, 1.0, MOND, curve_amp=1.6)
    schliff(img, OX, OY, 17.0, 1.0, MOND, curve_amp=1.6)
    for u in (6.0, 9.0):                                  # Runen
        speck(img, OX, OY, u, 0.5, MOND['glanz'])
    guard(img, OX, OY, -1.0, 0.6, -1.8, 1.8, GOLD)
    grip(img, OX, OY, -6.0, -2.0, 0.85,
         rampe('lavender', 'purple_dk', 'violet', 'purple', 'indigo', 'navy'))
    speck(img, OX, OY, -3.5, 0.0, 'gold')                 # Menuki
    pommel(img, OX, OY, -6.6, 1.2, GOLD)


def w_katana_storm(img):
    """Sturm-Katana: eckige Tsuba, Haertelinie, Funken am Ruecken."""
    blade(img, OX, OY, 17.0, 1.0, STURM, curve_amp=1.4)
    schliff(img, OX, OY, 17.0, 1.0, STURM, curve_amp=1.4, schritt=3)
    for u in (7.0, 11.0):                                 # Funken
        speck(img, OX, OY, u, 0.5, 'pale_yellow')
    guard(img, OX, OY, -1.0, 0.9, -1.5, 1.5, GOLD)
    grip(img, OX, OY, -6.0, -2.2, 0.85,
         rampe('sage_lt', 'slate_dk', 'sage', 'slate_gr', 'slate', 'slate_dk'))
    pommel(img, OX, OY, -6.6, 1.2, SILBER)


def w_greatsword_flame(img):
    """Flammen-Grossschwert: gefluegelte Parierstange, Glut am Ruecken."""
    blade(img, OX, OY, 15.5, 1.5, FLAMME, tip=4.0, fuller=True)
    for u in (3.0, 6.0, 9.0):                             # Feuerzungen
        speck(img, OX, OY, u, 1.5, 'ember')
        speck(img, OX, OY, u + 0.5, 2.0, 'orange')
        speck(img, OX, OY, u + 1.0, 1.5, 'flame')
    guard(img, OX, OY, -1.0, 0.9, -3.4, 3.4, GOLD, flare=1.0)
    gem(img, OX, OY, -1.0, 'ember', 'crimson', 'blood_dk', glanz='sand')
    grip(img, OX, OY, -5.0, -2.2, 0.9,
         rampe('rose', 'blood_dk', 'maroon', 'blood_dk', 'purple_dk', 'ink'))
    pommel(img, OX, OY, -5.9, 1.7, GOLD)


def w_curved_fang(img):
    """Krummschwert Fang: einseitige Parierstange, Knochenzaehne."""
    def teeth(u):
        return -0.5 if u > 4.0 and int(math.floor(u)) % 3 == 0 else 0.0

    blade(img, OX, OY, 15.0, 1.5, FANG, curve_amp=2.2, tip=4.0, serr=teeth)
    for u in (6.0, 9.0, 12.0):                            # Zahnspitzen
        v = -1.5 + 2.2 * (u / 15.0) ** 2
        speck(img, OX, OY, u, v, 'cream')
    guard(img, OX, OY, -1.0, 0.9, -1.6, 3.4, HOLZ, spitze='cream')
    grip(img, OX, OY, -5.0, -2.2, 1.05, DUNKELLEDER)
    pommel(img, OX, OY, -5.9, 1.6, KNOCHEN)


def w_dagger_bleed(img):
    """Blutdolch: Blutrinne in der Klinge, kleiner Stein im Parier."""
    ROSA = rampe('pink_lt', 'maroon', 'pink', 'rose', 'maroon', 'purple_dk')
    blade(img, OX, OY, 9.0, 1.0, BLUT, curve_amp=1.0, tip=2.5)
    for u in (3.0, 5.0, 7.0):                             # Blutrinne
        speck(img, OX, OY, u, 0.1 + 1.0 * (u / 9.0) ** 2, BLUT['tief'])
    guard(img, OX, OY, -0.8, 0.8, -1.8, 1.8, ROSA)
    gem(img, OX, OY, -0.8, 'crimson', 'blood', 'blood_dk', glanz='salmon')
    grip(img, OX, OY, -3.8, -1.8, 0.8, DUNKELLEDER)
    pommel(img, OX, OY, -4.5, 1.3, ROSA)


def w_dagger_gold(img):
    """Gnadendolch: schmaler Stich, goldene Parierstange mit Dornen."""
    blade(img, OX, OY, 11.0, 0.75, STAHL, tip=2.5)
    guard(img, OX, OY, -0.8, 0.8, -2.4, 2.4, GOLD, spitze='pale_yellow')
    grip(img, OX, OY, -4.0, -1.8, 0.8, LEDER)
    pommel(img, OX, OY, -4.8, 1.4, GOLD)


# --- Fernkampf -------------------------------------------------------------
# Aus Kaesten aufgebaut: Lauf nach rechts, Griff unten links.
# Licht wie beim Nahkampf von oben links - obere Zeile hell, untere tief.

def box(img, x0, y0, w, h, r):
    """Waagerechter Block ueber vier Tonstufen plus Lichtpunkte oben."""
    for j in range(h):
        if j == 0:
            col = r['hell']
        elif j == h - 1:
            col = r['tief']
        elif j == h - 2 and h >= 3:
            col = r['dunkel']
        else:
            col = r['mitte']
        for i in range(w):
            put(img, x0 + i, y0 + j, C(col))
    for i in (1, 2):                         # ein kurzer Lichtreflex, keine
        if i < w:                            # gestrichelte Linie ueber den Lauf
            put(img, x0 + i, y0, C(r['glanz']))


def slant(img, x0, y0, w, h, drift, r):
    """Schraeg nach unten links laufender Block - Griff oder Schaft."""
    for j in range(h):
        sx = x0 + int(round(drift * j))
        for i in range(w):
            if i == 0:
                col = r['hell']
            elif i == w - 1:
                col = r['tief']
            elif i == w - 2:
                col = r['dunkel']
            else:
                col = r['mitte']
            put(img, sx + i, y0 + j, C(col))


def w_revolver(img):
    """Revolver: kurzer Lauf, ausgestellte Trommel, Holzgriff mit Maserung."""
    slant(img, 9, 17, 4, 6, -0.5, LEDER)                # Griff
    box(img, 7, 12, 8, 5, SILBER)                       # Rahmen
    box(img, 14, 13, 12, 3, SILBER)                     # Lauf
    box(img, 7, 14, 6, 5, SILBER)                       # Trommel
    for x in (8, 11):                                   # Trommelzuege
        for y in (15, 16, 17):
            put(img, x, y, C('gold' if y < 17 else 'copper'))
    put(img, 6, 11, C('lilac'))                         # Hahn
    put(img, 6, 12, C('mauve'))
    put(img, 25, 12, C('gold'))                         # Korn
    put(img, 25, 14, C('plum'))                         # Muendung
    put(img, 13, 12, C('sand'))                         # Schraube
    put(img, 9, 18, C('dust'))                          # Maserung im Griff
    put(img, 8, 19, C('dust'))
    put(img, 14, 17, C('mauve'))                        # Abzugsbuegel
    put(img, 15, 18, C('mauve'))
    put(img, 14, 18, C('plum'))


def w_shotgun_boom(img):
    """Schrotflinte: doppelter Lauf, Messingband, schwerer Holzschaft."""
    slant(img, 3, 13, 7, 6, -0.3, HOLZ)                 # Schaft
    box(img, 10, 11, 4, 7, SILBER)                      # Verschluss
    box(img, 13, 11, 14, 3, SILBER)                     # oberer Lauf
    box(img, 13, 15, 14, 3, SILBER)                     # unterer Lauf
    for y in (11, 12, 13):                              # Messingband
        put(img, 12, y, C('sand' if y < 13 else 'amber'))
    put(img, 26, 10, C('gold'))                         # Korn
    put(img, 26, 12, C('plum'))                         # Muendungen
    put(img, 26, 16, C('plum'))
    put(img, 11, 18, C('mauve'))                        # Abzug
    for x in (5, 7):                                    # Maserung im Schaft
        put(img, x, 16, C('maroon'))


def w_smg_buzz(img):
    """MP: kastiger Verschluss, langes Magazin, Schulterstuetze."""
    stahl_gruen = rampe('sage_lt', 'slate_dk', 'sage', 'slate_gr', 'slate', 'slate_dk')
    gruen = rampe('moss', 'ink', 'olive', 'olive_dk', 'ink', 'ink')
    box(img, 10, 17, 4, 7, gruen)                       # Magazin
    box(img, 3, 12, 4, 4, gruen)                        # Schulterstuetze
    box(img, 6, 11, 13, 6, stahl_gruen)                 # Verschluss
    box(img, 19, 12, 8, 3, stahl_gruen)                 # Lauf
    box(img, 15, 17, 3, 4, stahl_gruen)                 # Pistolengriff
    put(img, 26, 11, C('lime'))                         # Korn
    put(img, 26, 13, C('ink'))                          # Muendung
    put(img, 15, 11, C('lime'))                         # Visier
    for x in (7, 8):                                    # Ladehebel
        put(img, x, 12, C('lime'))
    for y in (18, 20, 22):                              # Magazinrippen
        put(img, 11, y, C('moss'))


def w_bow_hunter(img):
    """Jagdbogen: Holzbogen mit Sehne, senkrecht wie in Terraria."""
    x0, y0, hoehe, bauch = 9, 3, 26, 5
    for i in range(hoehe):
        t = i / (hoehe - 1.0)
        bogen = bauch * math.sin(math.pi * t)
        x = x0 + int(round(bogen))
        put(img, x0, y0 + i, C('mint'))                 # Sehne
        if bogen >= 0.5:
            put(img, x, y0 + i, C('sand' if i % 3 else 'tan'))
            put(img, x + 1, y0 + i, C('rust_dk' if i % 3 else 'olive_dk'))
        if i in (0, hoehe - 1):
            put(img, x, y0 + i, C('gold'))              # Wurfarmspitzen
    mitte = y0 + hoehe // 2
    for dy in (-2, -1, 0, 1, 2):                        # Griffwicklung
        put(img, x0 + bauch, mitte + dy, C('maroon' if dy % 2 else 'blood'))
        put(img, x0 + bauch + 1, mitte + dy, C('blood_dk'))


# --- Stangenwaffen ---------------------------------------------------------
# Calamity teilt den Nahkampf in Breitschwerter, Kurzschwerter, Speere,
# Flegel, Sensen und Wurfwaffen auf. Die brauchen mehr Platz als 32x32,
# deshalb bringt jede Waffe unten ihre eigene Leinwand mit.

def stange(img, ox, oy, u_from, u_to, half, r, ringe=(), v_c=0.0):
    """Schaft entlang der Diagonale: hell oben links, tief unten rechts."""
    for y in range(img.height):
        for x in range(img.width):
            u, v = to_uv(x, y, ox, oy)
            vv = v - v_c
            if not (u_from - 0.001 <= u <= u_to + 0.001 and abs(vv) <= half + 0.001):
                continue
            if vv <= -half + 0.5:
                col = r['hell']
            elif vv >= half - 0.5:
                col = r['tief']
            else:
                col = r['mitte']
            put(img, x, y, C(col))
    for u in ringe:                       # Beschlagringe
        for v in (-half, 0.0, half):
            speck(img, ox, oy, u, v + v_c, r['glanz'] if v < 0 else r['dunkel'])


def kette(img, ox, oy, u_from, u_to, r):
    """Kettenglieder zwischen Griff und Kugel."""
    u = u_from
    hell = True
    while u <= u_to:
        speck(img, ox, oy, u, -0.3, r['hell'] if hell else r['mitte'])
        speck(img, ox, oy, u + 0.6, 0.3, r['dunkel'])
        u += 0.9                          # Glieder beruehren sich
        hell = not hell


def kugel(img, cx, cy, rad, r, dornen=()):
    """Flegelkopf: runde Masse mit Lichtseite, dazu Dornen."""
    for y in range(img.height):
        for x in range(img.width):
            d = math.hypot(x - cx, y - cy)
            if d > rad:
                continue
            licht = (x - cx) + (y - cy)
            if licht < -rad * 0.7:
                col = r['glanz']
            elif licht < -rad * 0.15:
                col = r['hell']
            elif licht < rad * 0.5:
                col = r['mitte']
            elif licht < rad * 0.9:
                col = r['dunkel']
            else:
                col = r['tief']
            put(img, x, y, C(col))
    for dx, dy in dornen:
        put(img, cx + dx, cy + dy, C(r['hell'] if dx + dy < 0 else r['dunkel']))


def balken(img, x0, y0, x1, y1, dicke, r, kappe=None):
    """Dicker Strich zwischen zwei Punkten, quer schattiert.

    Die allgemeinste Form im Werkzeugkasten: taugt fuer Bumerangarme,
    Stielhaelften, Hammerkoepfe - alles, was nicht auf der Klingendiagonale
    liegt. Licht faellt wie ueberall von oben links.
    """
    dx, dy = x1 - x0, y1 - y0
    laenge2 = max(1e-6, dx * dx + dy * dy)
    for y in range(img.height):
        for x in range(img.width):
            t = ((x - x0) * dx + (y - y0) * dy) / laenge2
            t = min(1.0, max(0.0, t))
            px, py = x0 + t * dx, y0 + t * dy
            if math.hypot(x - px, y - py) > dicke:
                continue
            licht = ((x - px) + (y - py)) / max(dicke, 0.5)
            if licht < -0.85:
                col = r['glanz']
            elif licht < -0.30:
                col = r['hell']
            elif licht < 0.30:
                col = r['mitte']
            elif licht < 0.80:
                col = r['dunkel']
            else:
                col = r['tief']
            put(img, x, y, C(col))
    if kappe:
        for cx, cy in ((x0, y0), (x1, y1)):
            put(img, int(round(cx)), int(round(cy)), C(kappe))


def sichel(img, cx, cy, radius, grad_von, grad_bis, dicke, r, schwund=0.8):
    """Sichelblatt: Ring zwischen zwei Boegen, der zur Spitze hin auslaeuft.

    Die Aussenseite ist der Ruecken, die Innenseite die geschliffene Schneide -
    daher liegt der hellste Ton innen. Fuer Sensen, Sicheln und Krummklingen.
    """
    a_von, a_bis = math.radians(grad_von), math.radians(grad_bis)
    spanne = max(1e-6, a_bis - a_von)
    for y in range(img.height):
        for x in range(img.width):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            if d > radius + 0.5 or d < radius - dicke - 0.5:
                continue
            a = math.atan2(-dy, dx)
            if a < a_von - 0.02:
                a += 2 * math.pi
            if not (a_von - 0.02 <= a <= a_bis + 0.02):
                continue
            t = (a - a_von) / spanne
            dk = dicke * max(0.0, 1.0 - t) ** schwund
            if dk < 0.6 or d < radius - dk:
                continue
            f = (radius - d) / max(dk, 0.001)   # 0 = Ruecken, 1 = Schneide
            if f < 0.18:
                col = r['kante']
            elif f < 0.45:
                col = r['dunkel']
            elif f < 0.70:
                col = r['mitte']
            elif f < 0.88:
                col = r['hell']
            else:
                col = r['glanz']
            put(img, x, y, C(col))


def schnur(img, punkte, r, dick_von=2.0, dick_bis=0.6, dornen=None):
    """Zug aus Stuetzpunkten, der zum Ende hin duenner wird.

    Fuer Peitschen, Ketten und Schnuere: zwischen je zwei Punkten liegt ein
    balken(), dessen Dicke ueber den Verlauf abnimmt.
    """
    n = max(1, len(punkte) - 1)
    for i in range(n):
        (x0, y0), (x1, y1) = punkte[i], punkte[i + 1]
        t = i / n
        balken(img, x0, y0, x1, y1, dick_von + (dick_bis - dick_von) * t, r)
    if dornen:
        for i in range(1, n):
            x, y = punkte[i]
            put(img, x, y - 2, C(dornen))


def ring(img, cx, cy, aussen, innen, r):
    """Kreisring mit Lichtseite oben links - fuer Wurfringe und Beschlaege."""
    for y in range(img.height):
        for x in range(img.width):
            d = math.hypot(x - cx, y - cy)
            if not (innen <= d <= aussen):
                continue
            licht = ((x - cx) + (y - cy)) / max(aussen, 1.0)
            if licht < -0.75:
                col = r['glanz']
            elif licht < -0.25:
                col = r['hell']
            elif licht < 0.25:
                col = r['mitte']
            elif licht < 0.70:
                col = r['dunkel']
            else:
                col = r['tief']
            put(img, x, y, C(col))


def platte_halb(breite, hoehe, j, spitz=2.4):
    """Halbbreite der Schildplatte in Zeile j - Beschlaege muessen sie
    kennen, sonst haengen sie neben der Platte in der Luft.
    """
    t = j / max(1.0, hoehe - 1.0)
    halb = (breite / 2.0) * (1.0 - t ** spitz)
    return halb * 0.8 if j == 0 else halb


def platte(img, cx, y0, breite, hoehe, r, spitz=2.4):
    """Schildplatte: oben breit und gerade, unten auf eine Spitze zulaufend.

    spitz steuert, wie schnell die Flanken einlaufen - kleine Werte geben
    ein Rundschild, grosse ein schlankes Reiterschild.
    """
    for j in range(hoehe):
        halb = platte_halb(breite, hoehe, j, spitz)
        for i in range(-int(halb), int(halb) + 1):
            x, y = cx + i, y0 + j
            rand = abs(i) >= halb - 1.0
            if rand:
                col = r['dunkel'] if i < 0 else r['tief']
            elif i + j * 0.6 < -halb * 0.35:
                col = r['hell']
            elif i + j * 0.6 < halb * 0.35:
                col = r['mitte']
            else:
                col = r['dunkel']
            put(img, x, y, C(col))


def kristall(img, cx, cy, rad, r, zacken=True):
    """Geschliffener Kristall: Raute mit Facetten, heller Kern, Zacken.

    Die Zacken haengen am Koerper, damit der spaetere schwarze Rand die ganze
    Form umschliesst statt einzelne Punkte zu umkringeln.
    """
    for y in range(img.height):
        for x in range(img.width):
            d = abs(x - cx) + abs(y - cy)          # Rautenabstand
            if d > rad:
                continue
            licht = (x - cx) + (y - cy)
            if d <= 1:
                col = r['glanz']
            elif licht < -rad * 0.45:
                col = r['hell']
            elif licht < rad * 0.1:
                col = r['mitte']
            elif licht < rad * 0.6:
                col = r['dunkel']
            else:
                col = r['tief']
            put(img, x, y, C(col))
    if zacken:
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            for i in (rad, rad + 1):
                put(img, cx + dx * i, cy + dy * i,
                    C(r['hell'] if dx + dy < 0 else r['dunkel']))


def buch(img, x0, y0, breite, hoehe, deckel, seiten):
    """Geschlossenes Buch: Deckel, Ruecken links, Schnitt rechts."""
    for j in range(hoehe):
        for i in range(breite):
            x, y = x0 + i, y0 + j
            if i < 2:                              # Ruecken
                col = deckel['dunkel'] if i else deckel['tief']
            elif i >= breite - 3:                  # Blattschnitt
                col = seiten['hell'] if (j % 2) else seiten['mitte']
            elif j == 0:
                col = deckel['hell']
            elif j == hoehe - 1:
                col = deckel['tief']
            elif j == hoehe - 2:
                col = deckel['dunkel']
            else:
                col = deckel['mitte']
            put(img, x, y, C(col))
    for i in (2, breite - 4):                      # Beschlagecken
        for j in (1, hoehe - 2):
            put(img, x0 + i, y0 + j, C('gold'))


def gedreht(img, zeichnen):
    """Zeichnet ein Bauteil und dreht es um 180 Grad - fuer Doppelklingen,
    deren zweite Haelfte nach unten links zeigt."""
    tmp = blank(img.width, img.height)
    zeichnen(tmp)
    img.alpha_composite(tmp.transpose(Image.ROTATE_180))


def gespiegelt(img, zeichnen):
    """Zeichnet ein Bauteil und klappt es waagerecht - fuer nach links
    ausholende Formen wie das Sensenblatt."""
    tmp = blank(img.width, img.height)
    zeichnen(tmp)
    img.alpha_composite(ImageOps.mirror(tmp))


def w_spear_brim(img):
    """Speer: langer Schaft mit Beschlagringen, schmales Blatt. 40x40."""
    ox, oy = 5, 35
    stange(img, ox, oy, 0.0, 21.0, 0.75, HOLZ, ringe=(4.0, 12.0, 19.5))
    bx, by = to_xy(21.0, 0.0, ox, oy)
    guard(img, bx, by, 0.0, 0.8, -1.8, 1.8, GOLD)          # Tuelle
    blade(img, bx, by, 8.5, 1.1, STAHL, tip=4.5)
    pommel(img, ox, oy, -1.2, 1.4, GOLD)                   # Schaftende


def w_flail_nebula(img):
    """Flegel: Griff, Kette, gedornte Kugel. 40x40."""
    ox, oy = 6, 34
    grip(img, ox, oy, 0.0, 5.0, 0.85, DUNKELLEDER)
    pommel(img, ox, oy, -0.8, 1.4, EISEN)
    kette(img, ox, oy, 4.0, 18.0, EISEN)   # bis in die Kugel hinein
    kx, ky = to_xy(20.0, 0.0, ox, oy)
    kugel(img, kx, ky, 3.6, EISEN,
          dornen=((-4, 0), (-5, 0), (4, 0), (5, 0), (0, -4), (0, -5),
                  (0, 4), (0, 5), (-3, -3), (3, 3)))
    speck(img, ox, oy, 20.0, -0.8, 'violet')               # Kernglut
    speck(img, ox, oy, 20.4, -0.3, 'lavender')


def w_scythe_harvest(img):
    """Sense: langer Schaft, weit ausholendes Blatt nach links. 44x44."""
    ox, oy = 6, 38
    stange(img, ox, oy, 0.0, 20.0, 0.75, DUNKELLEDER, ringe=(6.0, 14.0))
    bx, by = to_xy(20.0, 0.0, ox, oy)
    guard(img, bx, by, 0.0, 0.9, -1.6, 1.6, EISEN)         # Blattschuh
    sichel(img, bx - 11, by + 1, 11.5, -8, 118, 4.2, FANG)
    pommel(img, ox, oy, -1.2, 1.5, EISEN)


# --- Rogue-Klasse ----------------------------------------------------------
# Calamitys eigene Klasse: Wurfdolche, Bumerangs, Stachelbaelle, Wurfspiesse.
# Kleine, schnelle Formen - die duerfen ruhig auf kleinere Leinwaende.

def w_dagger_throw(img):
    """Wurfdolch: klein, schmal, roter Stein im Parier. 24x24."""
    schwert(img, 7, 16, 10.0, 0.75, STAHL, GOLD, wicklung=DUNKELLEDER,
            stein=BLUT, stufe=1, tip=3.0)


def w_boomerang_wood(img):
    """Bumerang: zwei Holzarme, Lederwicklung am Knick, Metallkappen. 32x32."""
    balken(img, 23, 15, 9, 6, 2.2, HOLZ)
    balken(img, 23, 15, 9, 25, 2.2, HOLZ)
    balken(img, 22, 15, 24, 16, 2.4, HOLZ)
    for x, y in ((14, 10), (17, 12), (14, 20), (17, 18)):
        put(img, x, y, C('maroon'))                  # Maserung laengs der Arme
    for dy in (-2, -1, 0, 1, 2):                     # Wicklung am Knick
        put(img, 21 + abs(dy) // 2, 15 + dy, C('wine' if dy % 2 else 'dust'))
    for x, y in ((9, 6), (9, 25)):                   # Metallkappen
        put(img, x, y, C('mint'))
        put(img, x + 1, y, C('steel'))


def w_spiky_ball(img):
    """Stachelball: kompakte Wurfmasse mit Naht. 22x22."""
    wurfwaffe(img, 'ball', EISEN, KUPFER, stufe=0, groesse=4.4)


def w_javelin_bone(img):
    """Wurfspiess: schlanker Knochenschaft, Widerhaken am Kopf. 40x40."""
    ox, oy = 5, 34
    stange(img, ox, oy, 0.0, 19.0, 0.6, KNOCHEN, ringe=(6.0, 13.0))
    bx, by = to_xy(19.0, 0.0, ox, oy)
    guard(img, bx, by, 0.0, 0.7, -1.3, 1.3, GOLD)   # Tuelle setzt den Kopf ab
    blade(img, bx, by, 9.0, 1.0, SILBER, tip=5.0)
    speck(img, bx, by, 2.0, -1.6, 'cream')          # Widerhaken
    speck(img, bx, by, 2.6, -1.2, 'tan')
    speck(img, bx, by, 1.6, 1.6, 'wine')
    pommel(img, ox, oy, -1.0, 1.1, KNOCHEN)


# --- Schwere Formen --------------------------------------------------------
# Axt, Hammer, Doppelklinge und Katar sind keine Diagonalklingen mehr - sie
# leben von balken(), sichel() und den gedrehten Bauteilen.

def w_axe_battle(img):
    """Streitaxt: Schaft mit Beschlag, breites Blatt am Kopf. 40x40."""
    ox, oy = 7, 34
    stange(img, ox, oy, 0.0, 20.0, 0.8, HOLZ, ringe=(5.0, 12.0))
    tx, ty = to_xy(20.0, 0.0, ox, oy)
    balken(img, tx - 1, ty + 1, tx + 2, ty - 2, 2.0, EISEN)      # Auge
    sichel(img, tx - 4, ty + 4, 10.0, -34, 84, 5.6, STAHL, schwund=0.0)
    speck(img, ox, oy, 20.0, -1.4, 'sand')                       # Nietkopf
    pommel(img, ox, oy, -1.0, 1.4, EISEN)


def w_hammer_war(img):
    """Kriegshammer: klobiger Kopf quer zum Schaft, Nieten. 40x40."""
    ox, oy = 7, 34
    stange(img, ox, oy, 0.0, 19.0, 0.85, DUNKELLEDER, ringe=(6.0, 13.0))
    tx, ty = to_xy(19.5, 0.0, ox, oy)
    balken(img, tx - 5, ty - 5, tx + 5, ty + 5, 4.0, EISEN)      # Kopf
    balken(img, tx - 6, ty - 6, tx - 4, ty - 4, 3.2, STAHL)      # Schlagflaeche
    for dv in (-3.5, 3.5):                                       # Nieten
        speck(img, tx, ty, 0.0, dv, 'sand')
    pommel(img, ox, oy, -1.0, 1.5, EISEN)


def w_twinblade(img):
    """Doppelklinge: zwei Klingen an einem Griff, zweite um 180 Grad gedreht. 40x40."""
    ox, oy = 20, 20
    blade(img, ox, oy, 13.0, 1.0, MOND, tip=4.0)
    gedreht(img, lambda t: blade(t, t.width - 1 - ox, t.height - 1 - oy,
                                 13.0, 1.0, MOND, tip=4.0))
    guard(img, ox, oy, -0.8, 0.9, -2.4, 2.4, GOLD)
    gedreht(img, lambda t: guard(t, t.width - 1 - ox, t.height - 1 - oy,
                                 -0.8, 0.9, -2.4, 2.4, GOLD))
    grip(img, ox, oy, -3.6, -1.6, 1.0, DUNKELLEDER)
    speck(img, ox, oy, -2.6, 0.0, 'violet')                      # Griffstein


def w_katar(img):
    """Katar: Stossklinge, zwei Holme, Quergriff dazwischen. 34x34."""
    ox, oy = 13, 22
    blade(img, ox, oy, 13.0, 1.2, STAHL, tip=5.0)
    guard(img, ox, oy, -1.0, 0.9, -2.6, 2.6, EISEN)          # Klingenschuh
    for v in (-2.4, 2.4):                                     # Holme
        stange(img, ox, oy, -8.0, -1.5, 0.5, EISEN, v_c=v)
    guard(img, ox, oy, -5.0, 0.9, -2.4, 2.4, LEDER)           # Quergriff
    guard(img, ox, oy, -8.2, 0.5, -2.6, 2.6, EISEN)           # Abschlussbuegel
    speck(img, ox, oy, -5.0, 0.0, 'gold')                     # Nietkopf


# --- Magie -----------------------------------------------------------------
# Calamity trennt Zauberstaebe, Magiepistolen, Zauberbuecher und Stabwaffen.
# Gemeinsamer Nenner: ein leuchtender Kern, der Rest ist Fassung.

def w_wand_spark(img):
    """Zauberstab: schlanker Schaft, gefasster Kristall. 32x32."""
    ox, oy = 8, 24
    stange(img, ox, oy, 0.0, 14.0, 0.6, DUNKELLEDER, ringe=(4.0,))
    kx, ky = to_xy(15.0, 0.0, ox, oy)
    guard(img, ox, oy, 14.2, 0.7, -1.4, 1.4, GOLD)           # Fassung
    kristall(img, kx + 1, ky - 1, 3, MOND)
    pommel(img, ox, oy, -0.8, 1.1, GOLD)


def w_tome_flames(img):
    """Zauberbuch: Deckel mit Beschlag, Blattschnitt, Glutstein. 30x30."""
    buch(img, 6, 6, 18, 19, rampe('rose', 'purple_dk', 'maroon', 'blood_dk',
                                  'purple_dk', 'ink'), KNOCHEN)
    kristall(img, 13, 15, 3, FLAMME, zacken=False)
    for y in (9, 21):                                        # Schliessbaender
        for x in range(8, 19):
            put(img, x, y, C('gold' if x % 3 else 'amber'))


def w_staff_crystal(img):
    """Kristallstab: langer Schaft, Krallenfassung, grosser Kern. 44x44."""
    ox, oy = 7, 37
    stange(img, ox, oy, 0.0, 22.0, 0.8, HOLZ, ringe=(6.0, 14.0))
    kx, ky = to_xy(26.0, 0.0, ox, oy)
    for v in (-2.2, 2.2):                                    # Krallen
        stange(img, ox, oy, 21.5, 25.0, 0.5, GOLD, v_c=v)
    guard(img, ox, oy, 22.0, 0.8, -2.4, 2.4, GOLD)
    kristall(img, kx, ky, 4, STURM)
    pommel(img, ox, oy, -1.0, 1.4, GOLD)


def w_magic_gun(img):
    """Magiepistole: wie ein Revolver gebaut, aber mit Kristallkammer
    statt Trommel - so bleibt die Silhouette lesbar. 32x32."""
    slant(img, 9, 18, 4, 6, -0.5, DUNKELLEDER)               # Griff
    box(img, 6, 12, 10, 5, GOLD)                             # Gehaeuse
    box(img, 16, 13, 10, 3, SILBER)                          # Lauf
    kristall(img, 10, 18, 3, MOND, zacken=False)             # Kammer unter dem Lauf
    put(img, 10, 15, C('sky'))                               # Kammerlicht
    put(img, 25, 12, C('sky'))                               # Muendungsfunken
    put(img, 25, 16, C('blue_br'))
    put(img, 5, 12, C('amber'))                              # Hahn
    put(img, 15, 18, C('rust_dk'))                           # Abzugsbuegel
    put(img, 14, 18, C('copper'))


def bogenarm(img, x0, y0, hoehe, bauch, r, sehne=None):
    """Wurfarm als Sinusbogen, wahlweise mit Sehne auf der Sehnenlinie."""
    for i in range(hoehe):
        t = i / (hoehe - 1.0)
        aus = bauch * math.sin(math.pi * t)
        x = x0 + int(round(aus))
        if sehne:
            put(img, x0, y0 + i, C(sehne))
        if aus >= 0.5:
            put(img, x, y0 + i, C(r['hell']))
            put(img, x + 1, y0 + i, C(r['dunkel']))
        if i in (0, hoehe - 1):
            put(img, x, y0 + i, C(r['glanz']))


def w_crossbow_repeater(img):
    """Armbrust: waagerechter Schaft, Wurfarme vorn, aufgelegter Bolzen. 36x36."""
    slant(img, 9, 20, 4, 7, -0.4, DUNKELLEDER)              # Griff
    box(img, 4, 16, 21, 4, HOLZ)                            # Schaft
    box(img, 20, 15, 4, 6, EISEN)                           # Buegelfassung
    bogenarm(img, 22, 5, 26, 5, HOLZ, sehne='mint')         # Wurfarme
    box(img, 8, 17, 16, 2, SILBER)                          # Bolzen auf dem Schaft
    put(img, 24, 17, C('sand'))                             # Bolzenspitze
    put(img, 25, 18, C('copper'))
    put(img, 12, 21, C('mauve'))                            # Abzug
    put(img, 5, 15, C('sand'))                              # Kolbenbeschlag


def w_launcher_rocket(img):
    """Raketenwerfer: dickes Rohr, Visier oben, Gefechtskopf vorn. 36x36."""
    slant(img, 11, 20, 4, 7, -0.4, DUNKELLEDER)             # Griff
    box(img, 3, 14, 27, 6, EISEN)                           # Rohr
    box(img, 28, 13, 4, 8, SILBER)                          # Muendungstrichter
    box(img, 2, 15, 3, 4, SILBER)                           # Schubduese hinten
    box(img, 13, 10, 6, 4, EISEN)                           # Visier
    put(img, 15, 11, C('lime'))                             # Optik
    put(img, 16, 11, C('green_lt'))
    for j, br in ((0, 1), (1, 2), (2, 3), (3, 2), (4, 1)):  # Gefechtskopf als Kegel
        for i in range(br):
            put(img, 32 + i, 14 + j, C('crimson' if i else 'salmon'))
    put(img, 34, 16, C('blood_dk'))
    put(img, 14, 20, C('mauve'))                            # Abzug
    for x in (8, 22):                                       # Nietreihen
        for y in (15, 19):
            put(img, x, y, C('sand'))


def w_flamethrower(img):
    """Flammenwerfer: Tank hinten, Schlauch, Duese mit Zuendflamme. 36x36."""
    slant(img, 14, 20, 4, 7, -0.4, DUNKELLEDER)             # Griff
    box(img, 4, 12, 7, 11, rampe('sage_lt', 'ink', 'olive', 'olive_dk', 'ink', 'ink'))
    for y in range(13, 22):                                 # Rundung des Tanks
        put(img, 3, y, C('olive_dk'))
        put(img, 11, y, C('ink'))
    box(img, 11, 16, 13, 5, EISEN)                          # Gehaeuse
    box(img, 24, 17, 7, 3, SILBER)                          # Lauf
    box(img, 30, 16, 2, 5, GOLD)                            # Duese
    for x in range(9, 13):                                  # Schlauch
        put(img, x, 14, C('maroon'))
        put(img, x, 15, C('blood_dk'))
    for y in (15, 19):                                      # Tankbaender
        for x in range(4, 11):
            put(img, x, y, C('moss'))
    put(img, 7, 11, C('sand'))                              # Ventil
    put(img, 8, 11, C('copper'))
    for x, y, col in ((32, 16, 'ember'), (32, 17, 'orange'), (32, 18, 'ember'),
                      (33, 17, 'flame'), (33, 18, 'orange'), (34, 17, 'sand')):
        put(img, x, y, C(col))                              # Zuendflamme
    put(img, 17, 20, C('mauve'))                            # Abzug


# --- Beschwoerung und Sonderformen -----------------------------------------

def w_summon_totem(img):
    """Beschwoerungsstab: gegabelter Kopf, gefasste Kugel, Runen. 44x44."""
    ox, oy = 8, 37
    stange(img, ox, oy, 0.0, 22.0, 0.8, DUNKELLEDER, ringe=(6.0, 14.0))
    for v in (-2.4, 2.4):                                    # Gabelzinken
        stange(img, ox, oy, 21.0, 26.0, 0.55, GOLD, v_c=v)
    guard(img, ox, oy, 21.5, 0.8, -2.6, 2.6, GOLD)
    kx, ky = to_xy(25.5, 0.0, ox, oy)
    kugel(img, kx, ky, 3.4, rampe('aqua_lt', 'teal_dk', 'aqua', 'teal_br',
                                  'teal', 'teal_dk'))
    for u in (8.0, 12.0, 16.0):                              # Runen im Schaft
        speck(img, ox, oy, u, 0.0, 'aqua')
    pommel(img, ox, oy, -1.0, 1.4, GOLD)


def w_whip_thorn(img):
    """Dornenpeitsche: Griff unten links, auslaufender Riemen. 40x40."""
    ox, oy = 6, 33
    grip(img, ox, oy, 0.0, 5.5, 1.0, LEDER)
    pommel(img, ox, oy, -0.8, 1.3, GOLD)
    guard(img, ox, oy, 6.0, 0.7, -1.4, 1.4, GOLD)
    schnur(img, [(14, 25), (20, 22), (26, 21), (31, 16), (34, 9), (32, 4)],
           rampe('rose', 'purple_dk', 'maroon', 'blood_dk', 'purple_dk', 'ink'),
           dick_von=1.8, dick_bis=0.6, dornen='sand')


def w_yoyo_disc(img):
    """Yoyo: Scheibe an der Schnur, Fingerschlaufe oben links. 32x32."""
    schnur(img, [(10, 8), (14, 13), (18, 17)],
           rampe('mint', 'mauve', 'steel', 'lilac', 'mauve', 'plum'),
           dick_von=0.6, dick_bis=0.6)
    kugel(img, 20, 20, 5.2, rampe('sky', 'navy', 'blue_br', 'blue',
                                  'indigo', 'navy'))
    kristall(img, 20, 20, 2, GOLD, zacken=False)             # Achse
    for x, y in ((9, 6), (10, 6), (9, 7), (10, 7)):          # Schlaufe
        put(img, x, y, C('tan'))


def w_greataxe(img):
    """Grossaxt: zwei Blaetter quer zum Schaft, schweres Auge. 44x44.

    Beide Blaetter sind Sicheln um dasselbe Auge, ihre Mittelpunkte liegen
    spiegelbildlich quer zur Schaftachse - sonst wachsen sie auf derselben
    Seite zusammen und das Ganze liest sich als Falter.
    """
    ox, oy = 8, 38
    stange(img, ox, oy, 0.0, 19.0, 0.9, HOLZ, ringe=(6.0, 13.0))
    tx, ty = to_xy(19.0, 0.0, ox, oy)
    balken(img, tx - 2, ty + 2, tx + 2, ty - 2, 2.6, EISEN)   # Auge
    sichel(img, tx - 6, ty - 6, 9.5, -100, 10, 4.4, STAHL, schwund=0.0)
    sichel(img, tx + 6, ty + 6, 9.5, 80, 190, 4.4, STAHL, schwund=0.0)
    speck(img, ox, oy, 19.0, 0.0, 'sand')                    # Nietkopf
    pommel(img, ox, oy, -1.2, 1.5, EISEN)


def w_sickle_blood(img):
    """Sichel: kurzer Griff, eng gebogenes Blatt. 32x32."""
    ox, oy = 6, 26
    grip(img, ox, oy, 0.0, 7.0, 0.9, LEDER)
    pommel(img, ox, oy, -0.9, 1.4, EISEN)
    guard(img, ox, oy, 7.8, 0.8, -1.6, 1.6, GOLD)
    bx, by = to_xy(8.5, 0.0, ox, oy)
    sichel(img, bx - 8, by + 2, 8.5, -20, 128, 3.4, BLUT)


def w_chakram(img):
    """Wurfring: geschliffener Reif mit vier Klingen. 32x32."""
    wurfwaffe(img, 'ring', STAHL, LEDER, stufe=0, cx=15, cy=15, groesse=6.0)


def w_shield_tower(img):
    """Schild: Platte mit Randbeschlag und Buckel. 36x36."""
    platte(img, 17, 4, 22, 27, EISEN)
    for j, x in ((5, 17), (26, 17)):                         # Zierniete
        put(img, x, j, C('gold'))
    kugel(img, 17, 15, 4.0, GOLD)                            # Buckel
    kristall(img, 17, 15, 2, MOND, zacken=False)             # Wappenstein


def w_blunderbuss(img):
    """Donnerbuechse: Holzschaft, weit ausgestellte Muendung. 36x36."""
    slant(img, 4, 16, 6, 6, -0.2, HOLZ)                      # Kolben
    box(img, 9, 16, 8, 4, HOLZ)                              # Schaftbacke
    box(img, 16, 17, 9, 3, SILBER)                           # Lauf
    for i in range(6):                                       # Trichter
        h = 3 + i
        box(img, 25 + i, 18 - (h // 2), 1, h, SILBER)
    box(img, 12, 15, 4, 2, GOLD)                             # Schloss
    put(img, 13, 14, C('sand'))                              # Hahn
    put(img, 14, 20, C('mauve'))                             # Abzug
    for x in (10, 14):                                       # Maserung
        put(img, x, 19, C('maroon'))


# --- Bauplan Schwert -------------------------------------------------------
# Alle Klingenwaffen folgen demselben Aufbau. Statt ihn je Waffe zu wiederholen,
# setzt schwert() ihn einmal zusammen und nimmt die Unterschiede als Parameter.
# stufe bildet die Calamity-Progression ab:
#   0 Pre-Hardmode  schlichtes Parier, kein Stein
#   1 Hardmode      Haertelinie und Stein im Parier
#   2 Post-Moon-Lord ausgestellte Quillons, Dornen, Funken auf der Klinge

def schwert(img, ox, oy, laenge, halb, klinge, beschlag, wicklung=LEDER,
            stein=None, stufe=0, kruemmung=0.0, tip=3.5, fuller=None,
            serr=None):
    if fuller is None:
        fuller = halb >= 1.25
    blade(img, ox, oy, laenge, halb, klinge, curve_amp=kruemmung, tip=tip,
          serr=serr, fuller=fuller)
    if stufe >= 1:
        schliff(img, ox, oy, laenge, halb, klinge, curve_amp=kruemmung,
                schritt=3 if stufe == 1 else 2)
    if stufe >= 2:
        for u in (laenge * 0.35, laenge * 0.6):               # Funken im Stahl
            speck(img, ox, oy, u, 0.4 + kruemmung * (u / laenge) ** 2,
                  klinge['glanz'])

    quer = 1.7 + halb * 1.2
    dick = 0.7 + halb * 0.2
    guard(img, ox, oy, -0.9, dick, -quer, quer, beschlag,
          flare=0.5 if stufe >= 2 else 0.0,
          spitze=beschlag['glanz'] if stufe >= 2 else None)
    if stein:
        gem(img, ox, oy, -0.9, stein['hell'], stein['mitte'], stein['dunkel'],
            glanz=stein['glanz'])

    griff_von = -(3.4 + halb * 1.4)
    grip(img, ox, oy, griff_von, -1.9, 0.8 + halb * 0.15, wicklung)
    pommel(img, ox, oy, griff_von - 0.9, 1.1 + halb * 0.35, beschlag)


def w_shortsword_copper(img):
    """Kupferkurzschwert - Pre-Hardmode, schlicht. 32x32."""
    schwert(img, 11, 20, 13.5, 1.0, KUPFER, KUPFER, wicklung=LEDER, stufe=0)


def w_broadsword_cobalt(img):
    """Kobaltbreitschwert - Hardmode, Haertelinie und Stein. 36x36."""
    schwert(img, 12, 23, 17.0, 1.5, KOBALT, SILBER, stein=MOND, stufe=1,
            tip=4.5)


def w_greatsword_abyss(img):
    """Abgrundgrossschwert - Hardmode, breit und dunkel. 40x40."""
    schwert(img, 13, 26, 19.0, 2.0, ABGRUND, EISEN, wicklung=DUNKELLEDER,
            stein=STURM, stufe=1, tip=5.0)


def w_katana_dawn(img):
    """Morgenkatana - Hardmode, gekruemmt, goldenes Heft. 36x36."""
    schwert(img, 11, 24, 19.0, 1.0, FLAMME, GOLD, stein=None, stufe=1,
            kruemmung=1.6, tip=4.5)


def w_dagger_void(img):
    """Leeredolch - Post-Moon-Lord, Dornen und Funken. 28x28."""
    schwert(img, 9, 18, 10.5, 1.0, LEERE, GOLD, wicklung=DUNKELLEDER,
            stein=LEERE, stufe=2, kruemmung=0.9, tip=3.0)


def w_blade_astral(img):
    """Astralklinge - Post-Moon-Lord, ausgestellte Quillons. 40x40."""
    schwert(img, 13, 26, 19.5, 1.5, ASTRAL, GOLD, wicklung=DUNKELLEDER,
            stein=ASTRAL, stufe=2, tip=5.0)


# --- Bauplan Stangenwaffe --------------------------------------------------
# Schaft, Knauf und Stufendeko sind bei Speer, Axt, Sense und Stab identisch -
# nur der Kopf unterscheidet sie. Also nimmt stangenwaffe() den Kopf als
# Funktion entgegen. Die kopf_*-Bauer liefern so eine Funktion zurueck.

def stangenwaffe(img, ox, oy, laenge, kopf, holz=HOLZ, beschlag=EISEN,
                 stufe=0, halb=0.8):
    ringe = ((laenge * 0.3, laenge * 0.62) if stufe == 0 else
             (laenge * 0.2, laenge * 0.45, laenge * 0.7))
    stange(img, ox, oy, 0.0, laenge, halb, holz, ringe=ringe)
    tx, ty = to_xy(laenge, 0.0, ox, oy)
    kopf(img, ox, oy, tx, ty, stufe)
    if stufe >= 2:                                   # Runen im Schaft
        for u in (laenge * 0.36, laenge * 0.56, laenge * 0.76):
            speck(img, ox, oy, u, 0.0, beschlag['glanz'])
    pommel(img, ox, oy, -1.0, 1.3 + halb * 0.4, beschlag)


def kopf_speer(klinge, beschlag=GOLD, laenge=9.0, halb=1.1):
    def bauen(img, ox, oy, tx, ty, stufe):
        guard(img, tx, ty, 0.0, 0.8, -1.9, 1.9, beschlag,
              spitze=beschlag['glanz'] if stufe >= 2 else None)
        blade(img, tx, ty, laenge, halb, klinge, tip=laenge * 0.55)
        if stufe >= 1:
            schliff(img, tx, ty, laenge, halb, klinge, von=2,
                    bis=int(laenge) - 3, schritt=2)
    return bauen


def kopf_axt(klinge, radius=10.0, dicke=5.6, doppelt=False):
    def bauen(img, ox, oy, tx, ty, stufe):
        balken(img, tx - 2, ty + 2, tx + 2, ty - 2, 2.4, EISEN)
        if doppelt:
            sichel(img, tx - 6, ty - 6, radius, -100, 10, dicke * 0.8,
                   klinge, schwund=0.0)
            sichel(img, tx + 6, ty + 6, radius, 80, 190, dicke * 0.8,
                   klinge, schwund=0.0)
        else:
            sichel(img, tx - 4, ty + 4, radius, -34, 84, dicke, klinge,
                   schwund=0.0)
        speck(img, tx, ty, 0.0, 0.0, 'sand' if stufe < 2 else klinge['glanz'])
    return bauen


def kopf_sense(klinge, radius=11.5, dicke=4.2):
    def bauen(img, ox, oy, tx, ty, stufe):
        guard(img, tx, ty, 0.0, 0.9, -1.7, 1.7, EISEN)
        sichel(img, tx - 11, ty + 1, radius, -8, 118, dicke, klinge)
        if stufe >= 2:
            speck(img, tx, ty, 0.0, -2.4, klinge['glanz'])
    return bauen


def kopf_kugel(kern, beschlag=GOLD, rad=3.4):
    def bauen(img, ox, oy, tx, ty, stufe):
        for v in (-2.4, 2.4):                        # Gabelzinken
            stange(img, ox, oy, laenge_von(ox, oy, tx, ty) - 1.0,
                   laenge_von(ox, oy, tx, ty) + 4.0, 0.55, beschlag, v_c=v)
        guard(img, tx, ty, -0.5, 0.8, -2.6, 2.6, beschlag)
        kugel(img, tx + 3, ty - 3, rad, kern)
        if stufe >= 2:
            kristall(img, tx + 3, ty - 3, 2, kern, zacken=False)
    return bauen


def kopf_hammer(kopframpe, weite=5.0, dicke=4.0):
    def bauen(img, ox, oy, tx, ty, stufe):
        balken(img, tx - weite, ty - weite, tx + weite, ty + weite,
               dicke, kopframpe)
        balken(img, tx - weite - 1, ty - weite - 1, tx - weite + 1,
               ty - weite + 1, dicke * 0.8, SILBER)      # Schlagflaeche
        for dv in (-weite * 0.7, weite * 0.7):
            speck(img, tx, ty, 0.0, dv, 'sand' if stufe < 2 else 'pale_yellow')
    return bauen


def laenge_von(ox, oy, tx, ty):
    """Wieviel u liegt zwischen Schaftfuss und einem Punkt - fuer Koepfe,
    die noch etwas am Schaft entlang bauen wollen."""
    return ((tx - ox) - (ty - oy)) / 2.0


def w_axe_copper(img):
    """Kupferaxt - Pre-Hardmode. 40x40."""
    stangenwaffe(img, 7, 34, 19.0, kopf_axt(KUPFER, radius=9.0, dicke=5.0),
                 holz=HOLZ, beschlag=KUPFER, stufe=0)


def w_spear_cobalt(img):
    """Kobaltspeer - Hardmode, Haertelinie im Blatt. 44x44."""
    stangenwaffe(img, 6, 37, 22.0, kopf_speer(KOBALT), holz=LEDER,
                 beschlag=SILBER, stufe=1, halb=0.85)


def w_scythe_void(img):
    """Leeresense - Post-Moon-Lord, Runen im Schaft. 46x46."""
    stangenwaffe(img, 7, 39, 21.0, kopf_sense(LEERE, radius=12.0, dicke=4.4),
                 holz=LEDER, beschlag=GOLD, stufe=2)


def w_staff_abyss(img):
    """Abgrundstab - Hardmode, gefasster Kern. 44x44."""
    stangenwaffe(img, 7, 37, 22.0, kopf_kugel(ABGRUND), holz=LEDER,
                 beschlag=GOLD, stufe=1)


def w_hammer_astral(img):
    """Astralhammer - Post-Moon-Lord, schwerer Kopf. 44x44."""
    stangenwaffe(img, 7, 37, 20.0, kopf_hammer(ASTRAL, weite=5.5, dicke=4.2),
                 holz=LEDER, beschlag=GOLD, stufe=2, halb=0.9)


def w_greataxe_abyss(img):
    """Abgrunddoppelaxt - Hardmode, zwei Blaetter. 46x46."""
    stangenwaffe(img, 8, 40, 21.0,
                 kopf_axt(ABGRUND, radius=9.5, dicke=5.5, doppelt=True),
                 holz=HOLZ, beschlag=EISEN, stufe=1, halb=0.9)


# --- Bauplan Schusswaffe ---------------------------------------------------
# Gehaeuse, Griff, Lauf und Muendung wiederholen sich bei jeder Feuerwaffe.
# Unterschiede: Lauflaenge, Muendungsform, Magazin, Visier, Kolben - und die
# Stufe, die Messingbeschlag (1) beziehungsweise Kern und Kuehlrippen (2) setzt.

def schusswaffe(img, metall, holz, laenge=10, stufe=0, magazin=False,
                visier=False, kolben=False, muendung='gerade', kern=None,
                x=6, y=13):
    hoehe = 6
    if kolben:
        slant(img, x - 7, y + 1, 8, 5, -0.25, holz)          # Schulterstuetze
    slant(img, x + 3, y + hoehe, 4, 6, -0.5, holz)           # Griff
    box(img, x, y, 11, hoehe, metall)                        # Gehaeuse
    bx, by = x + 11, y + 1
    box(img, bx, by, laenge, 3, metall)                      # Lauf

    if muendung == 'trichter':
        for i in range(5):
            h = 3 + i
            box(img, bx + laenge + i, by + 1 - h // 2, 1, h, metall)
    elif muendung == 'kegel':
        for j, br in ((0, 1), (1, 2), (2, 3), (3, 2), (4, 1)):
            for i in range(br):
                put(img, bx + laenge + i, by - 1 + j,
                    C('crimson' if i else 'salmon'))
    else:
        put(img, bx + laenge - 1, by + 1, C('ink'))          # Seele

    if magazin:
        box(img, x + 8, y + hoehe, 4, 8, holz)
        for j in (y + hoehe + 2, y + hoehe + 4, y + hoehe + 6):
            put(img, x + 9, j, C(holz['glanz']))
    if visier:
        box(img, x + 5, y - 3, 5, 3, metall)
        put(img, x + 7, y - 2, C(metall['glanz']))
    if kern:
        kristall(img, x + 4, y + hoehe + 1, 3, kern, zacken=False)
        put(img, x + 4, y + hoehe - 2, C(kern['hell']))

    if stufe >= 1:                                           # Messingbeschlag
        for j in range(y, y + hoehe):
            put(img, x + 10, j, C('sand' if j < y + hoehe - 2 else 'amber'))
    if stufe >= 2:                                           # Kuehlrippen
        for i in range(bx + 2, bx + laenge - 1, 3):
            put(img, i, by, C(metall['glanz']))
        put(img, bx + laenge, by, C('sky'))
        put(img, bx + laenge, by + 2, C('blue_br'))
    put(img, x + 11, y + hoehe - 1, C('mauve'))              # Abzug


def w_pistol_scrap(img):
    """Schrottpistole - Pre-Hardmode, kurzer Lauf. 30x30."""
    schusswaffe(img, EISEN, LEDER, laenge=7, stufe=0, x=5, y=12)


def w_revolver_heavy(img):
    """Schwerer Revolver - Hardmode, langer Lauf, Messing. 34x34."""
    schusswaffe(img, SILBER, LEDER, laenge=12, stufe=1, x=5, y=13)


def w_pistol_burst(img):
    """Salvenpistole - Hardmode, Visier. 32x32."""
    schusswaffe(img, KOBALT, DUNKELLEDER, laenge=8, stufe=1, visier=True,
                x=6, y=14)


def w_smg_needle(img):
    """Nadel-MP - Hardmode, langes Magazin. 34x34."""
    schusswaffe(img, SILBER, DUNKELLEDER, laenge=10, stufe=1, magazin=True,
                visier=True, x=5, y=12)


def w_shotgun_scatter(img):
    """Streuflinte - Hardmode, Trichtermuendung und Kolben. 38x38."""
    schusswaffe(img, SILBER, HOLZ, laenge=11, stufe=1, kolben=True,
                muendung='trichter', x=9, y=15)


def w_raygun_astral(img):
    """Astralstrahler - Post-Moon-Lord, Kristallkern und Kuehlrippen. 36x36."""
    schusswaffe(img, ASTRAL, DUNKELLEDER, laenge=12, stufe=2, kern=ASTRAL,
                visier=True, x=6, y=14)


def kopf_hellebarde(klinge, beschlag=SILBER):
    """Hellebardenkopf: Beil an der Flanke, Stossklinge obenauf."""
    def bauen(img, ox, oy, tx, ty, stufe):
        balken(img, tx - 2, ty + 2, tx + 2, ty - 2, 2.2, EISEN)
        sichel(img, tx - 4, ty + 4, 8.5, -30, 70, 4.4, klinge, schwund=0.0)
        guard(img, tx, ty, 0.0, 0.7, -1.6, 1.6, beschlag)
        blade(img, tx, ty, 7.0, 0.9, klinge, tip=4.0)
        if stufe >= 1:
            speck(img, tx, ty, 1.5, -1.2, klinge['glanz'])
    return bauen


# --- Stufenvarianten -------------------------------------------------------
# Ab hier kostet eine Waffe eine Zeile. Die Formen stehen, variiert werden
# Rampe, Stufe und Masse - genau wie Calamity dieselbe Silhouette ueber
# Pre-Hardmode, Hardmode und Post-Moon-Lord fuehrt.

def w_shortsword_iron(img):
    """Eisenkurzschwert - Pre-Hardmode. 32x32."""
    schwert(img, 11, 20, 13.0, 1.0, EISEN, EISEN, stufe=0)


def w_broadsword_bone(img):
    """Knochenbreitschwert - Pre-Hardmode, breit und stumpf. 36x36."""
    schwert(img, 12, 23, 16.0, 1.5, KNOCHEN, KUPFER, wicklung=DUNKELLEDER,
            stein=KNOCHEN, stufe=0, tip=4.0)


def w_rapier_gold(img):
    """Goldrapier - Hardmode, sehr schmale Klinge. 36x36."""
    schwert(img, 11, 24, 18.0, 0.75, STAHL, GOLD, stein=GOLD, stufe=1,
            tip=4.0)


def w_katana_void(img):
    """Leerekatana - Post-Moon-Lord, gekruemmt und gedornt. 38x38."""
    schwert(img, 12, 25, 20.0, 1.0, LEERE, GOLD, wicklung=DUNKELLEDER,
            stein=LEERE, stufe=2, kruemmung=1.7, tip=4.5)


def w_dagger_cobalt(img):
    """Kobaltdolch - Hardmode. 28x28."""
    schwert(img, 9, 18, 10.0, 1.0, KOBALT, SILBER, stein=MOND, stufe=1,
            tip=3.0)


def w_spear_bone(img):
    """Knochenspeer - Pre-Hardmode. 44x44."""
    stangenwaffe(img, 6, 37, 21.0, kopf_speer(KNOCHEN, beschlag=KUPFER),
                 holz=LEDER, beschlag=KUPFER, stufe=0, halb=0.8)


def w_halberd_cobalt(img):
    """Kobalthellebarde - Hardmode, Beil und Stossklinge. 46x46."""
    stangenwaffe(img, 7, 39, 22.0, kopf_hellebarde(KOBALT), holz=LEDER,
                 beschlag=SILBER, stufe=1, halb=0.85)


def w_scythe_copper(img):
    """Kupfersense - Pre-Hardmode. 44x44."""
    stangenwaffe(img, 7, 37, 20.0, kopf_sense(KUPFER, radius=11.0, dicke=4.0),
                 holz=LEDER, beschlag=SILBER, stufe=0)


def w_rifle_cobalt(img):
    """Kobaltgewehr - Hardmode, langer Lauf mit Zielfernrohr. 42x42."""
    schusswaffe(img, KOBALT, HOLZ, laenge=16, stufe=1, visier=True,
                kolben=True, x=10, y=16)


def w_smg_astral(img):
    """Astral-MP - Post-Moon-Lord, Magazin und Kuehlrippen. 36x36."""
    schusswaffe(img, ASTRAL, DUNKELLEDER, laenge=10, stufe=2, magazin=True,
                visier=True, kern=ASTRAL, x=6, y=13)


# --- Bauplan Wurfwaffe -----------------------------------------------------
# Rogue-Waffen sind klein und rund: Stern, Ring, Kugel, Bombe. Sie teilen
# sich Nabe, Kantenlicht und Stufendeko, unterscheiden sich nur in der Form.

def stern(img, cx, cy, zacken, laenge, r, spitzwinkel=0.45):
    """Sternfoermige Klingen um eine Nabe - fuer Wurfsterne."""
    for k in range(zacken):
        a = 2.0 * math.pi * k / zacken - math.pi / 2.0
        dx, dy = math.cos(a), -math.sin(a)
        for i in range(laenge + 1):
            br = int(round((laenge - i) * spitzwinkel))
            for j in range(-br, br + 1):
                x = int(round(cx + dx * i - dy * j))
                y = int(round(cy + dy * i + dx * j))
                licht = (x - cx) + (y - cy)
                if licht < -laenge * 0.5:
                    col = r['glanz']
                elif licht < -laenge * 0.15:
                    col = r['hell']
                elif licht < laenge * 0.25:
                    col = r['mitte']
                elif licht < laenge * 0.6:
                    col = r['dunkel']
                else:
                    col = r['tief']
                put(img, x, y, C(col))


def wurfwaffe(img, form, klinge, beschlag=EISEN, stufe=0, cx=12, cy=12,
              groesse=4.0):
    """Kleine Wurfwaffe in einer von vier Formen.

    form: 'stern', 'ring', 'ball' oder 'bombe'. stufe 1 setzt einen
    Beschlagring beziehungsweise ein Band, stufe 2 einen Kern und Funken.
    """
    if form == 'stern':
        stern(img, cx, cy, 4, int(groesse * 2), klinge)
        ring(img, cx, cy, groesse * 0.55, groesse * 0.25, beschlag)
    elif form == 'ring':
        ring(img, cx, cy, groesse * 1.6, groesse, klinge)
        aussen = int(math.ceil(groesse * 1.6))
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            for i, br in ((aussen - 1, 1), (aussen, 1), (aussen + 1, 1),
                          (aussen + 2, 0)):
                for k in range(-br, br + 1):
                    put(img, cx + dx * i - dy * k, cy + dy * i + dx * k,
                        C(klinge['hell'] if dx + dy < 0 else klinge['dunkel']))
        ring(img, cx, cy, groesse * 1.02, groesse * 0.65, beschlag)
    elif form == 'ball':
        kugel(img, cx, cy, groesse, klinge)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1),
                       (-1, 1), (1, -1)):
            schraeg = dx and dy
            nah = int(groesse * (0.72 if schraeg else 1.0)) + 1
            fern = nah + 1
            hell = dx + dy < 0
            put(img, cx + dx * nah, cy + dy * nah,
                C(klinge['glanz'] if hell else klinge['mitte']))
            put(img, cx + dx * fern, cy + dy * fern,
                C(klinge['hell'] if hell else klinge['tief']))
        for i in range(-int(groesse) + 1, int(groesse)):     # Naht
            put(img, cx + i, cy + int(groesse * 0.45),
                C(beschlag['mitte'] if i % 2 else beschlag['dunkel']))
        for ax, ay in ((1, -2), (-2, 1)):                    # Verschleiss
            put(img, cx + ax, cy + ay, C(beschlag['hell']))
    elif form == 'bombe':
        kugel(img, cx, cy, groesse, klinge)
        for i in range(3):                               # Zuendschnur
            put(img, cx + 1 + i, cy - int(groesse) - i, C(beschlag['mitte']))
        put(img, cx + 3, cy - int(groesse) - 3, C('ember'))
        put(img, cx + 4, cy - int(groesse) - 3, C('orange'))
        for i in range(-2, 3):                           # Halsband
            put(img, cx + i, cy - int(groesse) + 1, C(beschlag['hell']))

    if stufe >= 1:                       # Glanzpunkt - beim Reif auf den
        versatz = int(groesse * 1.3) if form == 'ring' else 1
        put(img, cx - versatz, cy - versatz, C(beschlag['glanz']))
    if stufe >= 2:
        if form != 'ring':               # der Reif ist innen hohl
            kristall(img, cx, cy, 2, klinge, zacken=False)
        for dx, dy in ((-1, 0), (0, -1)):                # Glanz auf der Kante
            put(img, cx + dx * int(groesse), cy + dy * int(groesse),
                C(klinge['glanz']))


def w_shuriken_steel(img):
    """Wurfstern - Pre-Hardmode. 24x24."""
    wurfwaffe(img, 'stern', STAHL, GOLD, stufe=0, groesse=4.5)


def w_shuriken_astral(img):
    """Astralstern - Post-Moon-Lord, Kern und Funken. 28x28."""
    wurfwaffe(img, 'stern', ASTRAL, GOLD, stufe=2, cx=14, cy=14, groesse=5.0)


def w_chakram_void(img):
    """Leerering - Post-Moon-Lord. 32x32."""
    wurfwaffe(img, 'ring', LEERE, GOLD, stufe=2, cx=15, cy=15, groesse=5.5)


def w_spikyball_cobalt(img):
    """Kobaltstachelball - Hardmode. 26x26."""
    wurfwaffe(img, 'ball', KOBALT, SILBER, stufe=1, cx=13, cy=13, groesse=4.4)


def w_bomb_fire(img):
    """Brandbombe - Pre-Hardmode, Zuendschnur brennt. 26x26."""
    wurfwaffe(img, 'bombe', EISEN, KUPFER, stufe=0, cx=13, cy=15, groesse=5.0)


def w_bomb_void(img):
    """Leerebombe - Post-Moon-Lord, glimmender Kern. 28x28."""
    wurfwaffe(img, 'bombe', LEERE, GOLD, stufe=2, cx=14, cy=16, groesse=5.2)


# --- Kleine Bauplaene ------------------------------------------------------
# Bogen, Buch, Peitsche und Yoyo waren bisher Einzelstuecke. Auch sie haben
# eine feste Anatomie, also bekommen sie ihre eigenen Bauer.

def bogen(img, x0, y0, hoehe, bauch, holz, sehne='mint', stufe=0,
          griff=None):
    """Bogen mit Wurfarmen, Sehne und Griffwicklung."""
    bogenarm(img, x0, y0, hoehe, bauch, holz, sehne=sehne)
    mitte = y0 + hoehe // 2
    wick = griff or LEDER
    for dy in range(-2, 3):
        put(img, x0 + bauch, mitte + dy,
            C(wick['mitte'] if dy % 2 else wick['hell']))
        put(img, x0 + bauch + 1, mitte + dy, C(wick['tief']))
    for y in (y0, y0 + hoehe - 1):                   # Wurfarmspitzen
        put(img, x0, y, C('gold'))
    for y in (y0 + 1, y0 + hoehe - 2):
        put(img, x0 + 1, y, C('amber'))
    if stufe >= 1:                                   # Beschlag auf den Armen
        for y in (y0 + 4, y0 + hoehe - 5):
            put(img, x0 + int(bauch * 0.75), y, C('sand'))
            put(img, x0 + int(bauch * 0.75) + 1, y, C('rust_dk'))
    if stufe >= 2:                                   # Kern im Griff
        kristall(img, x0 + bauch, mitte, 2, holz, zacken=False)


def zauberbuch(img, x0, y0, breite, hoehe, deckel, stein, stufe=0):
    """Zauberbuch mit Beschlagbaendern und Wappenstein."""
    buch(img, x0, y0, breite, hoehe, deckel, KNOCHEN)
    kristall(img, x0 + breite // 2 - 1, y0 + hoehe // 2, 3, stein,
             zacken=stufe >= 2)
    for y in (y0 + 3, y0 + hoehe - 4):
        for x in range(x0 + 2, x0 + breite - 3):
            put(img, x, y, C('gold' if x % 3 else 'amber'))
    if stufe >= 1:
        put(img, x0 + 2, y0 + hoehe // 2, C('sand'))          # Schliesse


def peitsche(img, ox, oy, punkte, riemen, beschlag=GOLD, stufe=0):
    """Peitsche: Griff, Beschlagring, auslaufender Riemen."""
    grip(img, ox, oy, 0.0, 5.5, 1.0, LEDER)
    pommel(img, ox, oy, -0.8, 1.3, beschlag)
    guard(img, ox, oy, 6.0, 0.7, -1.4, 1.4, beschlag)
    schnur(img, punkte, riemen, dick_von=1.8, dick_bis=0.6,
           dornen=beschlag['hell'] if stufe >= 1 else None)
    if stufe >= 2:
        for x, y in punkte[2:4]:
            put(img, x, y - 3, C(riemen['glanz']))


def yoyo(img, cx, cy, rad, scheibe, achse=GOLD, stufe=0):
    """Yoyo: Schnur mit Schlaufe, Scheibe, Achse."""
    schnur(img, [(cx - 10, cy - 12), (cx - 6, cy - 7), (cx - 2, cy - 3)],
           SILBER, dick_von=0.6, dick_bis=0.6)
    kugel(img, cx, cy, rad, scheibe)
    kristall(img, cx, cy, 2, achse, zacken=False)
    for x, y in ((cx - 11, cy - 14), (cx - 10, cy - 14),
                 (cx - 11, cy - 13), (cx - 10, cy - 13)):
        put(img, x, y, C('tan'))
    if stufe >= 2:
        for dx, dy in ((-1, 0), (0, -1)):
            put(img, cx + dx * int(rad), cy + dy * int(rad),
                C(scheibe['glanz']))


def w_summon_copper(img):
    """Kupfertotem - Pre-Hardmode Beschwoerung. 40x40."""
    natur = rampe('green_pl', 'green_dk', 'green_lt', 'green_br', 'green',
                  'green_dk')
    stangenwaffe(img, 7, 34, 19.0, kopf_kugel(natur, beschlag=KUPFER, rad=3.2),
                 holz=DUNKELLEDER, beschlag=KUPFER, stufe=0)


def w_summon_astral(img):
    """Astraltotem - Post-Moon-Lord Beschwoerung. 46x46."""
    stangenwaffe(img, 8, 39, 22.0, kopf_kugel(ASTRAL, rad=3.8), holz=LEDER,
                 beschlag=GOLD, stufe=2)


def w_wand_cobalt(img):
    """Kobaltrute - Hardmode. 32x32."""
    ox, oy = 8, 24
    stange(img, ox, oy, 0.0, 14.0, 0.6, DUNKELLEDER, ringe=(4.0, 9.0))
    kx, ky = to_xy(15.0, 0.0, ox, oy)
    guard(img, ox, oy, 14.2, 0.7, -1.4, 1.4, SILBER)
    kristall(img, kx + 1, ky - 1, 3, KOBALT)
    pommel(img, ox, oy, -0.8, 1.1, SILBER)


def w_tome_void(img):
    """Leerekodex - Post-Moon-Lord. 30x30."""
    zauberbuch(img, 6, 5, 18, 20,
               rampe('lavender', 'magenta_dk', 'violet', 'purple',
                     'purple_dk', 'ink'), LEERE, stufe=2)


def w_bow_cobalt(img):
    """Kobaltbogen - Hardmode. 32x32."""
    bogen(img, 9, 3, 26, 5, KOBALT, sehne='mint', stufe=1)


def w_bow_astral(img):
    """Astralbogen - Post-Moon-Lord, Kern im Griff. 34x34."""
    bogen(img, 10, 3, 28, 6, ASTRAL, sehne='aqua_lt', stufe=2)


def w_whip_astral(img):
    """Astralpeitsche - Post-Moon-Lord. 40x40."""
    peitsche(img, 6, 33, [(14, 25), (20, 22), (26, 21), (31, 16), (34, 9),
                          (32, 4)], ASTRAL, beschlag=GOLD, stufe=2)


def w_yoyo_void(img):
    """Leereyoyo - Post-Moon-Lord. 32x32."""
    yoyo(img, 20, 20, 5.2, LEERE, achse=GOLD, stufe=2)


def schild(img, cx, y0, breite, hoehe, platte_r, buckel_r, stein=None,
           stufe=0):
    """Schild: Platte, Randnieten, Buckel, wahlweise Wappenstein."""
    platte(img, cx, y0, breite, hoehe, platte_r)
    for j in (y0 + 1, y0 + hoehe - 6):
        put(img, cx, j, C(buckel_r['glanz']))
    kugel(img, cx, y0 + hoehe // 3, breite * 0.19, buckel_r)
    if stein:
        kristall(img, cx, y0 + hoehe // 3, 2, stein, zacken=False)
    if stufe >= 1:                                   # Randbeschlag
        for j in range(2, hoehe - 8, 4):
            rand = int(platte_halb(breite, hoehe, j)) - 1
            put(img, cx - rand, y0 + j, C(buckel_r['hell']))
            put(img, cx + rand, y0 + j, C(buckel_r['dunkel']))
    if stufe >= 2:
        j = hoehe - 9
        rand = max(1, int(platte_halb(breite, hoehe, j)) - 1)
        for dx in (-rand, rand):
            put(img, cx + dx, y0 + j, C(buckel_r['glanz']))


def flegel(img, ox, oy, kettenlaenge, kopf_r, griff_r=DUNKELLEDER,
           beschlag=EISEN, stufe=0, rad=3.6):
    """Flegel: Griff, Kette, gedornte Kugel. Die Kette laeuft in die Kugel
    hinein, sonst haengt der Kopf lose."""
    grip(img, ox, oy, 0.0, 5.0, 0.85, griff_r)
    pommel(img, ox, oy, -0.8, 1.4, beschlag)
    kette(img, ox, oy, 4.0, kettenlaenge + 2.0, beschlag)
    kx, ky = to_xy(kettenlaenge + 4.0, 0.0, ox, oy)
    kugel(img, kx, ky, rad, kopf_r)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1),
                   (-1, 1), (1, -1)):
        schraeg = dx and dy
        nah = int(rad * (0.72 if schraeg else 1.0)) + 1
        hell = dx + dy < 0
        put(img, kx + dx * nah, ky + dy * nah,
            C(kopf_r['glanz'] if hell else kopf_r['mitte']))
        put(img, kx + dx * (nah + 1), ky + dy * (nah + 1),
            C(kopf_r['hell'] if hell else kopf_r['tief']))
    if stufe >= 2:
        kristall(img, kx, ky, 2, kopf_r, zacken=False)


def doppelklinge(img, ox, oy, laenge, halb, klinge, beschlag, stufe=0):
    """Doppelklinge: zwei Klingen an einem Griff, die zweite um 180 Grad."""
    for kippen in (False, True):
        def zeichnen(ziel, kippen=kippen):
            px, py = ((ziel.width - 1 - ox, ziel.height - 1 - oy)
                      if kippen else (ox, oy))
            blade(ziel, px, py, laenge, halb, klinge, tip=laenge * 0.3)
            guard(ziel, px, py, -0.8, 0.9, -1.6 - halb, 1.6 + halb, beschlag,
                  spitze=beschlag['glanz'] if stufe >= 2 else None)
        if kippen:
            gedreht(img, zeichnen)
        else:
            zeichnen(img)
    grip(img, ox, oy, -3.6, -1.6, 1.0, DUNKELLEDER)
    if stufe >= 1:
        speck(img, ox, oy, -2.6, 0.0, beschlag['glanz'])


def w_shield_cobalt(img):
    """Kobaltschild - Hardmode. 36x36."""
    schild(img, 17, 4, 22, 27, KOBALT, SILBER, stein=MOND, stufe=1)


def w_shield_void(img):
    """Leereschild - Post-Moon-Lord. 38x38."""
    schild(img, 18, 4, 24, 29, LEERE, GOLD, stein=LEERE, stufe=2)


def w_flail_copper(img):
    """Kupferflegel - Pre-Hardmode. 38x38."""
    flegel(img, 6, 32, 12.0, KUPFER, beschlag=EISEN, stufe=0, rad=3.4)


def w_flail_astral(img):
    """Astralflegel - Post-Moon-Lord. 42x42."""
    flegel(img, 7, 36, 15.0, ASTRAL, beschlag=GOLD, stufe=2, rad=4.0)


def w_twinblade_astral(img):
    """Astraldoppelklinge - Post-Moon-Lord. 44x44."""
    doppelklinge(img, 22, 22, 15.0, 1.1, ASTRAL, GOLD, stufe=2)


WEAPONS = [
    ('sword_melee',      'Kurzschwert',            w_sword_melee),
    ('shortsword_bone',  'Knochen-Kurzschwert',    w_shortsword_bone),
    ('broadsword_iron',  'Eisen-Breitschwert',     w_broadsword_iron),
    ('broadsword_titan', 'Titanen-Breitschwert',   w_broadsword_titan),
    ('katana_moon',      'Mond-Katana',            w_katana_moon),
    ('katana_storm',     'Sturm-Katana',           w_katana_storm),
    ('greatsword_flame', 'Flammen-Grossschwert',   w_greatsword_flame),
    ('curved_fang',      'Krummschwert Fang',      w_curved_fang),
    ('dagger_bleed',     'Blutdolch',              w_dagger_bleed),
    ('dagger_gold',      'Gnadendolch',            w_dagger_gold),
    ('revolver',         'Revolver',               w_revolver),
    ('shotgun_boom',     'Schrotflinte',           w_shotgun_boom),
    ('smg_buzz',         'MP',                     w_smg_buzz),
    ('bow_hunter',       'Jagdbogen',              w_bow_hunter),
    ('spear_brim',       'Speer',                  w_spear_brim,      40),
    ('flail_nebula',     'Flegel',                 w_flail_nebula,    40),
    ('scythe_harvest',   'Sense',                  w_scythe_harvest,  44),
    ('dagger_throw',     'Wurfdolch',              w_dagger_throw,    24),
    ('boomerang_wood',   'Bumerang',               w_boomerang_wood,  32),
    ('spiky_ball',       'Stachelball',            w_spiky_ball,      22),
    ('javelin_bone',     'Wurfspiess',             w_javelin_bone,    40),
    ('axe_battle',       'Streitaxt',              w_axe_battle,      40),
    ('hammer_war',       'Kriegshammer',           w_hammer_war,      40),
    ('twinblade',        'Doppelklinge',           w_twinblade,       40),
    ('katar',            'Katar',                  w_katar,           34),
    ('wand_spark',       'Zauberstab',             w_wand_spark,      32),
    ('tome_flames',      'Zauberbuch',             w_tome_flames,     30),
    ('staff_crystal',    'Kristallstab',           w_staff_crystal,   44),
    ('magic_gun',        'Magiepistole',           w_magic_gun,       32),
    ('crossbow_repeater', 'Armbrust',              w_crossbow_repeater, 36),
    ('launcher_rocket',  'Raketenwerfer',          w_launcher_rocket, 36),
    ('flamethrower',     'Flammenwerfer',          w_flamethrower,    36),
    ('summon_totem',     'Beschwoerungsstab',      w_summon_totem,    44),
    ('whip_thorn',       'Dornenpeitsche',         w_whip_thorn,      40),
    ('yoyo_disc',        'Yoyo',                   w_yoyo_disc,       32),
    ('greataxe',         'Grossaxt',               w_greataxe,        44),
    ('sickle_blood',     'Sichel',                 w_sickle_blood,    32),
    ('chakram',          'Wurfring',               w_chakram,         32),
    ('shield_tower',     'Schild',                 w_shield_tower,    36),
    ('blunderbuss',      'Donnerbuechse',          w_blunderbuss,     36),
    ('shortsword_copper', 'Kupferkurzschwert',     w_shortsword_copper, 32),
    ('broadsword_cobalt', 'Kobaltbreitschwert',    w_broadsword_cobalt, 36),
    ('greatsword_abyss', 'Abgrundgrossschwert',    w_greatsword_abyss, 40),
    ('katana_dawn',      'Morgenkatana',           w_katana_dawn,     36),
    ('dagger_void',      'Leeredolch',             w_dagger_void,     28),
    ('blade_astral',     'Astralklinge',           w_blade_astral,    40),
    ('axe_copper',       'Kupferaxt',              w_axe_copper,      40),
    ('spear_cobalt',     'Kobaltspeer',            w_spear_cobalt,    44),
    ('scythe_void',      'Leeresense',             w_scythe_void,     46),
    ('staff_abyss',      'Abgrundstab',            w_staff_abyss,     44),
    ('hammer_astral',    'Astralhammer',           w_hammer_astral,   44),
    ('greataxe_abyss',   'Abgrunddoppelaxt',       w_greataxe_abyss,  46),
    ('pistol_scrap',     'Schrottpistole',         w_pistol_scrap,    30),
    ('revolver_heavy',   'Schwerer Revolver',      w_revolver_heavy,  34),
    ('pistol_burst',     'Salvenpistole',          w_pistol_burst,    32),
    ('smg_needle',       'Nadel-MP',               w_smg_needle,      34),
    ('shotgun_scatter',  'Streuflinte',            w_shotgun_scatter, 38),
    ('raygun_astral',    'Astralstrahler',         w_raygun_astral,   36),
    ('shortsword_iron',  'Eisenkurzschwert',       w_shortsword_iron, 32),
    ('broadsword_bone',  'Knochenbreitschwert',    w_broadsword_bone, 36),
    ('rapier_gold',      'Goldrapier',             w_rapier_gold,     36),
    ('katana_void',      'Leerekatana',            w_katana_void,     38),
    ('dagger_cobalt',    'Kobaltdolch',            w_dagger_cobalt,   28),
    ('spear_bone',       'Knochenspeer',           w_spear_bone,      44),
    ('halberd_cobalt',   'Kobalthellebarde',       w_halberd_cobalt,  46),
    ('scythe_copper',    'Kupfersense',            w_scythe_copper,   44),
    ('rifle_cobalt',     'Kobaltgewehr',           w_rifle_cobalt,    42),
    ('smg_astral',       'Astral-MP',              w_smg_astral,      36),
    ('shuriken_steel',   'Wurfstern',              w_shuriken_steel,  24),
    ('shuriken_astral',  'Astralstern',            w_shuriken_astral, 28),
    ('chakram_void',     'Leerering',              w_chakram_void,    32),
    ('spikyball_cobalt', 'Kobaltstachelball',      w_spikyball_cobalt, 26),
    ('bomb_fire',        'Brandbombe',             w_bomb_fire,       26),
    ('bomb_void',        'Leerebombe',             w_bomb_void,       28),
    ('summon_copper',    'Kupfertotem',            w_summon_copper,   40),
    ('summon_astral',    'Astraltotem',            w_summon_astral,   46),
    ('wand_cobalt',      'Kobaltrute',             w_wand_cobalt,     32),
    ('tome_void',        'Leerekodex',             w_tome_void,       30),
    ('bow_cobalt',       'Kobaltbogen',            w_bow_cobalt,      32),
    ('bow_astral',       'Astralbogen',            w_bow_astral,      34),
    ('whip_astral',      'Astralpeitsche',         w_whip_astral,     40),
    ('yoyo_void',        'Leereyoyo',              w_yoyo_void,       32),
    ('shield_cobalt',    'Kobaltschild',           w_shield_cobalt,   36),
    ('shield_void',      'Leereschild',            w_shield_void,     38),
    ('flail_copper',     'Kupferflegel',           w_flail_copper,    38),
    ('flail_astral',     'Astralflegel',           w_flail_astral,    42),
    ('twinblade_astral', 'Astraldoppelklinge',     w_twinblade_astral, 44),
]


PALETTE_RGB = {tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
                for h in RES64.values()}


def inseln(img):
    """Groessen der zusammenhaengenden Teile (8er-Nachbarschaft).

    Ein Sprite soll aus einem Stueck bestehen. Freischwebende Deko bekommt
    im Spiel ihren eigenen schwarzen Rand und liest sich als Dreck.
    """
    px = img.load()
    gesehen = set()
    teile = []
    for y in range(img.height):
        for x in range(img.width):
            if not px[x, y][3] or (x, y) in gesehen:
                continue
            stapel = [(x, y)]
            gesehen.add((x, y))
            groesse = 0
            while stapel:
                cx, cy = stapel.pop()
                groesse += 1
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = cx + dx, cy + dy
                        if (0 <= nx < img.width and 0 <= ny < img.height
                                and (nx, ny) not in gesehen and px[nx, ny][3]):
                            gesehen.add((nx, ny))
                            stapel.append((nx, ny))
            teile.append(groesse)
    return sorted(teile, reverse=True)


def pruefen(img, name):
    """Prueft ein fertiges Sprite gegen die Regeln, die sich ueber die
    Runden herausgestellt haben. Gibt eine Liste von Beanstandungen zurueck.
    """
    px = img.load()
    w, h = img.size
    mangel = []
    voll = [(x, y) for y in range(h) for x in range(w) if px[x, y][3]]
    farben = {px[x, y][:3] for x, y in voll}
    if farben - PALETTE_RGB:
        mangel.append('Farbe ausserhalb der Palette')
    if {px[x, y][3] for x, y in voll} != {255}:
        mangel.append('Teiltransparenz')
    if len(farben) < 8:
        mangel.append('nur %d Farben - Bauteile teilen sich eine Rampe'
                      % len(farben))
    teile = inseln(img)
    if len(teile) > 1:
        mangel.append('%d lose Teile (%s)' % (len(teile), teile))
    return mangel


def zuschneiden(img):
    """Schneidet auf das Motiv zu und laesst genau 1 px Rand stehen.

    Die Groesse im WEAPONS-Eintrag ist damit nur noch die Zeichenflaeche -
    ausgeliefert wird, was die Waffe wirklich braucht. Das spart toten Rand
    und macht die 1-px-Regel zur Eigenschaft der Ausgabe statt zur Disziplin
    beim Zeichnen.
    """
    kasten = img.getbbox()
    if not kasten:
        return img
    inhalt = img.crop(kasten)
    eng = Image.new('RGBA', (inhalt.width + 2, inhalt.height + 2), (0, 0, 0, 0))
    eng.paste(inhalt, (1, 1))
    return eng


def check_border(img, name) -> None:
    """Der Rand muss frei bleiben - dort landet spaeter die schwarze Kontur."""
    w, h = img.size
    rand = ([(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)]
            + [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)])
    for x, y in rand:
        if img.getpixel((x, y))[3]:
            raise AssertionError('%s: Rand belegt bei %d,%d' % (name, x, y))


def contact_sheet(images, scale=6):
    """Kontaktbogen, der auch gemischte Leinwandgroessen sauber ausrichtet."""
    cols = 5
    rows = (len(images) + cols - 1) // cols
    zelle = max(max(im.size) for im in images) + 2
    sheet = Image.new('RGBA', (cols * zelle * scale, rows * zelle * scale),
                      (46, 34, 47, 255))
    for i, img in enumerate(images):
        big = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
        cx = (i % cols) * zelle * scale + (zelle * scale - big.width) // 2
        cy = (i // cols) * zelle * scale + (zelle * scale - big.height) // 2
        sheet.alpha_composite(big, (cx, cy))
    return sheet


KLASSEN = (
    ('Fernkampf', ('revolver', 'pistol', 'smg', 'shotgun', 'rifle',
                   'blunderbuss', 'bow', 'crossbow', 'launcher',
                   'flamethrower', 'raygun')),
    ('Magie', ('wand', 'tome', 'staff', 'magic')),
    ('Beschwoerung', ('summon',)),
    ('Rogue', ('shuriken', 'chakram', 'bomb', 'spiky', 'boomerang',
               'dagger_throw', 'javelin')),
    ('Nahkampf', ()),                       # Auffangklasse
)

STUFEN_WORT = (
    (2, ('astral', 'void', 'leere')),
    (1, ('cobalt', 'abyss', 'dawn', 'storm', 'moon', 'heavy', 'burst',
         'needle', 'scatter', 'titan', 'flame', 'gold')),
    (0, ()),
)


def klasse_von(wid):
    for name, teile in KLASSEN:
        if any(t in wid for t in teile):
            return name
    return 'Nahkampf'


def stufe_von(wid):
    for stufe, teile in STUFEN_WORT:
        if any(t in wid for t in teile):
            return stufe
    return 0


def liste_schreiben(pfad, zeilen):
    """Schreibt die Waffenliste als Markdown - Grundlage fuer die Einbindung."""
    stufen_name = {0: 'Pre-Hardmode', 1: 'Hardmode', 2: 'Post-Moon-Lord'}
    zeilen = sorted(zeilen, key=lambda z: (klasse_von(z[0]), stufe_von(z[0]), z[0]))
    text = [
        '# Waffen-Sprites', '',
        'Erzeugt von tools/generate_weapons.py. Nicht von Hand bearbeiten -',
        'Aenderungen gehen beim naechsten Lauf verloren.', '',
        'Alle Sprites: Resurrect-64-Palette, voll deckend, ohne eingebackene',
        'Kontur, rundum genau 1 px frei.', '',
        '| Datei | Name | Klasse | Stufe | Groesse | Farben |',
        '|---|---|---|---|---|---|',
    ]
    for wid, name, w, h, farben in zeilen:
        text.append('| `%s.png` | %s | %s | %s | %dx%d | %d |'
                    % (wid, name, klasse_von(wid),
                       stufen_name[stufe_von(wid)], w, h, farben))
    text += ['', 'Insgesamt %d Waffen.' % len(zeilen), '']
    with open(pfad, 'w', encoding='utf-8') as f:
        f.write(chr(10).join(text))


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(root / 'assets' / 'sprites' / 'weapons'))
    ap.add_argument('--sheet', action='store_true', help='Kontaktbogen daneben ablegen')
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    made = []
    zeilen = []
    beanstandet = []
    for eintrag in WEAPONS:
        wid, name, fn = eintrag[:3]
        gr = eintrag[3] if len(eintrag) > 3 else GROESSE
        img = blank(gr)
        fn(img)
        img = zuschneiden(img)
        check_border(img, wid)
        for satz in pruefen(img, wid):
            beanstandet.append((wid, satz))
        img.save(out / ('%s.png' % wid))
        farben = len({img.getpixel((x, y)) for x in range(img.width)
                      for y in range(img.height) if img.getpixel((x, y))[3]})
        made.append(img)
        zeilen.append((wid, name, img.width, img.height, farben))
        print('  %-20s %-24s %2dx%-2d %2d Farben'
              % (wid + '.png', name, img.width, img.height, farben))

    if args.sheet:
        contact_sheet(made).save(out / '_sheet.png')
        print('  %-20s Kontaktbogen' % '_sheet.png')

    liste = root / 'tools' / 'WAFFEN.md'
    liste_schreiben(liste, zeilen)
    print('\nFertig: %d Sprites in %s' % (len(made), out))
    print('Waffenliste: %s' % liste)
    if beanstandet:
        print('')
        print('Beanstandungen:')
        for wid, satz in beanstandet:
            print('  %-20s %s' % (wid, satz))
    else:
        print('Pruefung: alles sauber')


if __name__ == '__main__':
    main()
