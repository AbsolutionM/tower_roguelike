#!/usr/bin/env python3
"""Kachelsatz Schleimturm im Stil von Sprites/tilesets/slimetower (AAP-64).

Aufbau aus gras_flowers.aseprite abgelesen:
    32x32 Kacheln, 1 px Luecke im Blatt, elf Farben, grosse ruhige Flaechen.
    Rand:   1 px durchsichtig, 1 px Kohle (221c1a), dann links/rechts/unten
            eine Weinlinie (422433) als Schattenkante, oben direkt der
            dunkle Saum.
    Saum:   ein welliger Streifen dunkleren Bodens, 3-9 px tief, an jedem
            offenen Rand; laeuft an den Nahtstellen der Kacheln durch.
    Risse:  kurze Weinlinien vom Rand nach innen, darueber eine dunkle Zeile.
    Deko:   kleine Kreuze (hell, dunkle Mitte) und einzelne helle Punkte.
    Weg:    dunklere Flaeche mit rundem Eck, ohne Umriss.
    Klippe: unterer Rand zeigt eine Steinfront zwischen zwei Weinlinien.

Keine 3-Pixel-Regel - die gilt fuer Waffen. Kacheln leben von Flaechen.

Ausgabe nur in eigene Ordner:
    python tools/generate_tiles_aap.py --out C:/Users/maxst/Desktop/Sprites/claude/tilesets/slimetower
"""

from __future__ import annotations

import argparse
import math
import zlib
from pathlib import Path

from PIL import Image

from palette import duel_anpassen


AAP = {
    'schwarz': '060608', 'kohle': '141013', 'nacht': '221c1a',
    'kante': '242234', 'wein': '422433',
    'stein_tief': '333941', 'stein': '4a5462', 'stein_hell': '6d758d',
    'stein_licht': '8b93af', 'stein_glanz': 'b3b9d1',
    'schleim_kante': '24523b', 'schleim_tief': '1a7a3e',
    'schleim_dk': '14a02e', 'schleim': '59c135', 'schleim_hell': '9cdb43',
    'schleim_licht': 'd6f264', 'schleim_glanz': 'fffc40',
    'knochen': 'e4d2aa', 'knochen_dk': 'c7b08b', 'knochen_tief': 'a08662',
    'lila': '793a80', 'lila_dk': '403353',
}
AAP64 = set("""060608 141013 3b1725 73172d b4202a df3e23 fa6a0a f9a31b ffd541
fffc40 d6f264 9cdb43 59c135 14a02e 1a7a3e 24523b 122020 143464 285cc4 249fde
20d6c7 a6fcdb fef3c0 fad6b8 f5a097 e86a73 bc4a9b 793a80 403353 242234 221c1a
322b28 71413b bb7547 dba463 f4d29c fdf6d5 ffffff dae0ea b3b9d1 8b93af 6d758d
4a5462 333941 422433 5b3138 8e5252 ba756a e4d2aa c7b08b a08662 796755 5a4e44
423934""".split())
assert all(v in AAP64 for v in AAP.values())

N = 32
SEITEN = ((1, 0), (-1, 0), (0, 1), (0, -1))


def C(name):
    h = AAP[name]
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def zufall(name, k=0):
    """Deterministischer Wert 0..1 aus Kachelname und Laufindex."""
    return (zlib.crc32(('%s#%d' % (name, k)).encode()) & 0xffff) / 65535.0


class Kachel:
    def __init__(self, name):
        self.name = name
        self.img = Image.new('RGBA', (N, N), (0, 0, 0, 0))
        self.px = self.img.load()
        self._k = 0

    def put(self, x, y, col):
        if 0 <= x < N and 0 <= y < N:
            self.px[x, y] = C(col)

    def get(self, x, y):
        if 0 <= x < N and 0 <= y < N:
            return self.px[x, y]
        return None

    def ist(self, x, y, col):
        return self.get(x, y) == C(col)

    def wurf(self):
        self._k += 1
        return zufall(self.name, self._k)

    def wahl(self, folge):
        return folge[int(self.wurf() * len(folge)) % len(folge)]


# --- Saum und Rand ------------------------------------------------------------
# Der Saum ist eine Funktion der Position entlang des Randes, periodisch in
# 32, damit er von Kachel zu Kachel durchlaeuft - beim Vorbild liegen die
# Wellen an der Naht exakt uebereinander.

