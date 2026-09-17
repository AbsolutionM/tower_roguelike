#!/usr/bin/env python3
"""Schleime im Stil von Sprites/Enemies/green_slime.png (AAP-64).

Aufbau aus den drei Vorlagen abgelesen (12x9, 22x17, 30x21):
    Kuppel mit flachem Boden, 1 px Umriss im dunkelsten Ton.
    Oben ein Glanzband (fffc40), darunter Licht (d6f264), das nach
    rechts ausläuft - das Licht kommt von oben rechts: rechter Innenrand
    d6f264, linker Innenrand 9cdb43.
    Unten links ein Schattenband (14a02e, dann 1a7a3e), das vom Boden
    schraeg in die Mitte laeuft.
    Oben links eine Blase (Glanzfleck), zwei Augen aus 060608 mit Glanz.

Jede Sorte hat eigene Bauteile, nicht nur eine andere Rampe:
    Alle Gesichter sind leidend wie beim Bossschleim: Schlitzaugen unter
    haengenden Lidern, Sorgenbrauen, eine Traene, Maul nach unten gezogen.
    green   Grundform mit zweiter Blase
    venom   dunkle Flecken, Tropfen unter dem Koerper, schraege Augen, Fangzaehne
    ember   Flammenzungen auf dem Ruecken, Krustenrisse mit Glut, gluehende Augen
    frost   Eissplitter aus dem Ruecken, Facettenband, Funkeln, Rautenaugen
    iron    kantige Kuppel, Panzerplatten mit Nieten, Riss, Strichmund

Keine 3-Pixel-Regel - die gilt fuer Waffen. Der Riesenschleim hat
Flaechen aus 144 gleichen Pixeln.

Ausgabe nur in eigene Ordner:
    python tools/generate_enemies.py --out C:/Users/maxst/Desktop/Sprites/claude/Enemies
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image


# Rampe: kante, dunkel, mittel, koerper, hell, licht, glanz
# Rampen eine Stufe tiefer als bei den Vorlagen - der Turm ist duester
RAMPEN = {
    'green': ('122020', '24523b', '1a7a3e', '14a02e', '59c135', '9cdb43', 'd6f264'),
    'venom': ('242234', '403353', '793a80', '793a80', 'bc4a9b', 'e86a73', 'f5a097'),
    'ember': ('3b1725', '73172d', 'b4202a', 'df3e23', 'fa6a0a', 'f9a31b', 'ffd541'),
    'frost': ('122020', '143464', '285cc4', '249fde', '20d6c7', 'a6fcdb', 'ffffff'),
    'iron': ('141013', '242234', '333941', '4a5462', '6d758d', '8b93af', 'b3b9d1'),
    # Sorten mit eigener Bauart auf der gruenen Rampe
    'king': ('122020', '24523b', '1a7a3e', '14a02e', '59c135', '9cdb43', 'd6f264'),
    'skull': ('122020', '24523b', '1a7a3e', '14a02e', '59c135', '9cdb43', 'd6f264'),
    'shadow': ('060608', '141013', '221c1a', '242234', '403353', '793a80', 'bc4a9b'),
}
NUR_GROSS = {'king'}
SCHWARZ = (6, 6, 8, 255)
WEISS = (255, 255, 255, 255)

# Groessen wie die Vorlagen: (breite, hoehe, augen, blase)
GROESSEN = {
    'small': (12, 9, 1, 1),
    'medium': (22, 17, 2, 2),
    'giant': (30, 21, 3, 3),
}


def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def halbbreite(y, h, hw):
    """Kuppel: oben Ellipse, unten senkrecht, letzte Zeilen eingezogen."""
    kopf = h * 0.55
    if y < kopf:
        t = (kopf - y) / kopf
        b = hw * math.sqrt(max(0.0, 1.0 - t * t))
    else:
        b = hw
    if y >= h - 2:
        b -= (y - (h - 3)) * 1.2
    return max(0.0, b)


RAND = {'green': (0, 0), 'venom': (0, 4), 'ember': (5, 0), 'frost': (5, 0),
        'iron': (0, 0), 'king': (5, 0), 'skull': (0, 0), 'shadow': (4, 0)}


def schleim(art, groesse, muede=False):
    kante, dunkel, mittel, koerper, hell, licht, glanz = (rgb(c) for c in RAMPEN[art])
    w, h, augen, blase = GROESSEN[groesse]
    oben, unten = RAND[art]
    img = Image.new('RGBA', (w, h + oben + unten), (0, 0, 0, 0))
    px = img.load()
    cx = (w - 1) / 2.0
    hw = (w - 2) / 2.0
    innen = set()
    for y in range(1, h - 1):
        b = halbbreite(y - 1, h - 2, hw)
        if art == 'iron' and groesse != 'small':   # kantig: ganze Stufen
            b = math.floor(b)
        for x in range(w):
            if abs(x - cx) <= b - 0.5:
                innen.add((x, y + oben))
    ton = dict(kante=kante, dunkel=dunkel, mittel=mittel, koerper=koerper,
               hell=hell, licht=licht, glanz=glanz)
    _koerper(img, px, innen, ton, art, groesse, muede, w, h, oben, cx, hw,
             augen, blase)
    return img


def _koerper(img, px, innen, ton, art, groesse, muede, w, h, oben, cx, hw,
             augen, blase):
    """Grundkoerper wie bei den Vorlagen; Zeilen sind um oben verschoben."""
    kante, dunkel, mittel, koerper, hell, licht, glanz = (
        ton[k] for k in ('kante', 'dunkel', 'mittel', 'koerper', 'hell',
                         'licht', 'glanz'))
    H = img.height
    # Umriss: alles, was an innen grenzt
    for x, y in innen:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in innen and 0 <= n[0] < w and 0 <= n[1] < H:
                px[n] = kante
    for x, y in innen:
        px[x, y] = koerper

    def rand(x, y):
        return any((x + dx, y + dy) not in innen for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))

    # Innenraender: links hell, rechts licht (Licht von oben rechts)
    for x, y in innen:
        if not rand(x, y):
            continue
        if y >= oben + h - 2:
            continue                         # Bodenzeile bleibt Koerper
        if x > cx + 1:
            px[x, y] = licht
        elif x < cx - 1:
            px[x, y] = hell
    # Glanzband oben: Glanz in der obersten Zeile, Licht darunter
    for x, y in innen:
        if y == oben + 1 and x >= cx - 1:
            px[x, y] = glanz                           # Glanz nur rechts oben
        elif y == oben + 1 or (y == oben + 2 and rand(x, y) and x >= cx - 2):
            px[x, y] = licht
    # Schattenband unten links: laeuft vom Boden schraeg in die Mitte
    tiefe = max(2, h // 4)
    for x, y in innen:
        if rand(x, y) and y < oben + h - 2:
            continue
        rel = (oben + h - 2 - y) - (w - 2 - x) * 0.3   # Hoehe ueber Boden, links hoeher
        if rel < 0:
            px[x, y] = dunkel if y >= oben + h - 2 - tiefe // 2 or x < w * 0.3 else mittel
        elif rel < 1.2:
            px[x, y] = mittel
    # Kernschatten: die Zeile ueber dem Boden ganz dunkel, der Glanz oben
    # zwei Zeilen hoch in der Mitte - mehr Spanne zwischen Licht und
    # Schatten macht die Kuppel rund
    for x, y in innen:
        if y == oben + h - 3 and not rand(x, y):
            px[x, y] = dunkel
        if y == oben + 2 and abs(x - cx) < hw * 0.35 and not rand(x, y):
            px[x, y] = glanz
        if y == oben + 3 and abs(x - cx) < hw * 0.2 and not rand(x, y) and h >= 17:
            px[x, y] = licht
    # Boden: helle Zeile direkt ueber dem Umriss wie beim Vorbild
    for x, y in innen:
        if (x, y + 1) not in innen:
            px[x, y] = koerper if abs(x - cx) < hw - 2 else hell
    # Blase oben links
    bx, by = int(cx - hw * 0.45), oben + 2 + (h // 6)
    if blase == 1:
        px[bx, by] = licht
        px[bx + 1, by] = glanz
    else:
        r = blase
        for y in range(by - r, by + r + 1):
            for x in range(bx - r, bx + r + 1):
                d = math.hypot(x - bx, y - by)
                if (x, y) in innen and d <= r + 0.2:
                    px[x, y] = glanz if d <= r - 1.2 else (licht if x + y < bx + by else hell)
    # Gesicht als Kerben im Gel wie beim Boss, mit schleimigem Wulst
    # rundum: Augen unter haengenden Lidern, offener, nach unten gezogener
    # Mund, Traene. muede: nur die Lidrille.
    ay = oben + h // 2 - (1 if groesse == 'small' else 0)
    breite = {1: 1, 2: 3, 3: 5}[augen]
    ax1 = int(cx) - 1 - breite
    ax2 = int(cx) + 2
    kerben = set()
    for ax, links in ((ax1, True), (ax2, False)):
        if augen >= 2:
            for x in range(ax - 1, ax + breite + 1):
                for y in range(ay - 1, ay + 4):
                    if (x, y) in innen and px[x, y] in (koerper, hell, licht, glanz):
                        px[x, y] = mittel
        for i in range(breite):
            x = ax + i
            aussen = (breite - 1 - i) if links else i
            lid = ay + aussen // 2 if breite > 1 else ay
            if (x, lid) in innen:
                px[x, lid] = kante
                kerben.add((x, lid))
            if muede:
                if (x, lid + 1) in innen:
                    px[x, lid + 1] = hell
                continue
            tiefe = 1 if augen < 3 else 2
            for t in range(tiefe):
                if (x, lid + 1 + t) in innen:
                    px[x, lid + 1 + t] = dunkel if t == 0 else kante
                    kerben.add((x, lid + 1 + t))
            if (x, lid + 1 + tiefe) in innen:
                px[x, lid + 1 + tiefe] = hell
        if augen >= 2:
            bx = ax + (breite - 1 if links else 0)
            if (bx, ay - 1) in innen:
                px[bx, ay - 1] = dunkel
    if augen >= 2:                                     # Traene links
        for j in range(2 if augen == 2 else 3):
            if (ax1, ay + 3 + j) in innen:
                px[ax1, ay + 3 + j] = licht if j < 1 else glanz
    # Mund: offen, Winkel haengen; Innenraum dunkel, Unterlippe hell
    my = ay + augen + 2
    halb = {1: 1, 2: 2, 3: 3}[augen]
    hoehe_m = {1: 1, 2: 2, 3: 3}[augen]
    for x in range(int(cx) - halb, int(cx) + halb + 2):
        t = abs(x - cx - 0.5) / (halb + 0.5)
        oben_ = my + int(round(t * t * 1.5))
        unten_ = oben_ + hoehe_m - int(round(t * t * (hoehe_m - 1)))
        if muede:
            unten_ = oben_
        for y in range(oben_, unten_ + 1):
            if (x, y) not in innen:
                continue
            if y == oben_:
                px[x, y] = kante if augen >= 2 else dunkel
                kerben.add((x, y))
            elif y == unten_:
                px[x, y] = hell
            else:
                px[x, y] = dunkel
                kerben.add((x, y))
    # Schleimwulst um Augen und Mund
    if augen >= 2:
        for x, y in list(kerben):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
                n = (x + dx, y + dy)
                if n in innen and n not in kerben and px[n] not in (kante, dunkel):
                    px[n] = licht if (dx + dy) > 0 else hell
    SORTEN[art](img, px, innen, ton, groesse, muede, w, h, oben, cx, hw, augen, ay)


# --- Bauteile je Sorte --------------------------------------------------------

WEISS_EIS = (218, 224, 234, 255)


def augenpaar(cx, augen):
    return (int(cx) - augen // 2 - 1 - (augen - 1), int(cx) + 2 + (augen - 1))


def fuss(innen, x):
    """Oberster Koerperpunkt in Spalte x."""
    ys = [y for (xx, y) in innen if xx == x]
    return min(ys) if ys else None


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


def _tropfen(px, x, y, ton, H, lang=True):
    """Haengender Tropfen unter dem Koerper. lang: Hals 1 px, Bauch 3 px,
    Spitze - sonst nur eine Beule, die sich gerade loest."""
    if lang:
        form = ((0, 0, 'koerper'), (0, 1, 'koerper'),
                (-1, 2, 'hell'), (0, 2, 'koerper'), (1, 2, 'mittel'),
                (-1, 3, 'koerper'), (0, 3, 'mittel'), (1, 3, 'dunkel'),
                (0, 4, 'kante'))
    else:
        form = ((0, 0, 'koerper'), (1, 0, 'mittel'), (0, 1, 'mittel'), (1, 1, 'dunkel'))
    for dx, dy, name in form:
        if 0 <= y + dy < H:
            px[x + dx, y + dy] = ton[name]


def sorte_green(img, px, innen, ton, groesse, muede, w, h, oben, cx, hw, augen, ay):
    """Zweite, kleinere Blase rechts oben."""
    bx, by = int(cx + hw * 0.35), oben + 3
    if groesse != 'small' and (bx, by) in innen and (bx + 1, by) in innen:
        px[bx, by] = ton['licht']
        px[bx + 1, by] = ton['hell']
        if groesse == 'giant':
            px[bx, by + 1] = ton['hell']


def sorte_venom(img, px, innen, ton, groesse, muede, w, h, oben, cx, hw, augen, ay):
    """Dunkle Flecken, Tropfen unten, schraege Augen, Fangzaehne."""
    H = img.height
    flecken = {'small': ((cx - 3, oben + 5),),
               'medium': ((cx - 5, oben + 5), (cx + 6, oben + 10), (cx - 2, oben + 12)),
               'giant': ((cx - 7, oben + 6), (cx + 8, oben + 12), (cx - 3, oben + 15),
                         (cx + 10, oben + 5), (cx - 10, oben + 12))}[groesse]
    for fx, fy in flecken:
        fx, fy = int(fx), int(fy)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (fx + dx, fy + dy)
            if p in innen and px[p] in (ton['koerper'], ton['mittel']):
                px[p] = ton['dunkel']
    # Fangzaehne unter der Augenzeile
    zy = ay + augen + 1
    for zx in (int(cx) - 1, int(cx) + 2):
        if (zx, zy) in innen:
            px[zx, zy] = WEISS
            if groesse == 'giant' and (zx, zy + 1) in innen:
                px[zx, zy + 1] = WEISS_EIS
    # Tropfen unter dem Boden
    boden = oben + h - 2
    # ein langer Tropfen, sonst Beulen - zwei gleich lange saehen aus wie Beine
    stellen = {'small': ((int(cx) + 2, True),),
               'medium': ((int(cx) - 5, False), (int(cx) + 4, True)),
               'giant': ((int(cx) - 9, False), (int(cx) + 6, True), (int(cx) - 1, False))}[groesse]
    for tx, lang in stellen:
        _tropfen(px, tx, boden, ton, H, lang)


def sorte_ember(img, px, innen, ton, groesse, muede, w, h, oben, cx, hw, augen, ay):
    """Flammenzungen auf dem Ruecken, Krustenrisse mit Glut, gluehende Augen."""
    gold, gold_m, kupfer, dk = rgb('ffd541'), rgb('f9a31b'), rgb('df3e23'), rgb('73172d')
    zungen = {'small': ((int(cx) + 1, 2),),
              'medium': ((int(cx) - 3, 4), (int(cx) + 3, 5), (int(cx) + 7, 3)),
              'giant': ((int(cx) - 7, 4), (int(cx) - 1, 6), (int(cx) + 5, 5),
                        (int(cx) + 10, 3))}[groesse]
    for zx, zl in zungen:
        f = fuss(innen, zx)
        if f is None:
            continue
        for i in range(zl):
            y = f - 1 - i
            if y < 0:
                break
            if i < zl // 2:                     # breiter Fuss: kupfer | gold | kupfer
                px[zx - 1, y] = kupfer if i else gold_m
                px[zx, y] = gold
                px[zx + 1, y] = kupfer if i else gold_m
            elif i < zl - 1:                    # Hals: gold_m | kupfer
                px[zx, y] = gold_m
                px[zx + 1, y] = kupfer
            else:                               # Spitze
                px[zx, y] = kupfer
        if (zx - 2, f) in innen:                # dunkler Saum am Fuss
            px[zx - 2, f] = dk
    # Krustenrisse: Zickzack im unteren Drittel, Glut daneben
    y0 = oben + h - 4
    x = 3
    while x < w - 3:
        y = y0 - ((x * 7 // 3) % 3)
        if (x, y) in innen and (x, y + 1) in innen and (x + 1, y) in innen:
            px[x, y] = dk
            px[x + 1, y] = dk
            px[x, y + 1] = gold if x % 4 == 0 else gold_m
        x += 2 + (x * 5 % 3)
    # Im Grund der Augenkerben glueht es gold
    for (x, y) in list(innen):
        if px[x, y] == ton['dunkel'] and (x, y - 1) in innen and px[x, y - 1] == ton['kante'] \
                and (x, y + 1) in innen and px[x, y + 1] == ton['hell']:
            px[x, y] = gold


def sorte_frost(img, px, innen, ton, groesse, muede, w, h, oben, cx, hw, augen, ay):
    """Eissplitter aus dem Ruecken, Facettenband, Funkeln, Rautenaugen."""
    eis_h, eis_m, eis_d, eis_k = rgb('ffffff'), rgb('a6fcdb'), rgb('249fde'), rgb('143464')
    splitter = {'small': ((int(cx) + 1, 3),),
                'medium': ((int(cx) - 4, 4), (int(cx) + 2, 5), (int(cx) + 6, 3)),
                'giant': ((int(cx) - 8, 4), (int(cx) - 2, 6), (int(cx) + 4, 5),
                          (int(cx) + 9, 3))}[groesse]
    for sx, sl in splitter:
        f = fuss(innen, sx)
        if f is None:
            continue
        for i in range(sl):
            y = f - i
            if y < 0:
                break
            if i < sl - 1:                      # Schaft: dunkel | weiss | hell
                px[sx - 1, y] = eis_d
                px[sx, y] = eis_h
                px[sx + 1, y] = eis_m
                if (sx - 2, y) not in innen:
                    px[sx - 2, y] = eis_k
                if (sx + 2, y) not in innen:
                    px[sx + 2, y] = eis_k
            else:                               # Spitze
                px[sx, y] = eis_h
                px[sx, y - 1] = eis_k
    # Facette: ein kurzer Reflexstreifen rechts oben, schraeg wie die
    # Woelbung - Eis spiegelt in Flaechen, nicht in Punkten
    sx, sy = int(cx + hw * 0.3), oben + 3
    for i in range(3 + h // 6):
        for dx, col in ((0, ton['licht']), (1, ton['hell'])):
            p = (sx + i + dx, sy + i)
            if p in innen and px[p] in (ton['koerper'], ton['mittel']):
                px[p] = col
    # Funkeln
    funkeln = {'small': (), 'medium': ((int(cx) + 5, oben + 8),),
               'giant': ((int(cx) + 7, oben + 8), (int(cx) - 6, oben + 13))}[groesse]
    for fx, fy in funkeln:
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if (fx + dx, fy + dy) in innen:
                px[fx + dx, fy + dy] = eis_h if (dx, dy) == (0, 0) else eis_m


def sorte_iron(img, px, innen, ton, groesse, muede, w, h, oben, cx, hw, augen, ay):
    """Panzersegmente wie bei einer Assel: helle Baender quer ueber den
    Koerper, jedes mit Lichtkante oben, Schattenfuge unten und Nieten."""
    kante, hell, licht = ton['kante'], ton['hell'], ton['licht']
    baender = {'small': ((oben + 2, 2),),
               'medium': ((oben + 3, 3), (oben + 9, 3)),
               'giant': ((oben + 3, 3), (oben + 9, 4), (oben + 15, 3))}[groesse]
    for y0, hoehe in baender:
        for y in range(y0, y0 + hoehe + 1):
            for x in range(w):
                p = (x, y)
                if p not in innen or px[p] == SCHWARZ:
                    continue
                if y == y0 + hoehe:
                    px[p] = kante                     # Fuge
                elif y == y0:
                    px[p] = licht
                elif (x + 1, y) not in innen or (x - 1, y) not in innen:
                    continue                          # Innenrand bleibt
                else:
                    px[p] = hell
        for x in range(int(cx) % 4 + 2, w - 2, 5):    # Nieten
            if (x, y0 + 1) in innen and px[x, y0 + 1] == hell:
                px[x, y0 + 1] = kante
    # Strichmund
    my = ay + augen + 1
    for x in range(int(cx) - 1, int(cx) + 3):
        if (x, my) in innen:
            px[x, my] = kante


def sorte_king(img, px, innen, ton, groesse, muede, w, h, oben, cx, hw, augen, ay):
    """Koenig: Goldkrone mit drei Zacken und Rubin, sitzt schief auf der Kuppel."""
    gold, gold_m, gold_d, saum = rgb('ffd541'), rgb('f9a31b'), rgb('fa6a0a'), rgb('73172d')
    breite = 9 if groesse == 'giant' else 7
    kx = int(cx) - breite // 2 + (1 if groesse == 'giant' else 0)
    f = fuss(innen, int(cx)) or oben + 1
    y0 = f - 1                                       # Kronenreif liegt auf der Kuppel
    for x in range(kx, kx + breite):                 # Reif, zwei Zeilen
        px[x, y0] = gold_m
        px[x, y0 - 1] = gold
    for x in (kx, kx + breite - 1):
        px[x, y0] = gold_d
        px[x, y0 - 1] = gold_d
    zacken = 3 if groesse == 'giant' else 2
    for i, zx in enumerate((kx, kx + breite // 2, kx + breite - 1)):
        for j in range(1, zacken + 1):
            px[zx, y0 - 1 - j] = gold if (j < zacken and i == 1) else gold_m
            if i == 1 and j == 1 and groesse == 'giant':
                px[zx - 1, y0 - 1 - j] = gold
                px[zx + 1, y0 - 1 - j] = gold_m
    px[kx + breite // 2, y0] = saum                  # Rubin
    px[kx + breite // 2, y0 - 1] = rgb('df3e23')
    # Krone wirft Schatten auf die Kuppel
    for x in range(kx, kx + breite):
        if (x, y0 + 1) in innen:
            px[x, y0 + 1] = ton['mittel']
    sorte_green(img, px, innen, ton, groesse, muede, w, h, oben, cx, hw, augen, ay)


def sorte_skull(img, px, innen, ton, groesse, muede, w, h, oben, cx, hw, augen, ay):
    """Ein Totenkopf schwimmt im Schleim - seine Hoehlen sind die Augen."""
    knochen, schatten = rgb('e4d2aa'), rgb('c7b08b')
    breite = {'small': 5, 'medium': 7, 'giant': 9}[groesse]
    hoehe = {'small': 4, 'medium': 6, 'giant': 8}[groesse]
    sx = int(cx) - breite // 2
    sy = ay - (1 if groesse == 'small' else 2)
    for y in range(sy, sy + hoehe):
        for x in range(sx, sx + breite):
            if (x, y) not in innen:
                continue
            j = y - sy
            rand_x = x in (sx, sx + breite - 1)
            if j == 0 and rand_x:
                continue                             # runde Kalotte
            if j >= hoehe - 2 and (x < sx + 1 or x > sx + breite - 2):
                continue                             # Kiefer schmaler
            px[x, y] = schatten if (rand_x or j == hoehe - 1 or x > sx + breite - 2) else knochen
    # Augenhoehlen und Nase
    hy = sy + (1 if groesse == 'small' else 2)
    for hx in (sx + 1, sx + breite - 2):
        px[hx, hy] = SCHWARZ
        if groesse != 'small':
            px[hx, hy + 1] = SCHWARZ
            px[hx + (1 if hx < cx else -1), hy] = SCHWARZ
    px[int(cx), hy + (1 if groesse == 'small' else 2)] = schatten
    # Zaehne: Kante unten mit Luecken
    zy = sy + hoehe - 1
    for x in range(sx + 1, sx + breite - 1):
        if (x, zy) in innen:
            px[x, zy] = knochen if x % 2 else SCHWARZ



def sorte_shadow(img, px, innen, ton, groesse, muede, w, h, oben, cx, hw, augen, ay):
    """Schatten: Rauchfaeden steigen von der Kuppel auf, Augen leuchten weiss."""
    rauch = ton['koerper']
    faeden = {'small': ((int(cx) + 1, 3),),
              'medium': ((int(cx) - 4, 3), (int(cx) + 3, 4)),
              'giant': ((int(cx) - 6, 3), (int(cx) + 1, 5), (int(cx) + 7, 3))}[groesse]
    for fx, fl in faeden:
        f = fuss(innen, fx)
        if f is None:
            continue
        for i in range(fl):
            x = fx + (1 if i % 2 else 0)
            px[x, f - 1 - i] = rauch if i < fl - 1 else ton['dunkel']
            if i == 0:
                px[x - 1, f - 1] = ton['dunkel']
    # Im Grund der Augenkerben glimmt es kalt
    for (x, y) in list(innen):
        if px[x, y] == ton['dunkel'] and (x, y - 1) in innen and px[x, y - 1] == ton['kante'] \
                and (x, y + 1) in innen and px[x, y + 1] == ton['hell']:
            px[x, y] = rgb('20d6c7') if not muede else ton['mittel']


SORTEN = {'green': sorte_green, 'venom': sorte_venom, 'ember': sorte_ember,
          'frost': sorte_frost, 'iron': sorte_iron, 'king': sorte_king,
          'skull': sorte_skull, 'shadow': sorte_shadow}


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
    for art in RAMPEN:
        for groesse in GROESSEN:
            for muede in (False, True):
                if muede and groesse != 'medium':
                    continue
                if art in NUR_GROSS and groesse == 'small':
                    continue
                name = '%s%s_%s_slime' % (groesse + '_' if groesse != 'medium' else '',
                                          'sleepy' if muede else '', art)
                name = name.replace('__', '_').lstrip('_')
                if not muede and groesse == 'medium':
                    name = '%s_slime' % art
                img = zuschneiden(schleim(art, groesse, muede))
                img.save(ziel / (name + '.png'))
                bilder.append(img)
                print('  %-26s %2dx%d' % (name, img.width, img.height))
    sc = 4
    spalten = 4
    zelle = 34
    zeilen = (len(bilder) + spalten - 1) // spalten
    blatt = Image.new('RGBA', (spalten * zelle * sc, zeilen * zelle * sc), (56, 52, 72, 255))
    for i, im in enumerate(bilder):
        g = im.resize((im.width * sc, im.height * sc), Image.NEAREST)
        blatt.alpha_composite(g, ((i % spalten) * zelle * sc + (zelle * sc - g.width) // 2,
                                  (i // spalten) * zelle * sc + (zelle * sc - g.height) // 2))
    blatt.save(ziel / '_vorschau.png')


if __name__ == '__main__':
    main()
