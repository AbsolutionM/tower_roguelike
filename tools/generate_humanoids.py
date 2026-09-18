#!/usr/bin/env python3
"""Menschliche und untote Gegner im Stil der Spielfiguren (32x32, Duel).

Gleicher Koerperbau wie die Figuren aus generate_characters (Cowboy-Mass:
Kopfbedeckung, Gesicht, Poncho-Rumpf, Guertel, Hose, Stiefel, Huepf-Zyklus),
ohne Arme wie der Cowboy - was den Gegner ausmacht, sitzt in Kopf und
Rumpf. Nur der Ghul hat lange Arme.

    zombie     graugruene Haut, zerrissenes Hemd, Haarbueschel, hohle Augen
               (eins haengt tiefer), offener Mund
    skeleton   Schaedel mit Rostkappe, Brustkorb mit Rippen statt Rumpf
    ghoul      gebueckt, lila-graue Haut, lange Arme mit Krallen bis zum Boden,
               Ohren, Zahnreihe
    cultist    Kapuzenrobe, Gesicht im Schatten, zwei gluehende Augen,
               gluehendes Augensymbol auf der Brust
    mummy      Bandagen in Streifen, Kopf ganz umwickelt, ein Auge frei,
               lose Bandagenenden
    bandit     Mensch: Kopftuch, Augenbinde, Lederweste, Dolch am Guertel

Vier Richtungen (Front, FSide, BSide, Back) mal zehn Frames, Huepf-Zyklus wie
die Figuren. Ausgabe je Gegner in einen eigenen Ordner. Keine 3-Pixel-Regel.

    python tools/generate_humanoids.py --out C:/Users/maxst/Desktop/Sprites/claude/Enemies
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

import generate_characters as gc
from generate_characters import (C, fuss_spec, gesicht, guertel, helm, hose, kapuze,
                                 put, rumpf, stiefel, stiefel_paar)
from duel import duel_anpassen

# Duel-Toene direkt in die Namensliste der Figuren haengen
gc.AAP.update({
    'moder_hell': '87ae8e', 'moder': '71957d', 'moder_dk': '5b7b69', 'moder_tief': '2d4b47',
    'lumpen_hell': '9e8c79', 'lumpen': '857565', 'lumpen_dk': '625d54', 'lumpen_tief': '434549',
    'hosen_dk': '4a353c', 'hosen_tief': '31222a',
    'bein_hell': 'eadbc9', 'bein': 'ccc3b1', 'bein_dk': 'aea189', 'bein_tief': '857565',
    'rost_hell': 'a6aeba', 'rost': '828b98', 'rost_dk': '626871', 'rost_tief': '434549',
    'ghul_hell': 'b98c93', 'ghul': '977488', 'ghul_dk': '765d73', 'ghul_tief': '554769',
    'robe_hell': '904647', 'robe': '6e2434', 'robe_dk': '5f0926', 'robe_tief': '3b303c',
    'glut': 'ffe949', 'glut_dk': 'f99b4e',
    'binde_hell': 'fff3d6', 'binde': 'eadbc9', 'binde_dk': 'ccc3b1', 'binde_tief': '9e8c79',
    'haut2_hell': 'eadbc9', 'haut2': 'ebbd9d', 'haut2_dk': 'ac6f6e', 'haut2_tief': '77535b',
    'tuch': 'b63c35', 'tuch_dk': '904647', 'tuch_tief': '5f0926',
    'leder2_hell': 'cca96e', 'leder2': 'a96d58', 'leder2_dk': '633432', 'leder2_tief': '4a353c',
    'nacht2': '1d1d21', 'schwarz2': '000000', 'kralle': 'f5f7fa', 'blut': '904647',
    'haar_dk': '31222a', 'haar': '4a353c',
})

MODER = ('moder_hell', 'moder', 'moder_dk', 'moder_tief')
LUMPEN = ('lumpen_hell', 'lumpen', 'lumpen_dk', 'lumpen_tief')
HOSEN = ('lumpen', 'hosen_dk', 'hosen_tief', 'nacht2')
BEIN = ('bein_hell', 'bein', 'bein_dk', 'bein_tief')
ROST = ('rost_hell', 'rost', 'rost_dk', 'rost_tief')
GHUL = ('ghul_hell', 'ghul', 'ghul_dk', 'ghul_tief')
ROBE = ('robe_hell', 'robe', 'robe_dk', 'robe_tief')
BINDE = ('binde_hell', 'binde', 'binde_dk', 'binde_tief')
HAUT2 = ('haut2_hell', 'haut2', 'haut2_dk', 'haut2_tief')
LEDER2 = ('leder2_hell', 'leder2', 'leder2_dk', 'leder2_tief')
TUCH = ('tuch', 'tuch_dk', 'tuch_tief', 'nacht2')
HAAR = ('haar', 'haar_dk', 'haar_dk', 'nacht2')


# --- Bauteile, die die Figuren nicht haben ---------------------------------------

def arm(px, x0, y0, richtung, laenge, ton, hand=None, neigung=0.0):
    """Arm als 2 px dicker Balken von (x0, y0) in Richtung richtung (-1/1);
    neigung senkt (positiv) oder hebt ihn je Pixel. Hand am Ende."""
    hell, mitte, dunkel, kante = (C(t) for t in ton)
    for i in range(laenge):
        x = x0 + richtung * i
        y = y0 + int(round(neigung * i))
        put(px, x, y, mitte if i else dunkel)
        put(px, x, y + 1, dunkel)
        if i == 0:
            put(px, x, y - 1, hell)
    x = x0 + richtung * laenge
    y = y0 + int(round(neigung * laenge))
    if hand:
        hh, hm, hd, hk = (C(t) for t in hand)
        put(px, x, y, hm)
        put(px, x, y + 1, hd)
        put(px, x + richtung, y, hm)
        put(px, x + richtung, y + 1, hk)
    else:
        put(px, x, y, mitte)
        put(px, x, y + 1, kante)


def haengarm(px, x0, y0, sgn, laenge, ton, hand=None, vor=0):
    """Arm haengt aussen am Rumpf: 2 px breit, Schulter hell, Innenseite im
    Schatten. vor > 0 winkelt den Unterarm nach vorn (Zombie, Mumie):
    die letzten Zeilen ruecken nach innen unten. Hand am Ende, 3 px."""
    hell, mitte, dunkel, kante = (C(t) for t in ton)
    x = x0
    for j in range(laenge):
        if vor and j >= laenge - vor:
            x = x0 - sgn * (j - (laenge - vor) + 1)
        put(px, x, y0 + j, mitte if sgn < 0 else dunkel)
        put(px, x + sgn, y0 + j, dunkel if sgn < 0 else kante)
    put(px, x0, y0, hell)
    hy = y0 + laenge
    if hand:
        hh, hm, hd, hk = (C(t) for t in hand)
        put(px, x, hy, hm)
        put(px, x + sgn, hy, hd)
        put(px, x - sgn, hy, hm)
        put(px, x, hy + 1, hk)
    else:
        put(px, x, hy, dunkel)
        put(px, x + sgn, hy, kante)


def haarbueschel(px, cx, y, ton, muster):
    hell, mitte, dunkel, kante = (C(t) for t in ton)
    for dx, dy, t in muster:
        put(px, cx + dx, y + dy, (hell, mitte, dunkel, kante)[t])


def schaedel(px, cx, y0, seitlich=0):
    """Schaedel statt Gesicht: 10 breit, Hoehlen, Nasenloch, Zahnreihe."""
    hh, hm, hd, hk = (C(t) for t in BEIN)
    x0 = cx - 5
    for j in range(5):
        for i in range(10):
            x = x0 + i
            if j == 4 and (i < 2 or i > 7):
                continue
            u = (i + 0.5) / 10
            col = hd if (i in (0, 9) or j == 4) else (hh if u < 0.35 and j < 3 else (hd if u > 0.8 else hm))
            put(px, x, y0 + j, col)
    for ex in (cx - 3 + seitlich, cx + 2 + seitlich):
        for dx in (0, 1):
            put(px, ex + dx, y0 + 1, C('nacht2'))
            put(px, ex + dx, y0 + 2, C('schwarz2'))
        put(px, ex + 1, y0 + 2, C('robe_hell'))         # Glimmen in der Hoehle
    put(px, cx + seitlich // 2, y0 + 3, hk)
    for x in range(x0 + 2, x0 + 8):
        put(px, x, y0 + 4, hk if x % 2 else hh)


def brustkorb(px, cx, y0):
    """Rippen statt Rumpf: Wirbelsaeule, drei Rippenpaare, dahinter Dunkel."""
    hh, hm, hd, hk = (C(t) for t in BEIN)
    for j in range(6):
        b = (11, 11, 11, 10, 9, 9)[j]
        x0 = cx - b // 2 + (1 if b % 2 == 0 else 0)
        for i in range(b):
            put(px, x0 + i, y0 + j, C('nacht2') if 0 < i < b - 1 else C('lumpen_tief'))
    for j in range(6):
        put(px, cx, y0 + j, hd)
    for j in (1, 3, 5):
        for dx in range(1, 5):
            put(px, cx - dx, y0 + j - (1 if dx > 2 else 0), hm if dx < 4 else hd)
            put(px, cx + dx, y0 + j - (1 if dx > 2 else 0), hh if dx < 4 else hm)


# --- Figuren -------------------------------------------------------------------
# Nach dem Cowboy gebaut: keine Arme, Kopfbedeckung / Haar, Gesicht, Poncho-
# Rumpf, Guertel, Hose, zwei Stiefel, Huepf-Laufzyklus in vier Richtungen.
# Jeder Bauer bekommt: px, cx, Zeilen (y_gesicht, y_rumpf, y_guertel, y_hose,
# y_fuss), fuesse ('beide', 'lang', 'keine', 'rechts', 'links'), seitlich
# (0 / 2), hinten (Rueckansicht: kein Gesicht, Hinterkopf).

def fuesse_setzen(px, cx, y_fuss, ton, fuesse):
    """fuesse ist ein Stiefelpaar ((dx, dy) | None, (dx, dy) | None)."""
    stiefel_paar(px, cx, y_fuss, ton, fuesse)


def hinterkopf(px, cx, y0, ton):
    """Rueckansicht des Kopfes: 10 breit, 5 Zeilen, links hell, rechts dunkel."""
    hh, hm, hd, hk = (C(t) for t in ton)
    for j in range(5):
        for i in range(10):
            if j == 4 and (i < 1 or i > 8):
                continue
            u = (i + 0.5) / 10
            col = hk if (i in (0, 9) or j == 4) else (hh if u < 0.3 and j < 3 else (hd if u > 0.7 else hm))
            put(px, cx - 5 + i, y0 + j, col)


def zombie(px, cx, y, fuesse, seitlich, hinten):
    y_gesicht, y_rumpf, y_guertel, y_hose, y_fuss = y
    fuesse_setzen(px, cx, y_fuss, LUMPEN, fuesse)
    hose(px, cx, y_hose, HOSEN)
    guertel(px, cx, y_guertel, ('lumpen', 'lumpen_dk', 'lumpen_tief', 'nacht2'), ('lumpen_dk', 'lumpen_dk'), hinten=hinten)
    rumpf(px, cx, y_rumpf, LUMPEN, None, hinten=hinten, seitlich=seitlich)
    for x, yy in ((cx - 4, y_rumpf + 2), (cx + 2, y_rumpf + 3), (cx - 1, y_rumpf + 5)):
        put(px, x, yy, C('moder_dk'))
        put(px, x + 1, yy, C('moder'))
    put(px, cx + 3, y_rumpf + 5, C('moder_dk'))
    if hinten:
        hinterkopf(px, cx, y_gesicht, HAAR)
    else:
        gesicht(px, cx, y_gesicht, MODER, seitlich=seitlich)
        for ex in (cx - 3 + seitlich, cx + 2 + seitlich):
            dy = 1 if ex > cx else 0
            put(px, ex, y_gesicht + 2 + dy, C('nacht2'))
            put(px, ex + 1, y_gesicht + 2 + dy, C('nacht2'))
            put(px, ex + 1, y_gesicht + 3 + dy, C('moder_tief'))
        if seitlich:                                    # hinteres Auge verdeckt
            hx = cx - 3 + seitlich
            put(px, hx, y_gesicht + 2, C('moder'))
            put(px, hx + 1, y_gesicht + 2, C('moder'))
            put(px, hx + 1, y_gesicht + 3, C('moder'))
        put(px, cx + seitlich // 2, y_gesicht + 4, C('nacht2'))
        put(px, cx + 1 + seitlich // 2, y_gesicht + 4, C('nacht2'))
        put(px, cx + 2 + seitlich // 2, y_gesicht + 4, C('moder_tief'))
    haarbueschel(px, cx, y_gesicht - 1, HAAR,
                 ((-4, 0, 1), (-3, 0, 0), (-2, -1, 1), (-1, 0, 0), (0, -1, 1), (1, 0, 0), (2, 0, 1), (3, -1, 1), (4, 0, 2),
                  (-4, 1, 2), (4, 1, 2), (-5, 1, 2)))


def skeleton(px, cx, y, fuesse, seitlich, hinten):
    y_gesicht, y_rumpf, y_guertel, y_hose, y_fuss = y
    fuesse_setzen(px, cx, y_fuss, BEIN, fuesse)
    hose(px, cx, y_hose, ('bein', 'bein_dk', 'bein_tief', 'nacht2'))
    guertel(px, cx, y_guertel, LEDER2, ('rost', 'rost_hell'), hinten=hinten)
    if hinten:
        rumpf(px, cx, y_rumpf, ('bein_hell', 'bein', 'bein_dk', 'bein_tief'), None, hinten=True)
        for j in range(6):                            # Wirbelsaeule, Schulterblaetter
            put(px, cx, y_rumpf + j, C('bein_tief'))
        for dx in (-3, 3):
            put(px, cx + dx, y_rumpf + 1, C('bein_dk'))
            put(px, cx + dx, y_rumpf + 2, C('bein_dk'))
        hinterkopf(px, cx, y_gesicht, BEIN)
    else:
        brustkorb(px, cx, y_rumpf)
        schaedel(px, cx, y_gesicht, seitlich)
        if seitlich:
            hx = cx - 3 + seitlich
            for dx in (0, 1):
                put(px, hx + dx, y_gesicht + 1, C('bein'))
                put(px, hx + dx, y_gesicht + 2, C('bein'))
    gc.kuppel(px, cx + 0.5, y_gesicht - 0.5, 5.5, 3.6, ROST, oben_nur=True)
    for x in range(cx - 5, cx + 6):
        put(px, x, y_gesicht - 1, C('rost_dk'))
    put(px, cx + 2, y_gesicht - 3, C('rost_tief'))
    put(px, cx + 3, y_gesicht - 2, C('rost_tief'))


def ghoul(px, cx, y, fuesse, seitlich, hinten):
    y_gesicht, y_rumpf, y_guertel, y_hose, y_fuss = y
    y_gesicht += 2; y_rumpf += 2
    fuesse_setzen(px, cx, y_fuss, GHUL, fuesse)
    hose(px, cx, y_hose, ('ghul_dk', 'ghul_tief', 'nacht2', 'nacht2'))
    guertel(px, cx, y_guertel, ('lumpen_dk', 'lumpen_tief', 'nacht2', 'nacht2'), ('lumpen_tief', 'lumpen_tief'), hinten=hinten)
    rumpf(px, cx, y_rumpf, GHUL, None, hinten=hinten, seitlich=seitlich)
    for j in range(3):
        put(px, cx + 1 + j, y_rumpf - 1 + (j % 2), C('ghul_tief'))
    if hinten:
        hinterkopf(px, cx, y_gesicht, GHUL)
    else:
        gesicht(px, cx, y_gesicht, GHUL, seitlich=seitlich)
        for ex in (cx - 3 + seitlich, cx + 2 + seitlich):
            put(px, ex, y_gesicht + 2, C('glut'))
            put(px, ex + 1, y_gesicht + 2, C('nacht2'))
        if seitlich:
            put(px, cx - 3 + seitlich, y_gesicht + 2, C('ghul'))
            put(px, cx - 2 + seitlich, y_gesicht + 2, C('ghul'))
        for x in range(cx - 2, cx + 3):
            put(px, x + seitlich // 2, y_gesicht + 4, C('kralle') if x % 2 else C('nacht2'))
    put(px, cx - 6, y_gesicht + 1, C('ghul_dk'))
    put(px, cx - 6, y_gesicht, C('ghul'))
    put(px, cx + 5, y_gesicht + 1, C('ghul_dk'))
    put(px, cx + 5, y_gesicht, C('ghul'))
    hh, hm, hd, hk = (C(t) for t in GHUL)
    schwung = 1 if (fuesse[0] is None) != (fuesse[1] is None) else 0
    for sgn, x0 in ((-1, cx - 7), (1, cx + 6)):
        laenge = 8 + (schwung if sgn > 0 else 0)
        for j in range(laenge):
            put(px, x0, y_rumpf + 1 + j, hm if sgn < 0 else hd)
            put(px, x0 + sgn, y_rumpf + 1 + j, hd if sgn < 0 else hk)
        put(px, x0, y_rumpf + 1, hh)
        hy = y_rumpf + 1 + laenge
        for k in range(3):
            put(px, x0 + sgn * (k - 1), hy + (1 if k == 1 else 0), C('kralle'))


def cultist(px, cx, y, fuesse, seitlich, hinten):
    y_gesicht, y_rumpf, y_guertel, y_hose, y_fuss = y
    fuesse_setzen(px, cx, y_fuss, ('robe_dk', 'robe_tief', 'nacht2', 'nacht2'), fuesse)
    hose(px, cx, y_hose, ROBE)
    guertel(px, cx, y_guertel, ('leder2_hell', 'leder2', 'leder2_dk', 'leder2_tief'), ('glut_dk', 'glut'), hinten=hinten)
    rumpf(px, cx, y_rumpf, ROBE, None, hinten=hinten, seitlich=seitlich)
    hh, hm, hd, hk = (C(t) for t in ROBE)
    if not hinten:
        put(px, cx - 1, y_rumpf + 2, hk); put(px, cx + 2, y_rumpf + 2, hk)
        put(px, cx, y_rumpf + 2, C('glut_dk')); put(px, cx + 1, y_rumpf + 2, C('glut'))
        for x in range(cx - 1, cx + 3):
            put(px, x, y_rumpf + 3, hk)
        for j in range(5):
            for i in range(10):
                put(px, cx - 5 + i, y_gesicht + j, C('nacht2') if 1 <= i <= 8 else hk)
        for ex in (cx - 3 + seitlich, cx + 2 + seitlich):
            if cx - 5 < ex < cx + 4:
                put(px, ex, y_gesicht + 2, C('glut'))
                put(px, ex, y_gesicht + 3, C('glut_dk'))
    else:
        hinterkopf(px, cx, y_gesicht, ROBE)
    kapuze(px, cx, y_gesicht - 2, ROBE)


def mummy(px, cx, y, fuesse, seitlich, hinten):
    y_gesicht, y_rumpf, y_guertel, y_hose, y_fuss = y
    fuesse_setzen(px, cx, y_fuss, BINDE, fuesse)
    hose(px, cx, y_hose, BINDE)
    guertel(px, cx, y_guertel, ('binde_dk', 'binde_tief', 'lumpen_dk', 'lumpen_tief'), ('binde_tief', 'binde_dk'), hinten=hinten)
    rumpf(px, cx, y_rumpf, BINDE, None, hinten=hinten, seitlich=seitlich)
    hinterkopf(px, cx, y_gesicht, BINDE)               # Kopf ist ganz umwickelt
    for x in range(cx - 5, cx + 5):
        put(px, x, y_gesicht - 1, C('binde_dk'))
        put(px, x, y_gesicht - 2, C('binde'))
    put(px, cx - 5, y_gesicht - 1, C('binde_tief')); put(px, cx + 4, y_gesicht - 2, C('binde_tief'))
    # Bandagen: schraege Baender, zwei Pixel breit, alle fuenf Zeilen
    for yy in range(y_gesicht - 2, y_guertel):
        for x in range(cx - 6, cx + 7):
            if not (0 <= yy < 32 and 0 <= x < 32) or not px[x, yy][3]:
                continue
            r = (x + yy * 2) % 6
            if r == 0:
                put(px, x, yy, C('binde_tief'))
            elif r == 1:
                put(px, x, yy, C('binde_dk'))
    if not hinten:
        # Augenschlitz: dunkler Spalt zwischen den Bandagen, ein Auge
        for x in range(cx - 4 + max(0, seitlich), cx + 5):
            put(px, x, y_gesicht + 2, C('nacht2'))
        put(px, cx + 1 + seitlich // 2, y_gesicht + 2, gc.AUGE)
        put(px, cx + 2 + seitlich // 2, y_gesicht + 2, gc.AUGE)
        put(px, cx + 1 + seitlich // 2, y_gesicht + 3, gc.AUGE)
        put(px, cx + 2 + seitlich // 2, y_gesicht + 3, C('nacht2'))
        put(px, cx + 2 + seitlich // 2, y_gesicht + 1, C('binde_hell'))
    for j in range(3):                                # lose Enden
        put(px, cx - 7, y_gesicht + 3 + j, C('binde_dk' if j < 2 else 'binde_tief'))
    put(px, cx + 6, y_rumpf + 5, C('binde_dk'))
    put(px, cx + 6, y_rumpf + 6, C('binde_tief'))


def bandit(px, cx, y, fuesse, seitlich, hinten):
    y_gesicht, y_rumpf, y_guertel, y_hose, y_fuss = y
    fuesse_setzen(px, cx, y_fuss, LEDER2, fuesse)
    hose(px, cx, y_hose, ('lumpen', 'hosen_dk', 'hosen_tief', 'nacht2'))
    guertel(px, cx, y_guertel, LEDER2, ('rost', 'rost_hell'), hinten=hinten)
    rumpf(px, cx, y_rumpf, ('lumpen_hell', 'lumpen', 'lumpen_dk', 'lumpen_tief'),
          LEDER2 if not hinten else None, hinten=hinten, seitlich=seitlich)
    if not hinten:
        put(px, cx + 4, y_guertel + 1, C('rost_hell'))
        put(px, cx + 4, y_guertel + 2, C('rost'))
        put(px, cx + 4, y_guertel, C('leder2_dk'))
        gesicht(px, cx, y_gesicht, HAUT2, seitlich=seitlich)
        # Halstuch ueber Mund und Nase: rote Binde, unten dunkler
        for x in range(cx - 4, cx + 5):
            put(px, x, y_gesicht + 3, C('tuch'))
            put(px, x, y_gesicht + 4, C('tuch_dk'))
        put(px, cx - 4, y_gesicht + 3, C('tuch_dk')); put(px, cx + 4, y_gesicht + 3, C('tuch_tief'))
        put(px, cx + 3, y_gesicht + 4, C('tuch_tief'))
        # linkes Auge: Klappe mit Riemen; rechtes Auge wie beim Cowboy
        if seitlich == 0:
            put(px, cx - 3, y_gesicht + 2, C('nacht2')); put(px, cx - 2, y_gesicht + 2, C('nacht2'))
            put(px, cx - 3, y_gesicht + 1, C('nacht2')); put(px, cx - 4, y_gesicht + 1, C('nacht2'))
    else:
        hinterkopf(px, cx, y_gesicht, HAAR)
    gc.kuppel(px, cx + 0.5, y_gesicht - 0.5, 5.8, 4.0, TUCH, oben_nur=True)
    for x in range(cx - 5, cx + 6):
        put(px, x, y_gesicht - 1, C('tuch_dk'))
    kx = cx + 6 if not hinten else cx - 6
    put(px, kx, y_gesicht - 1, C('tuch_dk'))          # Knoten
    put(px, kx + (1 if not hinten else -1), y_gesicht, C('tuch_tief'))
    put(px, kx + (1 if not hinten else -1), y_gesicht + 1, C('tuch_dk'))


GEGNER = {'zombie': zombie, 'skeleton_warrior': skeleton, 'ghoul': ghoul,
          'cultist': cultist, 'mummy': mummy, 'bandit': bandit}


# Animationen je Richtung: (Hub, Fuesse, seitlicher Versatz)
ANIMATIONEN = {
    'walk': tuple((h, f, 0) for h, f in gc.SCHRITTE),
    'walk_seite': tuple((h, p, 0) for h, p in gc.SCHRITTE_SEITE),
    'idle': ((0, 'beide', 0), (0, 'beide', 0), (-1, 'beide', 0), (-1, 'beide', 0),
             (0, 'beide', 0), (0, 'beide', 0), (1, 'keine', 0), (0, 'beide', 0)),
    # Angriff: ducken, abspringen, vorschnellen, landen
    'attack': ((1, 'keine', 0), (-3, 'lang', 1), (-1, 'lang', 3), (0, 'beide', 2),
               (0, 'beide', 1), (0, 'beide', 0)),
    # Treffer: zurueckgeworfen, dann zurueck
    'hurt': ((0, 'beide', -2), (1, 'beide', -3), (0, 'beide', -1), (0, 'beide', 0)),
    # Tod: sackt zusammen und sinkt in den Boden
    'death': ((1, 'keine', 0), (3, 'keine', 0), (6, 'keine', 0), (10, 'keine', 0),
              (14, 'keine', 0), (18, 'keine', 0)),
}
NAMEN = {'walk': '%s%d', 'idle': '%s_idle%d', 'attack': '%s_attack%d',
         'hurt': '%s_hurt%d', 'death': '%s_death%d'}


def gegner_frame(bauen, richtung, nr, anim='walk'):
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    px = img.load()
    if anim == 'walk' and richtung in ('FSide', 'BSide'):
        anim = 'walk_seite'
    hub, fuesse, versatz = ANIMATIONEN[anim][nr - 1]
    if isinstance(fuesse, str):
        fuesse = fuss_spec(fuesse)
    if anim == 'death' and hub >= 10:
        # untere Haelfte im Boden: Zeilen unterhalb der Kante 31 fallen weg
        pass
    hinten = richtung in ('Back', 'BSide')
    seitlich = 2 if richtung in ('FSide', 'BSide') else 0
    cx = 15 + (versatz if richtung in ('Front', 'Back') and False else 0)
    if richtung in ('FSide', 'BSide'):
        cx += versatz                            # seitlich: nach vorn/zurueck
    y_gesicht = 14 + hub
    y_rumpf = y_gesicht + 5
    y_guertel = y_rumpf + 6
    y_hose = y_guertel + 1
    y_fuss = y_hose + 1
    bauen(px, cx, (y_gesicht, y_rumpf, y_guertel, y_hose, y_fuss), fuesse, seitlich, hinten)
    if richtung == 'BSide':
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
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
        zeilen = []
        gesamt = 0
        for richtung in ('Front', 'FSide', 'BSide', 'Back'):
            for anim, schritte in ANIMATIONEN.items():
                if anim == 'walk_seite':
                    continue
                reihe = []
                for nr in range(1, len(schritte) + 1):
                    img = gegner_frame(bauen, richtung, nr, anim)
                    img.save(ziel / ((NAMEN[anim] % (richtung, nr)) + '.png'))
                    reihe.append(img)
                zeilen.append(reihe)
                gesamt += len(reihe)
        if args.sheet:
            sc = 3
            blatt = Image.new('RGBA', (10 * 34 * sc, len(zeilen) * 34 * sc), (34, 35, 35, 255))
            for r, reihe in enumerate(zeilen):
                for i, im in enumerate(reihe):
                    g = im.resize((32 * sc, 32 * sc), Image.NEAREST)
                    blatt.alpha_composite(g, (i * 34 * sc + sc, r * 34 * sc + sc))
            blatt.save(ziel / '_sheet.png')
        print('  %-18s %d Frames -> %s' % (name, gesamt, ziel))


if __name__ == '__main__':
    main()
