#!/usr/bin/env python3
"""Bossschleim - der Schleimkoenig, im Stil der Schleime (AAP-64).

Gleiche Bauregeln wie bei den kleinen: Kuppel mit flachem Boden, 1 px
Umriss, Glanzband oben, Lichtkante rechts, Schattenband unten links,
Kernschatten ueber dem Boden. Dazu, was einen Boss ausmacht:

    leidendes Gesicht als Kerben im Gel mit schleimigem Wulst rundum:
    Augen unter haengenden Lidern, offener, nach unten gezogener Mund,
    Sorgenfalten, eine Traene - kein Schwarz, kein Weiss
    zwei Tropfen an den Flanken, Pfuetze am Boden
    Frames: idle_1..3 (atmet: schmal/hoch - breit/flach), attack_1 (platt,
    Maul offen)

    python tools/generate_boss.py --out C:/Users/maxst/Desktop/Sprites/claude/Enemies/boss_slime
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image

from palette import duel_anpassen

# Duel-Palette, gedaempfte Moosreihe: Kante .. Glanz
RAMPE = ('2c3b39', '486859', '5d9b79', '86c69a', 'b5e7cb', 'd0ffea', 'efdd91')
SCHWARZ = (0, 0, 0, 255)
WEISS = (245, 247, 250, 255)


def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


KANTE, DUNKEL, MITTEL, KOERPER, HELL, LICHT, GLANZ = (rgb(c) for c in RAMPE)
GOLD, GOLD_M, GOLD_D, GOLD_K = rgb('ffd541'), rgb('f9a31b'), rgb('fa6a0a'), rgb('73172d')
KNOCHEN, KNOCHEN_S = rgb('c7b08b'), rgb('a08662')   # im Gel: gedaempft
STEINE = (rgb('df3e23'), rgb('249fde'), rgb('bc4a9b'))

W, H = 64, 52


def halbbreite(j, hoehe, hw):
    kopf = hoehe * 0.55
    if j < kopf:
        t = (kopf - j) / kopf
        b = hw * math.sqrt(max(0.0, 1.0 - t * t))
    else:
        b = hw
    if j >= hoehe - 3:
        b -= (j - (hoehe - 4)) * 1.3
    return max(0.0, b)


def boss(frame):
    """frame: 0-2 idle (atmen), 3 attack."""
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    px = img.load()
    # Atmen: breit/flach <-> schmal/hoch; Angriff ganz platt und breit
    breite, hoehe = {0: (50, 36), 1: (48, 38), 2: (50, 36), 3: (56, 30)}[frame]
    cx = (W - 1) / 2.0
    boden = H - 3
    y0 = boden - hoehe
    hw = breite / 2.0
    innen = set()
    for j in range(hoehe):
        b = halbbreite(j, hoehe, hw)
        for x in range(W):
            if abs(x - cx) <= b - 0.5:
                innen.add((x, y0 + j))

    def rand(x, y):
        return any((x + dx, y + dy) not in innen for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))

    for x, y in innen:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in innen and 0 <= n[0] < W and 0 <= n[1] < H:
                px[n] = KANTE
    # Kugelschattierung: der Leib ist eine Kuppel, kein Fleck. Normale aus
    # der Ellipse oben, Zylinder unten; Licht von oben rechts wie bei den
    # kleinen Schleimen. Sechs Stufen von Glanz bis Kante.
    kopf = hoehe * 0.55
    for x, y in innen:
        j = y - y0
        nx = (x - cx) / hw
        ny = (j - kopf) / kopf if j < kopf else 0.0
        d = nx * nx + ny * ny
        nz = math.sqrt(max(0.0, 1.0 - min(1.0, d)))
        lit = nx * 0.42 - ny * 0.62 + nz * 0.66
        # unten dunkler: der Boden liegt im Schatten der Kuppel
        lit -= 0.35 * max(0.0, (j - kopf) / (hoehe - kopf)) ** 1.5
        # mehr Flaeche im Schatten, Licht nur noch oben rechts
        if lit > 0.96:
            col = GLANZ
        elif lit > 0.88:
            col = LICHT
        elif lit > 0.74:
            col = HELL
        elif lit > 0.42:
            col = KOERPER
        elif lit > 0.12:
            col = MITTEL
        else:
            col = DUNKEL
        px[x, y] = col
    # Spiegelglanz: ein klar begrenzter Fleck oben rechts, darunter ein
    # kleiner zweiter - Gel glaenzt, es schimmert nicht nur
    gx, gy = cx + hw * 0.3, y0 + kopf * 0.38
    for x, y in innen:
        d = ((x - gx) / (hw * 0.15)) ** 2 + ((y - gy) / (kopf * 0.2)) ** 2
        if d <= 1.0:
            px[x, y] = GLANZ if d < 0.3 else LICHT      # gedaempfter Glanz
    for x, y in innen:
        d = ((x - gx - hw * 0.16) / (hw * 0.07)) ** 2 + ((y - gy - kopf * 0.42) / (kopf * 0.1)) ** 2
        if d <= 1.0:
            px[x, y] = LICHT
    # Durchscheinen: Gel laesst Licht durch, ueber dem Bodenschatten liegt
    # ein schmaler hellerer Saum (Streulicht von unten)
    for x, y in innen:
        if y == boden - 4 and not rand(x, y) and abs(x - cx) < hw - 4 and px[x, y] in (MITTEL, DUNKEL):
            px[x, y] = KOERPER
    # Lichtkante rechts, Schattenkante links am Rand
    for x, y in innen:
        if rand(x, y) and y < boden - 2:
            if x > cx + 2:
                px[x, y] = LICHT if y < y0 + kopf + 4 else HELL
            elif x < cx - 2:
                px[x, y] = MITTEL if y > y0 + 4 else HELL
    # Kernschatten ueber dem Boden, Bodenzeile wie beim Vorbild
    for x, y in innen:
        if y == boden - 2 and not rand(x, y):
            px[x, y] = DUNKEL
        if (x, y + 1) not in innen:
            px[x, y] = MITTEL if abs(x - cx) < hw - 3 else HELL
    # Pfuetze: der Boss steht in seinem eigenen Schleim
    for x in range(int(cx - hw) - 2, int(cx + hw) + 3):
        for y in (boden, boden + 1):
            if (x, y) not in innen and 0 <= x < W and y < H:
                aussen = abs(x - cx) > hw + 0.5
                px[x, y] = KANTE if (y == boden + 1 or abs(x - cx) > hw + 1.5) else (MITTEL if aussen else DUNKEL)
    # Gesicht als Kerben im Gel (obere Wand im Schatten, untere Lippe im
    # Licht), rundum ein schleimiger Wulst: das Gel hebt sich um jede Kerbe
    # als heller Saum. Augen haengen aussen tief, der Mund steht offen und
    # ist nach unten gezogen - ein Klagen.
    ay = y0 + int(hoehe * 0.42)
    kerben = set()                                    # alle Kerbenpixel fuer den Wulst
    for ax in (int(cx) - 11, int(cx) + 4):
        links = ax < cx
        breite = 7
        for x in range(ax - 1, ax + breite + 1):      # Hoehle leicht eingesunken
            for y in range(ay - 1, ay + 6):
                if (x, y) in innen and px[x, y] in (KOERPER, HELL, LICHT, GLANZ):
                    px[x, y] = MITTEL
        for i in range(breite):
            x = ax + i
            aussen = (breite - 1 - i) if links else i
            lid = ay + aussen // 2
            tiefe = 2 if frame != 3 else 1
            if (x, lid) in innen:
                px[x, lid] = KANTE
                kerben.add((x, lid))
            for t in range(tiefe):
                if (x, lid + 1 + t) in innen:
                    px[x, lid + 1 + t] = DUNKEL if t == 0 else KANTE
                    kerben.add((x, lid + 1 + t))
            if (x, lid + 1 + tiefe) in innen:
                px[x, lid + 1 + tiefe] = HELL         # untere Lippe
        for i in range(4):                            # Sorgenfalte innen hoch
            bx = ax + (i + 1 if links else breite - 2 - i)
            by = ay - 3 + (i // 2)
            if (bx, by) in innen:
                px[bx, by] = DUNKEL
    # Traene links
    tx = int(cx) - 12
    for j in range(3 + (frame % 3)):
        y = ay + 5 + j
        if (tx, y) in innen:
            px[tx, y] = LICHT if j < 2 else GLANZ
    # Mund: offen und nach unten gezogen - Oberkante ein Bogen mit
    # haengenden Winkeln, Innenraum dunkel, Unterkante hell (Lippe)
    my = ay + 8
    mw = 15 if frame != 3 else 19
    hoehe_m = 4 if frame != 3 else 8
    for x in range(int(cx) - mw // 2, int(cx) + mw // 2 + 1):
        t = abs(x - cx) / (mw / 2.0)
        oben = my + int(round(t * t * 3))             # Winkel haengen
        unten = oben + hoehe_m - int(round(t * t * (hoehe_m - 1)))
        for y in range(oben, unten + 1):
            if (x, y) not in innen:
                continue
            if y == oben:
                px[x, y] = KANTE
            elif y == unten:
                px[x, y] = HELL                        # Unterlippe im Licht
            elif y == oben + 1 or t > 0.85:
                px[x, y] = KANTE
            else:
                px[x, y] = DUNKEL
            if y != unten:
                kerben.add((x, y))
        if frame == 3 and abs(x - cx) < 3 and (x, unten - 2) in innen:
            px[x, unten - 2] = rgb('002219')           # Rachen
    # Schleimwulst: das Gel hebt sich um Augen und Mund - heller Saum rundum,
    # unten rechts (zum Licht) am hellsten
    for x, y in list(kerben):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
            n = (x + dx, y + dy)
            if n in innen and n not in kerben and px[n] not in (KANTE, DUNKEL):
                px[n] = LICHT if (dx + dy) > 0 else HELL
    # Tropfen an den Flanken
    for tx, laenge in ((int(cx - hw) + 3, 3), (int(cx + hw) - 5, 2)):
        ty = boden - 1
        for j in range(laenge):
            px[tx, ty + j] = KOERPER if j < laenge - 1 else MITTEL
            px[tx + 1, ty + j] = MITTEL if j < laenge - 1 else DUNKEL
        px[tx, ty + laenge] = KANTE
    return img


def mulde(px, innen, ex, ey, rx, ry, toene, neigung=0.0, tiefe=3):
    """Weiche Vertiefung im Gel: kein Umriss, sondern ein Verlauf. Innen der
    dunkelste Ton, nach aussen heller; die untere Wand faengt Licht (Hell).
    neigung kippt die Mulde (positiv: rechts tiefer). tiefe 1-3: wie viele
    Stufen der Grund unter der Oberflaeche liegt."""
    kante, dunkel, mittel, hell = toene
    for y in range(int(ey - ry) - 2, int(ey + ry) + 3):
        for x in range(int(ex - rx) - 2, int(ex + rx) + 3):
            if (x, y) not in innen:
                continue
            dx = x - ex
            dy = y - ey - neigung * dx
            d = (dx / rx) ** 2 + (dy / ry) ** 2
            if d > 1.35:
                continue
            unten = dy > ry * 0.35                     # untere Wand zum Licht
            if d <= 0.3:
                col = (kante, dunkel, mittel)[3 - tiefe] if tiefe < 3 else kante
            elif d <= 0.7:
                col = dunkel if tiefe >= 2 else mittel
            elif d <= 1.0:
                col = hell if unten and tiefe >= 2 else mittel
            else:
                col = hell if unten else None
            if col:
                px[x, y] = col


def falte(px, innen, x0, y0, dx, dy, laenge, dunkel, hell):
    """Kurze Falte: eine durchgehende dunkle Linie im Gel, am Ende ein
    heller Punkt, wo sich das Gel wieder hebt."""
    zuletzt = None
    for i in range(laenge * 2):
        x = int(round(x0 + dx * i / 2.0))
        y = int(round(y0 + dy * i / 2.0))
        if (x, y) != zuletzt and (x, y) in innen:
            px[x, y] = dunkel
            zuletzt = (x, y)
    if zuletzt and (zuletzt[0], zuletzt[1] + 1) in innen:
        px[zuletzt[0], zuletzt[1] + 1] = hell


def zuschneiden(img):
    kasten = img.getbbox()
    inhalt = img.crop(kasten)
    eng = Image.new('RGBA', (inhalt.width + 2, inhalt.height + 2), (0, 0, 0, 0))
    eng.paste(inhalt, (1, 1))
    return eng


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    ziel = Path(args.out)
    ziel.mkdir(parents=True, exist_ok=True)
    bilder = []
    for frame, name in enumerate(('idle_1', 'idle_2', 'idle_3', 'attack_1')):
        img = duel_anpassen(boss(frame))
        # alle Frames gleich gross, Boden unten buendig
        img.save(ziel / (name + '.png'))
        bilder.append(img)
        print('  %-10s %dx%d' % (name, img.width, img.height))
    sc = 4
    blatt = Image.new('RGBA', (4 * (W + 4) * sc, (H + 4) * sc), (38, 35, 61, 255))
    for i, im in enumerate(bilder):
        g = im.resize((im.width * sc, im.height * sc), Image.NEAREST)
        blatt.alpha_composite(g, (i * (W + 4) * sc + 2 * sc, 2 * sc))
    blatt.save(ziel / '_vorschau.png')


if __name__ == '__main__':
    main()