def saumtiefe(t, seite):
    ph = {'l': 0.0, 'r': 1.7, 'o': 3.1, 'u': 4.6}[seite]
    w = (2.4 * math.sin(2 * math.pi * t / 32 + ph)
         + 1.6 * math.sin(6 * math.pi * t / 32 + ph * 2))
    return max(3, min(9, int(round(5.5 + w))))


def plattform(k, offen, klippe=False):
    """Boden mit Rand an den offenen Seiten. offen: Teilmenge von 'lrou'."""
    x0 = 1 if 'l' in offen else 0
    x1 = 30 if 'r' in offen else 31
    y0 = 1 if 'o' in offen else 0
    y1 = 30 if 'u' in offen else 31
    r = 5
    ecken = []
    if 'l' in offen and 'o' in offen:
        ecken.append((x0 + r, y0 + r, -1, -1))
    if 'r' in offen and 'o' in offen:
        ecken.append((x1 - r, y0 + r, 1, -1))
    if 'l' in offen and 'u' in offen:
        ecken.append((x0 + r, y1 - r, -1, 1))
    if 'r' in offen and 'u' in offen:
        ecken.append((x1 - r, y1 - r, 1, 1))

    def innen(x, y):
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            return False
        for cx, cy, sx, sy in ecken:
            if (x - cx) * sx > 0 and (y - cy) * sy > 0:
                if (x - cx) ** 2 + (y - cy) ** 2 > r * r + 1:
                    return False
        return True

    maske = {(x, y) for y in range(N) for x in range(N) if innen(x, y)}
    # An geschlossenen Seiten liegt der Nachbar ausserhalb der Kachel, aber
    # im Boden - dort kein Rand.
    rand1 = {p for p in maske
             if any((p[0] + dx, p[1] + dy) not in maske
                    and 0 <= p[0] + dx < N and 0 <= p[1] + dy < N
                    for dx, dy in SEITEN)}
    rand2 = {p for p in maske - rand1
             if any((p[0] + dx, p[1] + dy) in rand1 for dx, dy in SEITEN)}

    for x, y in maske:
        k.put(x, y, 'stein')
    # Saum
    for x, y in maske:
        if 'l' in offen and x < x0 + 2 + saumtiefe(y, 'l'):
            k.put(x, y, 'stein_tief')
        if 'r' in offen and x > x1 - 2 - saumtiefe(y, 'r'):
            k.put(x, y, 'stein_tief')
        if 'o' in offen and y < y0 + 2 + saumtiefe(x, 'o'):
            k.put(x, y, 'stein_tief')
        if 'u' in offen and not klippe and y > y1 - 2 - saumtiefe(x, 'u'):
            k.put(x, y, 'stein_tief')
    # Klippe: Steinfront zwischen zwei Weinlinien
    if klippe:
        for x, y in maske:
            if y in (14, 15):
                k.put(x, y, 'stein_tief')
            if y == 16:
                k.put(x, y, 'kante')
            if y >= 17:
                k.put(x, y, 'wein' if y == 17 else 'kante')
        ziegel(k, maske, rand2, 18, 28)
    # Rand
    for x, y in rand2:
        oben = (x, y - 1) in rand1
        seitlich = ((x - 1, y) in rand1 or (x + 1, y) in rand1
                    or (x, y + 1) in rand1)
        if seitlich:
            k.put(x, y, 'wein')
        elif oben:
            k.put(x, y, 'stein_tief')
    for x, y in rand1:
        k.put(x, y, 'nacht')
    return maske, rand1, rand2


def ziegel(k, maske, rand2, ya, yb):
    """Mauerwerk auf der Klippe: Reihen zu 3 px, versetzt, mit Fugen."""
    reihe = 0
    y = ya
    while y + 3 <= yb + 1:
        versatz = (reihe * 5 + int(k.wurf() * 3)) % 9
        x = -versatz
        while x < N:
            breite = k.wahl((6, 7, 8, 9))
            fehlt = k.wurf() < 0.12
            for yy in range(y, y + 3):
                for xx in range(x, x + breite):
                    if (xx, yy) in maske and (xx, yy) not in rand2 and not fehlt:
                        if yy == y:
                            col = 'stein_hell'
                        elif yy == y + 2 or xx == x + breite - 1:
                            col = 'stein_tief'
                        else:
                            col = 'stein'
                        k.put(xx, yy, col)
            x += breite + 1
        y += 4
        reihe += 1


