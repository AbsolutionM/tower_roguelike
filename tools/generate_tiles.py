#!/usr/bin/env python3
"""Kachelsatz fuer den Schleimturm (32x32, Resurrect-64-Palette).

Gleiche Methode wie tools/generate_weapons.py: Code, der Pixel setzt,
deterministisch und wiederholbar.

Was der Satz abdeckt, richtet sich nach resources/rooms/layouts/slime_tower.txt:
  .  leer   -> boden_*
  #  Fels   -> wand_* (Neunerblock zum Anstueckeln) und fels_einzeln
  o  Erz    -> erz_schleim
Dazu Zierrat, der den Turm nach Schleimturm aussehen laesst.

UNTERSCHIED ZU DEN WAFFEN: Kacheln lassen keinen Rand frei. Sie stossen
nahtlos aneinander, deshalb wird bis an den Bildrand gezeichnet und die
Musterung wickelt sich ueber die Kante (siehe rausch()).

    python tools/generate_tiles.py            # -> assets/sprites/tiles/
    python tools/generate_tiles.py --out DIR --sheet
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

from PIL import Image

KACHEL = 32

# Palette wird vom Waffengenerator mitbenutzt, damit Waffen und Welt
# aus derselben Farbwelt kommen.
RES64 = {
    'ink': '2e222f', 'plum': '3e3546', 'mauve': '625565', 'dust': '966c6c',
    'tan': 'ab947a', 'wine': '694f62', 'lilac': '7f708a', 'steel': '9babb2',
    'mint': 'c7dcd0', 'white': 'ffffff',
    'blood_dk': '6e2727', 'blood': 'b33831', 'ember': 'ea4f36',
    'amber': 'f79617', 'gold': 'f9c22b', 'sand': 'fbb954',
    'maroon': '7a3045', 'rust_dk': '9e4539', 'rust': 'cd683d',
    'olive_dk': '4c3e24', 'olive': '676633', 'moss': 'a2a947', 'lime': 'd5e04b',
    'pale_yellow': 'fbff86',
    'green_dk': '165a4c', 'green': '239063', 'green_br': '1ebc73',
    'green_lt': '91db69', 'green_pl': 'cddf6c',
    'slate_dk': '313638', 'slate': '374e4a', 'slate_gr': '547e64',
    'sage': '92a984', 'sage_lt': 'b2ba90',
    'teal_dk': '0b5e65', 'teal': '0b8a8f', 'teal_br': '0eaf9b',
    'aqua': '30e1b9', 'aqua_lt': '8ff8e2',
    'navy': '323353', 'indigo': '484a77', 'blue': '4d65b4', 'sky': '8fd3ff',
    'purple_dk': '45293f', 'purple': '6b3e75', 'violet': '905ea9',
    'rose_dk': '753c54', 'rose': 'a24b6f', 'pink': 'cf657f',
    'magenta_dk': '831c5d', 'salmon': 'f68181', 'cream': 'fdcbb0',
}


def C(name):
    h = RES64[name]
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def leer():
    return Image.new('RGBA', (KACHEL, KACHEL), (0, 0, 0, 0))


def px(img, x, y, col):
    """Setzt ein Pixel mit Umlauf - so bleibt jede Musterung nahtlos."""
    img.putpixel((int(x) % KACHEL, int(y) % KACHEL), col)


def fuellen(img, col):
    for y in range(KACHEL):
        for x in range(KACHEL):
            img.putpixel((x, y), col)


def rausch(img, seed, koerner, farben, rand=1):
    """Streut Koerner ueber die Kachel. Weil px() umlaeuft, laufen auch
    Koerner am Rand auf der Nachbarkachel weiter - keine sichtbare Naht."""
    rng = random.Random(seed)
    for _ in range(koerner):
        x, y = rng.randrange(KACHEL), rng.randrange(KACHEL)
        col = C(rng.choice(farben))
        px(img, x, y, col)
        if rand and rng.random() < 0.45:
            px(img, x + rng.choice((-1, 1)), y + rng.choice((-1, 1)), col)


# --- Boden ------------------------------------------------------------------

def boden(img, seed, moosig=0.0):
    """Turmboden: grosse dunkle Platten.

    Der Boden muss sich von der Wand unterscheiden, sonst verschwimmt der
    Raum. Also: dunklere Grundfarbe, groessere Platten (16 px statt 8),
    ruhige Flaeche. Tiefe kommt aus der Fase an jeder Platte, nicht aus
    gestreuten Koernern - Rauschen liest sich als Dreck, nicht als Stein.
    """
    fuellen(img, C('plum'))
    for oy in (0, 16):                                 # zwei Plattenreihen
        for ox in (0, 16):
            for j in range(16):
                for i in range(16):
                    x, y = ox + i, oy + j
                    if i == 0 or j == 0:
                        col = 'ink'                    # Fuge
                    elif i == 1 or j == 1:
                        col = 'mauve'                  # Lichtfase
                    elif i == 15 or j == 15:
                        col = 'ink'
                    elif i == 14 or j == 14:
                        col = 'purple_dk'              # Schattenfase
                    else:
                        col = 'plum'
                    px(img, x, y, C(col))
    rausch(img, seed, 18, ('mauve', 'purple_dk'), rand=0)
    if moosig:
        rng = random.Random(seed + 77)
        for _ in range(int(26 * moosig)):
            x, y = rng.randrange(KACHEL), rng.randrange(KACHEL)
            px(img, x, y, C(rng.choice(('green_dk', 'olive_dk'))))
            if rng.random() < 0.4:
                px(img, x + 1, y, C('green_dk'))


def boden_riss(img, seed):
    boden(img, seed)
    rng = random.Random(seed + 5)
    x, y = 6, 4
    for _ in range(22):                                # Riss laeuft diagonal
        px(img, x, y, C('ink'))
        px(img, x + 1, y, C('plum'))
        x += rng.choice((1, 1, 0))
        y += rng.choice((1, 1, 2))


def boden_gitter(img, seed):
    boden(img, seed)
    for y in range(9, 24):                             # Abflussgitter
        for x in range(9, 24):
            rahmen = x in (9, 23) or y in (9, 23)
            if rahmen:
                px(img, x, y, C('mauve'))
            elif (x - 9) % 4 == 0 or (y - 9) % 7 == 0:
                px(img, x, y, C('slate_dk'))
            else:
                px(img, x, y, C('ink'))
    for x in range(10, 23, 4):                         # Schleim tropft durch
        px(img, x, 22, C('green_dk'))


# --- Wand -------------------------------------------------------------------

STEIN = ('lilac', 'mauve', 'wine', 'plum')


def wandkern(img, seed):
    """Mauerwerk im Verband - heller als der Boden, damit sich Wand und
    Flaeche im Raum unterscheiden lassen."""
    fuellen(img, C('mauve'))
    for reihe, y in enumerate((0, 8, 16, 24)):
        versatz = 0 if reihe % 2 == 0 else 8
        for x in range(KACHEL):
            px(img, x, y, C('plum'))                   # Lagerfuge
            px(img, x, y + 1, C('lilac'))              # Licht auf der Schicht
            px(img, x, y + 7, C('wine'))               # Schatten unten
        for x in (versatz, versatz + 16):              # Stossfuge
            for dy in range(1, 8):
                px(img, x, y + dy, C('plum'))
                px(img, x + 1, y + dy, C('lilac'))
    rausch(img, seed, 22, ('wine', 'lilac'), rand=0)
    rausch(img, seed + 600, 8, ('green_dk',), rand=0)  # Bewuchs in den Fugen


def kante(img, oben=False, unten=False, links=False, rechts=False):
    """Licht- und Schattenkanten an den offenen Seiten eines Wandblocks."""
    for i in range(KACHEL):
        if oben:
            px(img, i, 0, C('steel'))
            px(img, i, 1, C('lilac'))
        if unten:
            px(img, i, KACHEL - 1, C('ink'))
            px(img, i, KACHEL - 2, C('plum'))
        if links:
            px(img, 0, i, C('lilac'))
        if rechts:
            px(img, KACHEL - 1, i, C('plum'))
            px(img, KACHEL - 2, i, C('wine'))


def wand(oben=False, unten=False, links=False, rechts=False, seed=1,
         schleim=False):
    img = leer()
    wandkern(img, seed)
    kante(img, oben, unten, links, rechts)
    if schleim and oben:
        tropfen(img, seed)
    return img


def tropfen(img, seed):
    """Schleim laeuft ueber die Wandoberkante - macht aus Mauerwerk einen
    Schleimturm."""
    rng = random.Random(seed + 31)
    x = 2
    while x < KACHEL:
        tief = rng.randrange(3, 11)
        for y in range(0, tief):
            hell = 'green_br' if y < 2 else ('green' if y < tief - 2 else 'green_dk')
            px(img, x, y, C(hell))
            px(img, x + 1, y, C('green_dk'))
        px(img, x, tief, C('green_dk'))
        x += rng.randrange(4, 8)


def fels_einzeln(seed=9):
    """Frei stehender Fels - das '#' im Layout, wenn es allein steht."""
    img = leer()
    for y in range(KACHEL):
        for x in range(KACHEL):
            dx, dy = x - 15.5, y - 16.5
            d = math.hypot(dx * 1.0, dy * 1.15)
            if d > 13.5:
                continue
            nx, ny = dx / 13.5, dy / 13.5
            nz = math.sqrt(max(0.0, 1.0 - nx * nx - ny * ny))
            hell = nx * -0.5 + ny * -0.5 + nz * 0.71
            if hell > 0.92:
                col = 'steel'
            elif hell > 0.72:
                col = 'lilac'
            elif hell > 0.46:
                col = 'mauve'
            elif hell > 0.22:
                col = 'wine'
            else:
                col = 'plum'
            img.putpixel((x, y), C(col))
    rausch(img, seed, 40, ('wine', 'plum'), rand=0)
    for x, y in ((11, 12), (12, 13), (13, 12), (18, 20), (19, 21)):
        img.putpixel((x, y), C('ink'))                 # Kerben
    for x, y in ((9, 22), (22, 11), (16, 27)):         # Moospolster
        for dx in range(3):
            img.putpixel(((x + dx) % KACHEL, y), C('green_dk'))
    return img


def saeule(seed=12):
    """Saeule - fuer die Saeulen-Layouts im Schleimturm."""
    img = leer()
    for y in range(KACHEL):
        for x in range(7, 25):
            t = (x - 7) / 17.0
            if t < 0.12:
                col = 'lilac'
            elif t < 0.30:
                col = 'steel'
            elif t < 0.62:
                col = 'mauve'
            elif t < 0.84:
                col = 'wine'
            else:
                col = 'plum'
            img.putpixel((x, y), C(col))
    for y in (0, 1, 30, 31):                           # Kapitell und Sockel
        for x in range(5, 27):
            img.putpixel((x, y), C('lilac' if y in (0, 30) else 'mauve'))
    for y in (10, 21):                                 # Ringe
        for x in range(7, 25):
            img.putpixel((x, y), C('plum'))
        for x in range(7, 25, 3):
            img.putpixel((x, y + 1), C('wine'))
    for x in range(9, 24, 4):                          # Schleim am Sockel
        img.putpixel((x, 29), C('green_dk'))
        img.putpixel((x, 28), C('green'))
    return img


# --- Schleim ----------------------------------------------------------------

def schleim_klecks(img, cx, cy, rad, hell='green_br', mitte='green',
                   dunkel='green_dk', glanz='green_lt'):
    """Schleimlache - radial schattiert wie eine Kugel, nicht linear."""
    for y in range(KACHEL):
        for x in range(KACHEL):
            dx, dy = x - cx, (y - cy) * 1.7           # flach gedrueckt
            d = math.hypot(dx, dy)
            if d > rad:
                continue
            nx, ny = dx / rad, dy / rad
            nz = math.sqrt(max(0.0, 1.0 - min(1.0, nx * nx + ny * ny)))
            h = nx * -0.5 + ny * -0.5 + nz * 0.71
            if h > 0.93:
                col = glanz
            elif h > 0.70:
                col = hell
            elif h > 0.40:
                col = mitte
            else:
                col = dunkel
            px(img, x, y, C(col))


def lache(seed=3):
    img = leer()
    boden(img, seed, moosig=0.4)
    schleim_klecks(img, 14, 18, 11)
    schleim_klecks(img, 24, 24, 5)
    for x, y in ((10, 15), (12, 14), (20, 22)):        # Blasen
        px(img, x, y, C('green_pl'))
    return img


def blasen(seed=4):
    img = leer()
    boden(img, seed, moosig=0.7)
    for cx, cy, r in ((9, 10, 5), (21, 14, 7), (14, 25, 6)):
        schleim_klecks(img, cx, cy, r)
        px(img, cx - 1, cy - 1, C('green_pl'))
    return img


def erz_schleim(seed=6):
    """Erzader - das 'o' im Layout: Kristalle im Schleim."""
    img = leer()
    boden(img, seed, moosig=0.3)
    schleim_klecks(img, 16, 19, 10)
    for cx, cy, r in ((13, 15, 4), (20, 17, 3), (16, 22, 3)):
        for y in range(KACHEL):
            for x in range(KACHEL):
                d = abs(x - cx) + abs(y - cy)
                if d > r:
                    continue
                if d <= max(1, r * 0.3):
                    col = 'aqua_lt'
                elif x <= cx and y <= cy:
                    col = 'aqua'
                elif y <= cy:
                    col = 'teal_br'
                elif x <= cx:
                    col = 'teal'
                else:
                    col = 'teal_dk'
                px(img, x, y, C(col))
    return img


KACHELN = [
    ('boden_1', 'Boden', lambda: kachel(boden, 1)),
    ('boden_2', 'Boden, moosig', lambda: kachel(boden, 2, moosig=0.5)),
    ('boden_riss', 'Boden mit Riss', lambda: kachel(boden_riss, 3)),
    ('boden_gitter', 'Boden mit Gitter', lambda: kachel(boden_gitter, 4)),
    ('wand_voll', 'Wand, innen', lambda: wand(seed=5)),
    ('wand_oben', 'Wand, Oberkante', lambda: wand(oben=True, seed=6, schleim=True)),
    ('wand_unten', 'Wand, Unterkante', lambda: wand(unten=True, seed=7)),
    ('wand_links', 'Wand, linke Kante', lambda: wand(links=True, seed=8)),
    ('wand_rechts', 'Wand, rechte Kante', lambda: wand(rechts=True, seed=9)),
    ('wand_ecke_ol', 'Wand, Ecke oben links',
     lambda: wand(oben=True, links=True, seed=10, schleim=True)),
    ('wand_ecke_or', 'Wand, Ecke oben rechts',
     lambda: wand(oben=True, rechts=True, seed=11, schleim=True)),
    ('wand_ecke_ul', 'Wand, Ecke unten links',
     lambda: wand(unten=True, links=True, seed=12)),
    ('wand_ecke_ur', 'Wand, Ecke unten rechts',
     lambda: wand(unten=True, rechts=True, seed=13)),
    ('fels_einzeln', 'Fels, frei stehend', lambda: fels_einzeln(), True),
    ('saeule', 'Saeule', lambda: saeule(), True),
    ('schleim_lache', 'Schleimlache', lambda: lache()),
    ('schleim_blasen', 'Schleimblasen', lambda: blasen()),
    ('erz_schleim', 'Erzader', lambda: erz_schleim()),
]


def kachel(fn, seed, **kw):
    img = leer()
    fn(img, seed, **kw)
    return img


def pruefen(img, name, objekt=False):
    """Flaechenkacheln muessen voll deckend sein - eine Luecke faellt im
    Raster sofort auf. Objekte wie Fels und Saeule stehen dagegen frei und
    duerfen Transparenz haben; bei ihnen wird nur das Gezeichnete geprueft."""
    pal = {tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for h in RES64.values()}
    mangel = []
    daten = list(img.getdata())
    voll = [p for p in daten if p[3]]
    if not objekt and len(voll) != len(daten):
        mangel.append('nicht voll deckend')
    if any(0 < p[3] < 255 for p in daten):
        mangel.append('Teiltransparenz')
    if {p[:3] for p in voll} - pal:
        mangel.append('Farbe ausserhalb der Palette')
    if len({p[:3] for p in voll}) < 4:
        # Schwelle bewusst niedrig: eine hoehere Zahl verleitet dazu,
        # Toene durch gestreute Koerner zu erkaufen statt durch Form
        mangel.append('zu wenig Toene')
    return mangel


def bogen(kacheln, scale=4):
    spalten = 5
    reihen = (len(kacheln) + spalten - 1) // spalten
    blatt = Image.new('RGBA', (spalten * (KACHEL + 1) * scale,
                               reihen * (KACHEL + 1) * scale), (46, 34, 47, 255))
    for i, img in enumerate(kacheln):
        gross = img.resize((KACHEL * scale, KACHEL * scale), Image.NEAREST)
        blatt.alpha_composite(gross, ((i % spalten) * (KACHEL + 1) * scale,
                                      (i // spalten) * (KACHEL + 1) * scale))
    return blatt


def main():
    wurzel = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(wurzel / 'assets' / 'sprites' / 'tiles'))
    ap.add_argument('--sheet', action='store_true')
    args = ap.parse_args()

    aus = Path(args.out)
    aus.mkdir(parents=True, exist_ok=True)

    gemacht = []
    beanstandet = []
    for eintrag in KACHELN:
        kid, name, fn = eintrag[:3]
        objekt = len(eintrag) > 3 and eintrag[3]
        img = fn()
        for satz in pruefen(img, kid, objekt):
            beanstandet.append((kid, satz))
        img.save(aus / ('%s.png' % kid))
        gemacht.append(img)
        farben = len({p[:3] for p in img.getdata()})
        print('  %-16s %-24s %2d Farben' % (kid + '.png', name, farben))

    if args.sheet:
        bogen(gemacht).save(aus / '_sheet.png')

    print('\nFertig: %d Kacheln in %s' % (len(gemacht), aus))
    if beanstandet:
        print('Beanstandungen:')
        for kid, satz in beanstandet:
            print('  %-16s %s' % (kid, satz))
    else:
        print('Pruefung: alles sauber')


if __name__ == '__main__':
    main()
