#!/usr/bin/env python3
"""Kopiert die Sprites des Nutzers in die Duel-Palette - in einen eigenen
Ordner, die Originale bleiben unberuehrt.

    Sprites/<pfad>.png       -> Sprites/claude/duel/<pfad>.png
    Sprites/<pfad>.aseprite  -> Sprites/claude/duel/<pfad>.png  (erste Ebene)

Jede AAP-64-Farbe wird nach AAP_ZU_DUEL (duel.py) umgesetzt, alles andere
auf die naechste Duel-Farbe gerueckt.

    python tools/duel_kopie.py --quelle C:/Users/maxst/Desktop/Sprites
"""

from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

from PIL import Image

from duel import duel_anpassen


def aseprite_ebene(pfad):
    """Erste Bildebene (Cel) einer .aseprite-Datei als RGBA-Bild."""
    d = open(pfad, 'rb').read()
    _, magic, frames, w, h, tiefe = struct.unpack_from('<IHHHHH', d, 0)
    assert magic == 0xA5E0 and tiefe == 32, pfad
    pos = 128
    fb, fmagic, alt, dauer, _, neu = struct.unpack_from('<IHHHHI', d, pos)
    n = neu if neu else alt
    cp = pos + 16
    bild = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for _ in range(n):
        groesse, typ = struct.unpack_from('<IH', d, cp)
        koerper = d[cp + 6:cp + groesse]
        if typ == 0x2005:
            ebene, x, y, deck, celtyp = struct.unpack_from('<HhhBH', koerper, 0)
            if celtyp == 2:
                cw, ch = struct.unpack_from('<HH', koerper, 16)
                cel = Image.frombytes('RGBA', (cw, ch), zlib.decompress(koerper[20:]))
                bild.alpha_composite(cel, (max(0, x), max(0, y)),
                                     (max(0, -x), max(0, -y)))
        cp += groesse
    return bild


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--quelle', required=True)
    args = ap.parse_args()
    quelle = Path(args.quelle)
    ziel = quelle / 'claude' / 'duel'
    n = 0
    for pfad in sorted(quelle.rglob('*')):
        if 'claude' in pfad.parts or not pfad.is_file():
            continue
        if pfad.suffix.lower() == '.png':
            img = Image.open(pfad).convert('RGBA')
        elif pfad.suffix.lower() == '.aseprite':
            img = aseprite_ebene(pfad)
        else:
            continue
        aus = ziel / pfad.relative_to(quelle).with_suffix('.png')
        aus.parent.mkdir(parents=True, exist_ok=True)
        duel_anpassen(img).save(aus)
        n += 1
    print('%d Dateien nach %s' % (n, ziel))


if __name__ == '__main__':
    main()