def risse(k, offen, maske, anzahl=2):
    """Kurze Weinlinien vom Rand nach innen wie im Vorbild."""
    for seite in offen:
        for _ in range(anzahl):
            t = 4 + int(k.wurf() * 22)
            l = 3 + int(k.wurf() * 3)
            if seite == 'l':
                for i in range(l):
                    k.put(2 + i, t, 'stein_tief')
                    k.put(2 + i, t + 1, 'wein')
                k.put(2 + l, t + 2, 'wein')
            elif seite == 'r':
                for i in range(l):
                    k.put(29 - i, t, 'stein_tief')
                    k.put(29 - i, t + 1, 'wein')
                k.put(29 - l, t + 2, 'wein')
            elif seite == 'o':
                for i in range(l - 1):
                    k.put(t, 2 + i, 'wein')
                k.put(t + 1, 2 + l - 1, 'wein')
            elif seite == 'u':
                for i in range(l - 1):
                    if (t, 15 - i) in maske:
                        k.put(t, 15 - i, 'wein')


# --- Deko ---------------------------------------------------------------------

def frei(k, x, y, w=1, h=1, rand=1):
    """Liegt der Bereich ganz auf ruhigem Boden?"""
    for yy in range(y - rand, y + h + rand):
        for xx in range(x - rand, x + w + rand):
            c = k.get(xx, yy)
            if c not in (C('stein'), C('stein_tief')):
                return False
    return True


def kreuz(k, x, y, hell='stein_hell', mitte='stein_tief'):
    """Kleines Kreuz wie die Blumen im Vorbild - hier ein Pflasterstein."""
    for dx, dy in SEITEN:
        k.put(x + dx, y + dy, hell)
    k.put(x, y, mitte)


def punkte(k, anzahl, col='stein_licht'):
    n = 0
    for _ in range(40):
        if n >= anzahl:
            break
        x, y = 3 + int(k.wurf() * 26), 3 + int(k.wurf() * 26)
        if frei(k, x, y):
            k.put(x, y, col)
            n += 1


def kreuze(k, anzahl):
    n = 0
    for _ in range(40):
        if n >= anzahl:
            break
        x, y = 4 + int(k.wurf() * 24), 4 + int(k.wurf() * 24)
        if frei(k, x - 1, y - 1, 3, 3):
            kreuz(k, x, y)
            n += 1


def riss_lang(k):
    """Ein langer Riss quer ueber die Kachel: dunkle Linie mit Kantenkern
    - leicht schraeg, damit er nicht wie ein Strich wirkt."""
    x = 3 + int(k.wurf() * 5)
    y = 8 + int(k.wurf() * 14)
    linie = []
    for _ in range(16 + int(k.wurf() * 8)):
        if not frei(k, x, y, rand=0):
            break
        linie.append((x, y))
        x += 1
        y += (0, 0, 1, 1, 0, -1)[int(k.wurf() * 6)]
    for i, (px, py) in enumerate(linie):
        k.put(px, py, 'kante' if i % 3 else 'stein_tief')
    for px, py in linie:
        if k.ist(px, py + 1, 'stein') and k.wurf() < 0.4:
            k.put(px, py + 1, 'stein_tief')


