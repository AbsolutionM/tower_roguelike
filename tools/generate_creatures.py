#!/usr/bin/env python3
"""Weitere Gegner im Stil der Schleime (AAP-64): Fledermaus, Auge, Geist,
Spinne, Skelett, Wurm, Irrlicht.

Gleiche Regeln wie bei den Schleimen aus Sprites/Enemies:
    1 px Umriss im dunkelsten Ton der Rampe, Licht von oben rechts (Glanz
    oben, heller Innenrand rechts), Schattenband unten links, Augen aus
    060608 mit weissem Glanzpunkt. Keine 3-Pixel-Regel.

    Fledermaus    Kugelkoerper, Ohren, zwei Fluegel - zwei Frames (auf/ab)
    Auge          schwebender Augapfel mit Iris, Lid und haengenden Nervenstraengen,
                  zwei Frames (Blick links/rechts)
    Geist         Kuppel wie ein Schleim, unten ausgefranst, hohle Augen, zwei
                  Frames (Saum wabert)
    Spinne        Hinterleib und Kopf als Kugeln, acht Beine, vier rote Augen,
                  zwei Frames (Beine wechseln)
    Skelett       Schaedel, Brustkorb mit Rippen, Becken, Knochenarme und -beine,
                  zwei Frames (Schritt)
    Wurm          Made aus fuenf Kugelsegmenten, Kopf mit Fuehlern, zwei Frames
                  (Buckel wandert)
    Irrlicht      schwebende Flamme mit Gesicht, Kern hell, Saum dunkel, zwei
                  Frames (Zunge kippt)
    Koenigsschleim, Totenkopfschleim, Schattenschleim entstehen in
    generate_enemies.py als Sorten.

    python tools/generate_creatures.py --out C:/Users/maxst/Desktop/Sprites/claude/Enemies
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image

from palette import duel_anpassen

SCHWARZ = (6, 6, 8, 255)
WEISS = (255, 255, 255, 255)


def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def umriss(px, innen, kante, w, h):
    for x, y in innen:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in innen and 0 <= n[0] < w and 0 <= n[1] < h:
                px[n] = kante


def kuppel(cx, hw, y0, hoehe):
    """Pixel einer Halbkuppel: Ellipse oben, senkrecht unten."""
    m = set()
    for j in range(hoehe):
        t = (hoehe * 0.6 - j) / (hoehe * 0.6)
        b = hw * math.sqrt(max(0.0, 1.0 - t * t)) if j < hoehe * 0.6 else hw
        for x in range(int(cx - hw) - 1, int(cx + hw) + 2):
            if abs(x - cx) <= b - 0.5:
                m.add((x, y0 + j))
    return m


# --- Fledermaus ---------------------------------------------------------------

BAT = ('221c1a', '403353', '793a80', 'bc4a9b')      # kante, dunkel, koerper, hell


def fledermaus(frame):
    """Fluegel als geschlossene Segel: Oberkante eine Kurve von der Schulter
    zur Spitze, Unterkante zwei Bogen (Membran zwischen den Fingern).
    Frame 0 Fluegel oben, Frame 1 unten."""
    kante, dunkel, koerper, hell = (rgb(c) for c in BAT)
    w, h = 28, 18
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = img.load()
    cx, cy = 13.5, 9.5
    r = 3.4
    innen = {(x, y) for y in range(h) for x in range(w)
             if math.hypot(x - cx, y - cy) <= r}
    # Ohren: zwei Dreiecke
    for sgn in (-1, 1):
        for i in range(3):
            for k in range(3 - i):
                innen.add((int(cx + sgn * (1.0 + k * 0.5 + i * 0.5)), int(cy - r) + 1 - i))
    fluegel = set()
    spann = 10
    for sgn in (-1, 1):
        sx = cx + sgn * (r - 0.5)
        for i in range(spann + 1):
            t = i / spann
            x = int(round(sx + sgn * i))
            if frame == 0:
                oben = cy - 1.5 - 6.0 * t + 2.0 * t * t          # steigt zur Spitze
                unten = oben + 4.5 - 1.5 * t + 1.6 * abs(math.sin(t * math.pi * 2))
            else:
                oben = cy - 0.5 + 3.5 * t
                unten = oben + 4.0 - 1.0 * t + 1.6 * abs(math.sin(t * math.pi * 2))
            for y in range(int(round(oben)), int(round(unten)) + 1):
                if 0 <= x < w and 0 <= y < h:
                    fluegel.add((x, y))
    innen |= fluegel
    umriss(px, innen, kante, w, h)
    for x, y in innen:
        d = math.hypot(x - cx, y - cy)
        if d <= r:
            px[x, y] = hell if (x - cx) + (y - cy) < -1.5 else (koerper if (x - cx) + (y - cy) < 1.5 else dunkel)
        else:
            px[x, y] = dunkel
    # Fingerknochen: drei Strahlen von der Schulter, heller; Oberkante hell
    for sgn in (-1, 1):
        sx = cx + sgn * (r - 0.5)
        for x, y in fluegel:
            if sgn * (x - cx) <= 0:
                continue
            a = math.atan2(y - cy, sgn * (x - sx) + 0.01)
            strahlen = (-0.75, -0.42, -0.1) if frame == 0 else (0.05, 0.3, 0.55)
            if any(abs(a - st) < 0.09 for st in strahlen):
                px[x, y] = koerper
    for x, y in fluegel:
        if (x, y - 1) not in innen:
            px[x, y] = hell
    # Bauch heller, Augen rot, Fangzaehne
    px[int(cx), int(cy) + 1] = koerper
    for ax in (int(cx) - 1, int(cx) + 2):
        px[ax, int(cy) - 1] = rgb('df3e23')
    px[int(cx) - 1, int(cy) + 2] = WEISS
    px[int(cx) + 2, int(cy) + 2] = WEISS
    for x in range(int(cx) - 2, int(cx) + 4):
        if px[x, int(cy) + 2] != WEISS:
            px[x, int(cy) + 2] = kante
    return img



# --- Auge ---------------------------------------------------------------------

AUGE = ('3b1725', '8e5252', 'ba756a', 'e4d2aa', 'fef3c0', 'ffffff')   # kante..glanz
LID = ('73172d', 'b4202a')
ADER = 'df3e23'
IRIS = {'red': ('73172d', 'b4202a', 'df3e23', 'fa6a0a'),
        'blue': ('143464', '285cc4', '249fde', '20d6c7')}
NERV = ('3b1725', 'b4202a', 'fa6a0a')


def auge(art, gross, frame):
    kante, dunkel, mittel, koerper, hell, glanz = (rgb(c) for c in AUGE)
    i_dk, i_mi, i_he, i_ring = (rgb(c) for c in IRIS[art])
    lid_dk, lid_he = (rgb(c) for c in LID)
    n_k, n_d, n_h = (rgb(c) for c in NERV)
    r = 7.0 if gross else 4.6
    w = int(2 * r) + 4
    h = int(2 * r) + (9 if gross else 6)
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = img.load()
    cx, cy = (w - 1) / 2.0, r + 1.5
    innen = {(x, y) for y in range(h) for x in range(w) if math.hypot(x - cx, y - cy) <= r}
    umriss(px, innen, kante, w, h)
    for x, y in innen:
        d = math.hypot(x - cx, y - cy)
        nx, ny = (x - cx) / r, (y - cy) / r
        nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
        licht = nx * 0.45 - ny * 0.6 + nz * 0.66          # Licht von oben rechts
        # vier Stufen von Weiss bis Braun - die Kugel braucht die ganze Spanne
        if licht > 0.8:
            px[x, y] = hell
        elif licht > 0.4:
            px[x, y] = koerper
        elif licht > 0.05:
            px[x, y] = mittel
        else:
            px[x, y] = dunkel
        if licht > 0.95:
            px[x, y] = glanz
    # Iris: verschobener Kreis, Blick nach links/rechts
    blick = (-1 if frame == 0 else 1) * (2 if gross else 1)
    ir = 2.8 if gross else 1.8
    ix, iy = cx + blick, cy + 0.3
    for x, y in innen:
        d = math.hypot(x - ix, y - iy)
        if d <= ir + 0.3:
            px[x, y] = i_dk if d > ir - 0.7 else (i_he if (x - ix) + (y - iy) < -0.5 else i_mi)
            if ir - 1.6 < d <= ir - 0.7 and (x - ix) - (y - iy) > 0.5:
                px[x, y] = i_ring                  # Lichtring an der Irisunterkante
        if d <= (1.2 if gross else 0.6):
            px[x, y] = SCHWARZ
    px[int(round(ix - ir * 0.45)), int(round(iy - ir * 0.55))] = WEISS
    # Adern: kurze rote Zacken vom Irisrand nach aussen auf dem Weiss
    for (wx, wy), lang in (((-1, 0), 2), ((1, -1), 2), ((1, 1), 1)):
        ax, ay = int(round(ix + wx * (ir + 1))), int(round(iy + wy * (ir + 1)))
        for i in range(lang + (1 if gross else 0)):
            p = (ax + wx * i, ay + wy * i + (i % 2 if wy == 0 else 0))
            if p in innen and px[p] in (koerper, hell, mittel):
                px[p] = rgb(ADER)
    # Lid: fleischig, dunkelrot mit roter Unterkante, leicht schraeg - boeser Blick
    for x, y in list(innen):
        if (x, y - 1) not in innen and x < cx + r * 0.6:
            px[x, y] = lid_dk
            if (x, y + 1) in innen and x < cx - r * 0.2:
                px[x, y + 1] = lid_he
    # Nervenstraenge haengen unten, ungleich lang
    if gross:
        straenge = ((cx - r * 0.5, 4), (cx + 0.5, 6), (cx + r * 0.55, 3))
    else:
        straenge = ((cx - 1.5, 3), (cx + 1.5, 4))
    for sx, sl in straenge:
        sx = int(round(sx))
        y0 = max(y for (x, y) in innen if x == sx) + 1
        for i in range(sl):
            x = sx + (1 if i >= 2 else 0)
            if y0 + i < h:
                px[x, y0 + i] = n_h if i == 0 else (n_d if i < sl - 1 else n_k)
                if x - 1 >= 0 and i < sl - 1 and px[x - 1, y0 + i][3] == 0:
                    px[x - 1, y0 + i] = n_k
    return img


# --- Geist --------------------------------------------------------------------

GEIST = ('242234', '403353', '6d758d', '8b93af', 'a6fcdb', 'ffffff')
GEIST_AUGE = '20d6c7'
# kante, dunkel, mittel, koerper, hell, glanz


def geist(gross, frame):
    kante, dunkel, mittel, koerper, hell, glanz = (rgb(c) for c in GEIST)
    w, h = (28, 28) if gross else (20, 20)
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = img.load()
    cx = (w - 1) / 2.0
    hw = (w - 2) / 2.0 - 3                          # Platz fuer Aermchen
    kopf_h = int(h * 0.5)
    innen = kuppel(cx, hw, 1, kopf_h)
    # Rumpf: senkrecht weiter, unten tiefer Wellensaum (Frame versetzt)
    zipfel = 3 if gross else 2
    tiefe = 5 if gross else 3
    for y in range(1 + kopf_h, h - 1):
        for x in range(w):
            if abs(x - cx) > hw - 0.5:
                continue
            t = (x - (cx - hw)) / (2 * hw)
            welle = math.cos(t * math.pi * zipfel * 2 + (0 if frame == 0 else math.pi))
            saum = h - 2 - tiefe * (1 - welle) / 2
            if y <= saum:
                innen.add((x, y))
    umriss(px, innen, kante, w, h)
    for x, y in innen:
        px[x, y] = koerper
    for x, y in innen:
        rand = any((x + dx, y + dy) not in innen for dx, dy in ((1, 0), (-1, 0), (0, -1)))
        unten = (x, y + 1) not in innen
        if y <= 2 and abs(x - cx) < hw * 0.5:
            px[x, y] = glanz
        elif y == 3 and abs(x - cx) < hw * 0.35:
            px[x, y] = hell
        elif rand and x > cx + 1 and y < h - tiefe - 2:
            px[x, y] = hell                         # Lichtkante rechts
        elif unten:
            px[x, y] = dunkel                       # Saum
        elif (h - 2 - y) < (cx + hw - x) * 0.45 + 1:
            # Schattenband wie beim Schleim: unten links, laeuft schraeg hoch
            px[x, y] = dunkel if (h - 2 - y) < (cx + hw - x) * 0.45 - 3 else mittel
        elif rand and x < cx - 1:
            px[x, y] = mittel
        elif rand and y >= h - tiefe - 2:
            px[x, y] = mittel
    # Aermchen: eigene Stummel mit eigenem Umriss, damit sie sich abheben
    ay = 3 + kopf_h - (2 if frame else 0)
    for sgn in (-1, 1):
        arm = set()
        for i in range(4 if gross else 3):
            for j in range(2):
                arm.add((int(cx + sgn * (hw - 1 + i)), ay + j))
        umriss(px, arm, kante, w, h)
        for x, y in arm:
            px[x, y] = hell if sgn > 0 else koerper
        for x, y in arm:                            # Handspitze
            if (x + sgn, y) not in arm:
                px[x, y] = hell if sgn > 0 else mittel
    # Hohle Augen: schwarz mit dunklem Rand, Mund als Oval
    ey = 2 + kopf_h // 2
    for ex in (int(cx) - (3 if gross else 2), int(cx) + (2 if gross else 1)):
        for j in range(3 if gross else 2):
            px[ex, ey + j] = SCHWARZ
            if gross:
                px[ex + 1, ey + j] = SCHWARZ
        px[ex, ey - 1] = kante
        if gross:
            px[ex + 1, ey - 1] = kante
        # Pupille leuchtet tuerkis
        px[ex + (1 if gross else 0), ey + (1 if gross else 0)] = rgb(GEIST_AUGE)
    my = ey + (5 if gross else 3)
    for j in range(2 if gross else 1):
        px[int(cx), my + j] = SCHWARZ
        if gross:
            px[int(cx) + 1, my + j] = SCHWARZ
    px[int(cx), my - 1] = kante
    return img



# --- gemeinsame Schattierung --------------------------------------------------

def kugel_schatten(px, punkte, cx, cy, r, toene):
    """Radiale Schattierung mit dem Schleimlicht (oben rechts).
    toene: dunkel, mittel, koerper, hell, glanz."""
    dunkel, mittel, koerper, hell, glanz = toene
    for x, y in punkte:
        nx, ny = (x - cx) / r, (y - cy) / r
        nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
        licht = nx * 0.45 - ny * 0.6 + nz * 0.66
        if licht > 0.95:
            px[x, y] = glanz
        elif licht > 0.75:
            px[x, y] = hell
        elif licht > 0.35:
            px[x, y] = koerper
        elif licht > 0.0:
            px[x, y] = mittel
        else:
            px[x, y] = dunkel


def kreis(cx, cy, r):
    return {(x, y) for y in range(int(cy - r) - 1, int(cy + r) + 2)
            for x in range(int(cx - r) - 1, int(cx + r) + 2)
            if math.hypot(x - cx, y - cy) <= r}


def linie(a, b):
    """Pixel einer Linie von a nach b (Bresenham, grob)."""
    (x0, y0), (x1, y1) = a, b
    n = int(math.ceil(max(abs(x1 - x0), abs(y1 - y0), 1)))
    return {(int(round(x0 + (x1 - x0) * i / n)), int(round(y0 + (y1 - y0) * i / n)))
            for i in range(n + 1)}


# --- Spinne -------------------------------------------------------------------

SPINNE = ('141013', '242234', '403353', '793a80', 'bc4a9b')   # kante, dunkel, mittel, koerper, hell


def spinne(frame):
    """Beine zwei Pixel dick (Knochen hell, darunter Schatten), erst die
    Beine, dann die Kugeln darueber - so verschwinden die Ansaetze unter dem
    Leib statt ihn zu durchkreuzen."""
    kante, dunkel, mittel, koerper, hell = (rgb(c) for c in SPINNE)
    w, h = 32, 24
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = img.load()
    cx = (w - 1) / 2.0
    ly, ky = 10.0, 17.0
    leib = kreis(cx, ly, 5.4)
    kopf = kreis(cx, ky, 3.2)
    # Beine strahlen in vier Winkeln vom Leib ab (-50, -15, 20, 55 Grad),
    # damit sie sich nicht kreuzen: Oberschenkel nach aussen-oben, Schiene
    # nach unten. Ein Pixel dick - den Umriss gibt spaeter der Godot-Rand.
    beine = set()
    knie_punkte = []
    for sgn in (-1, 1):
        for i, grad in enumerate((-50, -15, 20, 55)):
            a = math.radians(grad)
            hub = 1.5 if (frame == 1) == (i % 2 == 0) else 0.0
            ansatz = (cx + sgn * 4.5 * math.cos(a), ly + 4.5 * math.sin(a))
            knie = (ansatz[0] + sgn * 6.0 * math.cos(a) + sgn * 1.0,
                    ansatz[1] + 6.0 * math.sin(a) - 2.5 - hub)
            fuss = (knie[0] + sgn * 3.0, knie[1] + 5.5 + hub)
            beine |= linie(ansatz, knie) | linie(knie, fuss)
            knie_punkte.append((int(round(knie[0])), int(round(knie[1]))))
    beine = {(x, y) for x, y in beine if 0 <= x < w and 0 <= y < h}
    for x, y in beine:
        px[x, y] = koerper if x > cx else mittel
    for x, y in knie_punkte:
        if (x, y) in beine:
            px[x, y] = hell
    for teil in (leib, kopf):
        umriss(px, teil, kante, w, h)
    for x, y in leib | kopf:
        px[x, y] = koerper
    kugel_schatten(px, leib, cx, ly, 5.4, (dunkel, mittel, koerper, hell, hell))
    kugel_schatten(px, kopf, cx, ky, 3.2, (dunkel, mittel, koerper, hell, hell))
    for x, y in kopf:
        if (x, y - 1) in leib and (x, y - 1) not in kopf:
            px[x, y - 1] = kante
    # Sanduhr auf dem Hinterleib: zwei Dreiecke Spitze an Spitze
    rot, rot_dk = rgb('df3e23'), rgb('b4202a')
    for dx, dy, col in ((-1, -2, rot), (0, -2, rot), (1, -2, rot), (0, -1, rot),
                        (0, 0, rot_dk), (0, 1, rot_dk), (-1, 2, rot_dk), (0, 2, rot_dk), (1, 2, rot_dk)):
        px[int(cx) + dx, int(ly) + dy] = col
    # Augen: zwei grosse orange, zwei kleine rote darueber; Fangzaehne
    px[int(cx) - 1, int(ky) - 1] = rgb('fa6a0a')
    px[int(cx) + 2, int(ky) - 1] = rgb('fa6a0a')
    px[int(cx) - 2, int(ky) - 2] = rot
    px[int(cx) + 3, int(ky) - 2] = rot
    px[int(cx) - 1, int(ky) + 2] = WEISS
    px[int(cx) + 2, int(ky) + 2] = WEISS
    px[int(cx), int(ky) + 1] = dunkel
    px[int(cx) + 1, int(ky) + 1] = dunkel
    return img


# --- Skelett ------------------------------------------------------------------

KNOCHEN = ('423934', '796755', 'a08662', 'c7b08b', 'e4d2aa', 'fef3c0')


def skelett(frame):
    kante, dunkel, mittel, koerper, hell, glanz = (rgb(c) for c in KNOCHEN)
    w, h = 18, 28
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = img.load()
    cx = (w - 1) / 2.0
    hub = 0 if frame == 0 else -1
    schaedel = kreis(cx, 4.5 + hub, 3.6)
    kiefer = {(x, y) for x in range(int(cx) - 2, int(cx) + 3) for y in (8 + hub, 9 + hub)}
    teile = set()
    # Brustkorb: Wirbelsaeule und drei Rippenpaare, Becken darunter
    rumpf_y = 11 + hub
    for j in range(0, 6):
        teile.add((int(cx), rumpf_y + j))
    rippen = set()
    for j in (0, 2, 4):
        for dx in range(-4, 5):
            if abs(dx) >= 1:
                rippen.add((int(cx) + dx, rumpf_y + j + (1 if abs(dx) > 2 else 0)))
    becken = {(int(cx) + dx, rumpf_y + 6 + (1 if abs(dx) == 3 else 0)) for dx in range(-3, 4)}
    # Arme: Oberarm schraeg, Unterarm haengt; Frame 1 schwingt vor
    arme = set()
    for sgn in (-1, 1):
        schulter = (cx + sgn * 4, rumpf_y)
        ellbogen = (cx + sgn * 6, rumpf_y + 4 + (1 if sgn * (1 - 2 * frame) > 0 else -1))
        hand = (cx + sgn * 6.5, rumpf_y + 8)
        arm = linie(schulter, ellbogen) | linie(ellbogen, hand)
        arme |= arm | {(x + 1, y) for x, y in arm}      # zwei Pixel dick wie die Beine
    # Beine: zwei Pixel dicke Knochen, Knie als Gelenk, Fuss drei breit nach
    # vorn. Ein Bein macht den Schritt (Knie vor, Fuss vor), das andere steht.
    beine = set()
    fuesse = set()
    for sgn in (-1, 1):
        schritt = (sgn == -1) == (frame == 0)
        hx = int(cx + sgn * 2)
        knie_y = rumpf_y + 11
        kx = hx + (sgn if schritt else 0)
        for y in range(rumpf_y + 7, knie_y + 1):     # Oberschenkel
            t = (y - rumpf_y - 7) / 4.0
            x = int(round(hx + (kx - hx) * t))
            beine |= {(x, y), (x + 1, y)}
        fx = kx + (sgn if schritt else 0)
        for y in range(knie_y, rumpf_y + 15):        # Schienbein
            t = (y - knie_y) / 3.0
            x = int(round(kx + (fx - kx) * t))
            beine |= {(x, y), (x + 1, y)}
        fy = rumpf_y + 15
        for dx in range(0, 3):                       # Fuss
            fuesse.add((fx + (dx if sgn > 0 else 1 - dx), fy))
    alles = schaedel | kiefer | teile | rippen | becken | arme | beine | fuesse
    alles = {(x, y) for x, y in alles if 0 <= x < w and 0 <= y < h}
    umriss(px, alles, kante, w, h)
    for x, y in alles:
        px[x, y] = koerper
    kugel_schatten(px, schaedel, cx, 4.5 + hub, 3.6, (dunkel, mittel, koerper, hell, glanz))
    for x, y in kiefer:
        px[x, y] = mittel if y == 9 + hub else koerper
    for x, y in rippen:
        px[x, y] = hell if x > cx else koerper
    for x, y in rippen:                              # Rippen sind rund: Unterkante dunkler
        if (x, y + 1) not in rippen and (x, y + 1) in alles and (x, y + 1) not in teile:
            px[x, y + 1] = dunkel
    for x, y in teile:
        px[x, y] = dunkel
    for x, y in becken:
        px[x, y] = mittel
    for x, y in arme | beine:
        px[x, y] = hell if x > cx else koerper
    for x, y in beine:                               # rechte Kante jedes Knochens im Schatten
        if (x + 1, y) not in beine:
            px[x, y] = mittel
    for x, y in fuesse:
        if (x, y) in alles:
            px[x, y] = koerper if x > cx else mittel
    # Gelenke als Knubbel, Augenhoehlen mit rotem Glimmen, Nasenloch, Zaehne
    for sgn in (-1, 1):
        schritt = (sgn == -1) == (frame == 0)
        kx = int(cx + sgn * 2) + (sgn if schritt else 0)
        if (kx, rumpf_y + 11) in alles:
            px[kx, rumpf_y + 11] = glanz
    for hx in (int(cx) - 2, int(cx) + 1):
        for dx in (0, 1):
            px[hx + dx, 4 + hub] = SCHWARZ
            px[hx + dx, 5 + hub] = SCHWARZ
        px[hx + 1, 5 + hub] = rgb('df3e23')
    px[int(cx), 6 + hub] = dunkel
    for x in range(int(cx) - 2, int(cx) + 3):
        px[x, 8 + hub] = kante if x % 2 else koerper
    return img


# --- Wurm ---------------------------------------------------------------------

WUERMER = {
    'pink': ('73172d', 'b4202a', 'e86a73', 'f5a097', 'fad6b8', 'fef3c0'),
    'green': ('24523b', '1a7a3e', '14a02e', '59c135', '9cdb43', 'd6f264'),
}


def wurm(art, frame):
    kante, dunkel, mittel, koerper, hell, glanz = (rgb(c) for c in WUERMER[art])
    w, h = 30, 16
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = img.load()
    boden = 12.0
    segmente = []
    for i in range(5):
        x = 5.5 + i * 4.6
        r = 3.6 if i == 4 else 3.0
        buckel = {0: (1, 2), 1: (2, 3)}[frame]
        y = boden - r - (2.0 if i in buckel else 0.0) - (0.6 if i == 4 else 0.0)
        segmente.append((x, y, r))
    alle = set()
    for x, y, r in segmente:
        alle |= kreis(x, y, r)
    umriss(px, alle, kante, w, h)
    for x, y, r in segmente:
        k = kreis(x, y, r)
        for pnt in k:
            px[pnt] = koerper
        kugel_schatten(px, k, x, y, r, (dunkel, mittel, koerper, hell, glanz))
        # Falte zum vorderen Segment: nur eine Stufe dunkler, nicht die Kante -
        # sonst zerfaellt die Made in Wuerstchen
        for (qx, qy) in k:
            if (qx + 1, qy) not in k and (qx + 1, qy) in alle:
                px[qx, qy] = dunkel if px[qx, qy] in (koerper, mittel) else mittel
    # Rueckenstreifen: dunkle Punkte auf jedem Segment
    for x, y, r in segmente[:4]:
        px[int(x), int(y - r) + 1] = dunkel
        px[int(x) - 1, int(y - r) + 2] = mittel
    # Kopf: Augen, Fuehler, Mund
    hx, hy, hr = segmente[4]
    for dx in (-1, 2):
        px[int(hx) + dx, int(hy)] = SCHWARZ
        px[int(hx) + dx + 1, int(hy)] = SCHWARZ
        px[int(hx) + dx + 1, int(hy) - 1] = WEISS
    px[int(hx) + 1, int(hy) + 2] = kante
    px[int(hx) + 2, int(hy) + 2] = kante
    for dx, dy in ((1, -4), (2, -5), (3, -4), (4, -5)):
        px[int(hx) + dx - 1, int(hy) + dy] = dunkel
    px[int(hx) + 1, int(hy) - 5] = kante
    px[int(hx) + 3, int(hy) - 5] = kante
    # Fuesschen unter jedem Segment
    for x, y, r in segmente[:4]:
        for dx in (-1, 1):
            px[int(x) + dx, int(y + r) + 1] = dunkel
    return img


# --- Irrlicht -----------------------------------------------------------------

FLAMMEN = {
    'orange': ('73172d', 'b4202a', 'df3e23', 'fa6a0a', 'f9a31b', 'ffd541', 'fffc40'),
    'blue': ('143464', '285cc4', '249fde', '20d6c7', 'a6fcdb', 'a6fcdb', 'ffffff'),
}


def irrlicht(art, frame):
    """Flamme als eine Form: unten rund, oben eine Zunge, die je Frame kippt.
    Die Schichten folgen dem Abstand zur Flammenachse - innen Weissgelb,
    aussen Dunkelrot - statt Zeile fuer Zeile, sonst wird es eine Muetze."""
    kante, dunkel, mittel, koerper, hell, licht, glanz = (rgb(c) for c in FLAMMEN[art])
    w, h = 16, 22
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = img.load()
    cx, cy = 7.5, 14.5
    r = 5.0
    spitze = 10.0                                   # Hoehe der Zunge ueber der Kugelmitte
    kipp = -3.0 if frame == 0 else 3.0

    def tiefe(x, y):
        """1 im Kern, 0 am Rand, negativ ausserhalb."""
        if y >= cy:
            return 1.0 - math.hypot(x - cx, y - cy) / r
        t = (cy - y) / spitze                       # 0 an der Kugelmitte, 1 an der Spitze
        if t > 1.0:
            return -1.0
        achse = cx + kipp * t * t
        radius = r * (1.0 - t) ** 0.75
        return 1.0 - abs(x - achse) / max(radius, 0.4)

    innen = {(x, y) for y in range(h) for x in range(w) if tiefe(x + 0.5, y + 0.5) > 0.0}
    umriss(px, innen, kante, w, h)
    for x, y in innen:
        d = tiefe(x + 0.5, y + 0.5)
        if d > 0.62:
            px[x, y] = glanz
        elif d > 0.45:
            px[x, y] = hell
        elif d > 0.3:
            px[x, y] = koerper
        elif d > 0.15:
            px[x, y] = mittel
        else:
            px[x, y] = dunkel
    # Gesicht im hellen Kern, schwarz wie bei den Schleimen: schraege
    # Augen, gezackter Mund
    ey = int(cy) - 1
    for sgn in (-1, 1):
        ex = int(cx) + (0 if sgn < 0 else 1) + sgn * 2
        px[ex, ey] = SCHWARZ
        px[ex, ey + 1] = SCHWARZ
        px[ex - sgn, ey - 1] = SCHWARZ
    my = int(cy) + 2
    for i, x in enumerate(range(int(cx) - 2, int(cx) + 4)):
        px[x, my + (0 if i in (0, 5) else 1)] = SCHWARZ
    return img


def zuschneiden(img):
    kasten = img.getbbox()
    inhalt = img.crop(kasten)
    eng = Image.new('RGBA', (inhalt.width + 2, inhalt.height + 2), (0, 0, 0, 0))
    eng.paste(inhalt, (1, 1))
    return duel_anpassen(eng)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    ziel = Path(args.out)
    ziel.mkdir(parents=True, exist_ok=True)
    bilder = []
    for frame in (0, 1):
        name = 'bat_%d' % (frame + 1)
        img = zuschneiden(fledermaus(frame))
        img.save(ziel / (name + '.png'))
        bilder.append(img)
        print('  %-24s %2dx%d' % (name, img.width, img.height))
    for art in IRIS:
        for gross in (False, True):
            for frame in (0, 1):
                name = '%s%s_eye_%d' % ('giant_' if gross else '', art, frame + 1)
                img = zuschneiden(auge(art, gross, frame))
                img.save(ziel / (name + '.png'))
                bilder.append(img)
                print('  %-24s %2dx%d' % (name, img.width, img.height))
    for gross in (False, True):
        for frame in (0, 1):
            name = '%sghost_%d' % ('giant_' if gross else '', frame + 1)
            img = zuschneiden(geist(gross, frame))
            img.save(ziel / (name + '.png'))
            bilder.append(img)
            print('  %-24s %2dx%d' % (name, img.width, img.height))
    reihe = []
    for frame in (0, 1):
        reihe.append(('spider_%d' % (frame + 1), spinne(frame)))
        reihe.append(('skeleton_%d' % (frame + 1), skelett(frame)))
    for art in WUERMER:
        for frame in (0, 1):
            reihe.append(('%s_worm_%d' % (art, frame + 1), wurm(art, frame)))
    for art in FLAMMEN:
        for frame in (0, 1):
            reihe.append(('%s_wisp_%d' % (art, frame + 1), irrlicht(art, frame)))
    for name, img in reihe:
        img = zuschneiden(img)
        img.save(ziel / (name + '.png'))
        bilder.append(img)
        print('  %-24s %2dx%d' % (name, img.width, img.height))
    sc, spalten, zelle = 4, 4, 30
    zeilen = (len(bilder) + spalten - 1) // spalten
    blatt = Image.new('RGBA', (spalten * zelle * sc, zeilen * zelle * sc), (38, 35, 61, 255))
    for i, im in enumerate(bilder):
        g = im.resize((im.width * sc, im.height * sc), Image.NEAREST)
        blatt.alpha_composite(g, ((i % spalten) * zelle * sc + (zelle * sc - g.width) // 2,
                                  (i // spalten) * zelle * sc + (zelle * sc - g.height) // 2))
    blatt.save(ziel / '_vorschau_creatures.png')


if __name__ == '__main__':
    main()