def schleimklecks(k, x, y, breite=5):
    """Kleiner Schleimhaufen: Kuppel mit Kante unten und Glanz oben links."""
    h = max(2, breite // 2)
    for dy in range(h + 1):
        halb = breite // 2 - (1 if dy == 0 else 0)
        for dx in range(-halb, halb + 1):
            xx, yy = x + dx, y - h + dy
            col = 'schleim'
            if dy == h or abs(dx) == halb:
                col = 'schleim_dk'
            if dy == h and abs(dx) < halb:
                col = 'schleim_kante'
            k.put(xx, yy, col)
    k.put(x - 1, y - h + 1, 'schleim_hell')
    k.put(x, y - h, 'schleim_hell')
    if breite >= 5:
        k.put(x - 1, y - h, 'schleim_hell')
    # Schatten auf dem Boden
    for dx in range(-(breite // 2), breite // 2 + 1):
        if k.ist(x + dx, y + 1, 'stein'):
            k.put(x + dx, y + 1, 'stein_tief')


def knochen(k, x, y):
    """Kleiner Knochen, liegt quer."""
    for i in range(1, 6):
        k.put(x + i, y, 'knochen' if i < 4 else 'knochen_dk')
        k.put(x + i, y + 1, 'knochen_dk')
    for xx in (x, x + 6):
        k.put(xx, y - 1, 'knochen')
        k.put(xx, y, 'knochen')
        k.put(xx, y + 1, 'knochen_dk')
        k.put(xx, y + 2, 'knochen_tief')
    k.put(x + 1, y - 1, 'knochen')
    k.put(x + 5, y + 2, 'knochen_tief')
    k.put(x + 3, y + 2, 'stein_tief')


def moos(k, x, y):
    """Feuchter Fleck: dunkelgruener Rand, Schleimpunkte innen."""
    for dy in range(-2, 3):
        w = 4 - abs(dy)
        for dx in range(-w, w + 1):
            if not (k.ist(x + dx, y + dy, 'stein')
                    or k.ist(x + dx, y + dy, 'stein_tief')):
                continue
            col = 'schleim_kante' if abs(dx) == w or abs(dy) == 2 else 'schleim_tief'
            k.put(x + dx, y + dy, col)
    k.put(x - 1, y, 'schleim_dk')
    k.put(x + 1, y - 1, 'schleim_dk')


def tropfen(k, x, maske):
    """Schleim laeuft ueber die Klippenkante herunter und endet in einem Tropfen.

    Oben eine flache Pfuetze auf dem Boden, ueber der Kante wird der Strang
    schmaler, unten haengt ein runder Tropfen. Links Licht, rechts Schatten.
    """
    # Pfuetze auf dem Boden (Zeilen 12-15), breiter als der Strang
    for dy, halb in ((12, 1), (13, 2), (14, 3), (15, 3)):
        for dx in range(-halb, halb + 1):
            rand = abs(dx) == halb or dy == 12
            k.put(x + dx, dy, 'schleim_dk' if rand else 'schleim')
    k.put(x - 1, 13, 'schleim_hell')
    k.put(x, 13, 'schleim_hell')
    k.put(x - 1, 14, 'schleim_hell')
    # ueber die Kante: Zeilen 16-17 noch drei breit
    for dy in (16, 17):
        for dx in (-1, 0, 1):
            if (x + dx, dy) in maske:
                k.put(x + dx, dy, 'schleim_hell' if dx == -1 else
                      'schleim' if dx == 0 else 'schleim_dk')
    # Strang: zwei breit, links Licht
    l = 3 + int(k.wurf() * 6)
    for i in range(l):
        yy = 18 + i
        if (x, yy) in maske:
            k.put(x, yy, 'schleim')
        if (x + 1, yy) in maske:
            k.put(x + 1, yy, 'schleim_dk')
    # Tropfen: rund, drei breit, mit Glanz und dunklem Grund
    y = 18 + l
    for dy, (a, b) in enumerate(((-1, 2), (-1, 2), (0, 1))):
        for dx in range(a, b + 1):
            if (x + dx, y + dy) in maske:
                if dy == 2:
                    col = 'schleim_kante'
                elif dx in (a, b):
                    col = 'schleim_dk'
                else:
                    col = 'schleim'
                k.put(x + dx, y + dy, col)
    k.put(x, y, 'schleim_hell')


# --- Schleimlache -------------------------------------------------------------
# Wie der Weg im Vorbild: eine Flaeche im dunkleren Ton mit runden Ecken.
# Die Lache liegt 8 px vom Kachelrand entfernt, so dass Boden und Lache im
# Raster buendig anschliessen.

R_LACHE = 8          # Abstand vom Kachelrand
R_AUSSEN = 12        # Eckradius aussen (konvex)
R_INNEN = 5          # Eckradius innen (konkav)


def lache_maske(art, r=R_AUSSEN):
    R, ri = R_LACHE, R_INNEN
    m = set()
    aussen = (('o', 'l', R + r, R + r), ('o', 'r', N - 1 - R - r, R + r),
              ('u', 'l', R + r, N - 1 - R - r),
              ('u', 'r', N - 1 - R - r, N - 1 - R - r))
    innen = (('io_l', R - 1, R - 1), ('io_r', N - R, R - 1),
             ('iu_l', R - 1, N - R), ('iu_r', N - R, N - R))
    for y in range(N):
        for x in range(N):
            drin = True
            if 'o' in art and y < R:
                drin = False
            if 'u' in art and y > N - 1 - R:
                drin = False
            if 'l' in art and x < R:
                drin = False
            if 'r' in art and x > N - 1 - R:
                drin = False
            for a, b, cx, cy in aussen:
                if a in art and b in art:
                    sx = -1 if b == 'l' else 1
                    sy = -1 if a == 'o' else 1
                    if (x - cx) * sx > 0 and (y - cy) * sy > 0:
                        if (x - cx) ** 2 + (y - cy) ** 2 > r * r + 2:
                            drin = False
            for name, cx, cy in innen:
                if name in art:
                    sx = -1 if name.endswith('l') else 1
                    sy = -1 if name.startswith('io') else 1
                    if (x - cx) * sx >= 0 and (y - cy) * sy >= 0:
                        drin = False
                    elif (x - cx) * sx >= -ri and (y - cy) * sy >= -ri:
                        ex, ey = cx - sx * ri, cy - sy * ri
                        if (x - ex) ** 2 + (y - ey) ** 2 > ri * ri + 2:
                            drin = False
            if drin:
                m.add((x, y))
    return m


def lache(k, art, blasen=2):
    plattform(k, '')
    # Ein Einzelteich ist nur 16 px gross - mit vollem Radius wuerde er zur Raute
    m = lache_maske(art, r=5 if len(art) == 4 else R_AUSSEN)
    for x, y in m:
        k.put(x, y, 'schleim_tief')
    # Lichtkante unten/rechts: die ferne Seite der Lache faengt Licht
    for x, y in m:
        if ((x, y + 1) not in m and y + 1 < N) or ((x + 1, y) not in m and x + 1 < N):
            k.put(x, y, 'schleim_dk')
    # Boden neben der Lache dunkel gesaeumt (feuchter Stein)
    for x, y in list(m):
        for dx, dy in SEITEN:
            if k.ist(x + dx, y + dy, 'stein'):
                k.put(x + dx, y + dy, 'stein_tief')
    # Blasen: Ring aus hellem Schleim mit dunkler Mitte, plus Glanzpunkte
    n = 0
    for _ in range(40):
        if n >= blasen:
            break
        x, y = 3 + int(k.wurf() * 26), 3 + int(k.wurf() * 26)
        if all((x + dx, y + dy) in m for dx in range(-2, 3) for dy in range(-2, 3)) \
                and all(k.ist(x + dx, y + dy, 'schleim_tief')
                        for dx in range(-2, 3) for dy in range(-2, 3)):
            kreuz(k, x, y, 'schleim', 'schleim_tief')
            k.put(x - 1, y - 1, 'schleim_hell')
            n += 1
    for _ in range(3):
        x, y = 2 + int(k.wurf() * 28), 2 + int(k.wurf() * 28)
        if all(k.ist(x + dx, y + dy, 'schleim_tief')
               for dx in range(-1, 2) for dy in range(-1, 2)):
            k.put(x, y, 'schleim_licht')
    return m


# --- Kacheln ------------------------------------------------------------------

LAGEN = {'tl': 'lo', 't': 'o', 'tr': 'ro', 'l': 'l', 'r': 'r',
         'bl': 'lu', 'b': 'u', 'br': 'ru', 'c': ''}
LACHEN = {'tl': ('o', 'l'), 't': ('o',), 'tr': ('o', 'r'), 'l': ('l',),
          'c': (), 'r': ('r',), 'bl': ('u', 'l'), 'b': ('u',),
          'br': ('u', 'r'), 'itl': ('io_l',), 'itr': ('io_r',),
          'ibl': ('iu_l',), 'ibr': ('iu_r',), 'single': ('o', 'u', 'l', 'r')}


def kachel(name):
    k = Kachel(name)
    teil = name.split('_')
    var = int(teil[2]) if len(teil) > 2 else 1
    if teil[0] == 'floor':
        lage = teil[1]
        offen = LAGEN[lage]
        klippe = 'u' in offen
        maske, _, _ = plattform(k, offen, klippe=klippe)
        risse(k, offen, maske, anzahl=2)
        if lage == 'c':
            if var == 1:
                kreuze(k, 2)
                punkte(k, 3)
            elif var == 2:
                riss_lang(k)
                punkte(k, 2)
            elif var == 3:
                schleimklecks(k, 10 + int(k.wurf() * 4), 12 + int(k.wurf() * 4), 5)
                schleimklecks(k, 21, 23, 3)
                punkte(k, 2)
            elif var == 4:
                knochen(k, 8 + int(k.wurf() * 8), 10 + int(k.wurf() * 10))
                kreuze(k, 1)
                punkte(k, 2)
            elif var == 5:
                moos(k, 10 + int(k.wurf() * 10), 10 + int(k.wurf() * 10))
                punkte(k, 3)
        elif klippe:
            kreuze(k, 1)
            punkte(k, 2)
            if var in (3, 5):
                tropfen(k, 6 + int(k.wurf() * 18), maske)
            if var == 4:
                tropfen(k, 5 + int(k.wurf() * 6), maske)
                tropfen(k, 18 + int(k.wurf() * 6), maske)
        else:
            kreuze(k, 1 + (var % 2))
            punkte(k, 2 + var % 3)
            if var == 3:
                schleimklecks(k, 16 + int(k.wurf() * 6), 16 + int(k.wurf() * 6), 4)
    elif teil[0] == 'pool':
        art = LACHEN[teil[1]]
        lache(k, art, blasen=3 if len(teil) > 2 else 2)
        if teil[1] != 'single':
            punkte(k, 2)
    return k


BLATT = (
    ('floor_tl', 'floor_t_1', 'floor_t_2', 'floor_t_3', 'floor_t_4', 'floor_t_5', 'floor_tr'),
    ('floor_l_1', 'pool_tl', 'pool_t', 'pool_tr', 'pool_itl', 'pool_itr', 'floor_r_1'),
    ('floor_l_2', 'pool_l', 'pool_c', 'pool_r', 'pool_ibl', 'pool_ibr', 'floor_r_2'),
    ('floor_l_3', 'pool_bl', 'pool_b', 'pool_br', 'pool_single', 'pool_c_2', 'floor_r_3'),
    ('floor_l_4', 'floor_c_1', 'floor_c_2', 'floor_c_3', 'floor_c_4', 'floor_c_5', 'floor_r_4'),
    ('floor_bl', 'floor_b_1', 'floor_b_2', 'floor_b_3', 'floor_b_4', 'floor_b_5', 'floor_br'),
)


def pruefen(img):
    px = img.load()
    farben = {px[x, y] for y in range(N) for x in range(N) if px[x, y][3]}
    fehler = []
    if any(c[3] not in (0, 255) for c in farben):
        fehler.append('Halbtransparenz')
    fremd = ['%02x%02x%02x' % c[:3] for c in farben
             if '%02x%02x%02x' % c[:3] not in AAP64]
    if fremd:
        fehler.append('nicht AAP-64: ' + ' '.join(fremd))
    return fehler, len(farben)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    ziel = Path(args.out)
    ziel.mkdir(parents=True, exist_ok=True)
    zeilen, spalten = len(BLATT), len(BLATT[0])
    blatt = Image.new('RGBA', (spalten * 33 - 1, zeilen * 33 - 1), (0, 0, 0, 0))
    alle = set()
    for r, reihe in enumerate(BLATT):
        for c, name in enumerate(reihe):
            k = kachel(name)
            duel_anpassen(k.img)
            k.img.save(ziel / (name + '.png'))
            blatt.alpha_composite(k.img, (c * 33, r * 33))
            fehler, n = ([], len({k.px[x, y] for y in range(N) for x in range(N) if k.px[x, y][3]}))
            alle |= {k.px[x, y] for y in range(N) for x in range(N) if k.px[x, y][3]}
            print('  %-12s %2d Farben %s' % (name, n, ', '.join(fehler) or 'ok'))
    blatt.save(ziel / 'slimetower_tileset.png')
    sc = 3
    hg = Image.new('RGBA', (blatt.width * sc, blatt.height * sc), (40, 36, 52, 255))
    hg.alpha_composite(blatt.resize((blatt.width * sc, blatt.height * sc), Image.NEAREST))
    hg.save(ziel / '_vorschau.png')
    print('Blatt %dx%d, %d Farben gesamt -> %s' % (blatt.width, blatt.height, len(alle), ziel))


if __name__ == '__main__':
    main()
