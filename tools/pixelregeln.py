#!/usr/bin/env python3
"""Gemeinsame Pixelart-Regeln fuer alle Waffengeneratoren.

Kernregel aus resources/weapons/gras_sword.png: hoechstens drei gleichfarbige
Pixel duerfen zusammenhaengen, und zwar nur waagerecht und senkrecht -
diagonal beruehrende Pixel zaehlen nicht. Grosse einfarbige Flaechen lassen
ein Sprite flach und billig wirken; das Aufbrechen erzeugt die typische
Koernung.

Gemessen an den Vorlagen im Projekt:
    gras_sword.png        groesste Flaeche  3 px   (haelt die Regel exakt)
    giant_bone_sword.png  groesste Flaeche  8 px   (haelt sie ungefaehr)

entflechten() bricht zu grosse Flaechen auf, indem einzelne Pixel auf den
naechstliegenden Ton wechseln, der im selben Sprite schon vorkommt. Dadurch
bleibt die Waffe in ihrer Rampe - es entsteht Koernung, keine Fremdfarbe.
"""

from __future__ import annotations


def flaechen(img, nur_deckend=True):
    """Alle gleichfarbigen 4-verbundenen Flaechen als Listen von Punkten."""
    px = img.load()
    w, h = img.size
    gesehen = set()
    gefunden = []
    for y in range(h):
        for x in range(w):
            if (x, y) in gesehen:
                continue
            c = px[x, y]
            if nur_deckend and not c[3]:
                continue
            stapel = [(x, y)]
            gesehen.add((x, y))
            teil = []
            while stapel:
                cx, cy = stapel.pop()
                teil.append((cx, cy))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if (0 <= nx < w and 0 <= ny < h and (nx, ny) not in gesehen
                            and px[nx, ny] == c):
                        gesehen.add((nx, ny))
                        stapel.append((nx, ny))
            gefunden.append((c, teil))
    return gefunden


def groesste_flaeche(img):
    teile = flaechen(img)
    return max((len(t) for _, t in teile), default=0)


def _farbton(c):
    """Farbton und Saettigung grob - reicht, um Materialien zu trennen."""
    r, g, b = c[0] / 255.0, c[1] / 255.0, c[2] / 255.0
    hoch, tief = max(r, g, b), min(r, g, b)
    spanne = hoch - tief
    if spanne < 0.06:
        return None, spanne              # praktisch unbunt
    if hoch == r:
        h = (60 * ((g - b) / spanne)) % 360
    elif hoch == g:
        h = 60 * ((b - r) / spanne) + 120
    else:
        h = 60 * ((r - g) / spanne) + 240
    return h, spanne


def _passt(a, b):
    """Gehoeren zwei Toene zum selben Material?

    Ohne diese Pruefung waehlt das Aufbrechen den farblich naechsten Ton im
    ganzen Sprite - und fuer ein dunkles Grau kann das ein dunkles Braun vom
    Griff sein. Dann sprenkelt Holzfarbe ueber den Stahl.
    """
    ha, sa = _farbton(a)
    hb, sb = _farbton(b)
    if ha is None or hb is None:
        return (ha is None) == (hb is None) or min(sa, sb) < 0.10
    d = abs(ha - hb)
    return min(d, 360 - d) < 45


def _nachbartoene(farbe, vorrat, anzahl=2):
    """Die farblich naechsten anderen Toene aus demselben Material.

    Bewusst kein Griff in die Palette: was schon im Sprite liegt, gehoert zur
    selben Rampe. Zwei Toene statt einem, weil sich sonst zwei Flaechen
    gegenseitig umfaerben koennen - A wird zu B, B wird zu A, und der Lauf
    endet nie.
    """
    r, g, b, _ = farbe
    def abstand(k):
        return (k[0] - r) ** 2 + (k[1] - g) ** 2 + (k[2] - b) ** 2
    gleich, fremd = [], []
    for k in vorrat:
        if k == farbe or k[3] != 255:
            continue
        (gleich if _passt(farbe, k) else fremd).append((abstand(k), k))
    gleich.sort()
    fremd.sort()
    reihe = [k for _, k in gleich] or [k for _, k in fremd]
    return reihe[:anzahl]


BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def _helligkeit(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _randtoene(img, punkte, farbe):
    """Welche Toene grenzen an diese Flaeche an?"""
    px = img.load()
    w, h = img.size
    nachbarn = {}
    for x, y in punkte:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                k = px[nx, ny]
                if k[3] == 255 and k != farbe:
                    nachbarn[k] = nachbarn.get(k, 0) + 1
    return nachbarn


def _abstandsfeld(punkte, quellen):
    """Wie weit ist jeder Punkt der Flaeche von den Quellen entfernt."""
    menge = set(punkte)
    weite = {p: 0 for p in quellen if p in menge}
    rand = list(weite)
    while rand:
        neu = []
        for x, y in rand:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n in menge and n not in weite:
                    weite[n] = weite[(x, y)] + 1
                    neu.append(n)
        rand = neu
    fern = max(weite.values(), default=0) + 1
    return {p: weite.get(p, fern) for p in punkte}


def _verlauf(img, farbe, punkte, max_gruppe):
    """Bricht eine Flaeche als Verlauf auf statt als Schachbrett.

    Die Flaeche wird zwischen ihren hellsten und dunkelsten Nachbarn
    aufgespannt; ueber eine Bayer-Matrix wird der dunklere Ton dort dichter
    gesetzt, wo die dunkle Seite naeher liegt. Dadurch zeigt jedes gesetzte
    Pixel, wie weit die Stelle im Schatten liegt - es hat einen Zweck. Ein
    gleichmaessiges Schachbrett zeigt nur, dass eine Regel erfuellt wurde.
    """
    px = img.load()
    nachbarn = _randtoene(img, punkte, farbe)
    if not nachbarn:
        return False
    passend = [k for k in nachbarn if _passt(farbe, k)] or list(nachbarn)
    dunkler = min(passend, key=_helligkeit)
    heller = max(passend, key=_helligkeit)
    if _helligkeit(dunkler) >= _helligkeit(farbe):
        dunkler = min(passend, key=lambda k: abs(_helligkeit(k) - _helligkeit(farbe)))
    if dunkler == farbe:
        return False

    menge = set(punkte)
    q_dunkel = [p for p in punkte
                if any((p[0] + dx, p[1] + dy) not in menge
                       and _daneben(img, p, dx, dy, dunkler)
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    q_hell = [p for p in punkte
              if any((p[0] + dx, p[1] + dy) not in menge
                     and _daneben(img, p, dx, dy, heller)
                     for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    if not q_dunkel:
        return False
    ad = _abstandsfeld(punkte, q_dunkel)
    ah = _abstandsfeld(punkte, q_hell) if q_hell else {p: 1 for p in punkte}

    for x, y in punkte:
        d, hl = ad[(x, y)], ah[(x, y)]
        anteil = hl / float(d + hl) if (d + hl) else 0.5   # 1 = dicht am Dunklen
        schwelle = (BAYER[y % 4][x % 4] + 0.5) / 16.0
        if anteil > schwelle:
            px[x, y] = dunkler
    return True


def _daneben(img, p, dx, dy, farbe):
    px = img.load()
    nx, ny = p[0] + dx, p[1] + dy
    return (0 <= nx < img.width and 0 <= ny < img.height
            and px[nx, ny] == farbe)


def _greedy(img, max_gruppe, runden):
    """Letzte Instanz: bricht auf, ohne auf die Form zu achten."""
    px = img.load()
    for _ in range(runden):
        teile = flaechen(img)
        zu_gross = [(c, t) for c, t in teile if len(t) > max_gruppe]
        if not zu_gross:
            return True
        vorrat = {c for c, _ in teile}
        for farbe, punkte in zu_gross:
            toene = _nachbartoene(farbe, vorrat)
            if not toene:
                continue
            behalten = set()
            for pt in sorted(punkte):
                gruppe = {pt}
                stapel = [pt]
                while stapel:
                    cx, cy = stapel.pop()
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        n = (cx + dx, cy + dy)
                        if n in behalten and n not in gruppe:
                            gruppe.add(n)
                            stapel.append(n)
                if len(gruppe) <= max_gruppe:
                    behalten.add(pt)
                else:
                    px[pt[0], pt[1]] = toene[(pt[0] + pt[1]) % len(toene)]
    return not any(len(t) > max_gruppe for _, t in flaechen(img))


def _erzwingen(img, max_gruppe):
    px = img.load()
    for farbe, punkte in flaechen(img):
        if len(punkte) <= max_gruppe:
            continue
        toene = _nachbartoene(farbe, {c for c, _ in flaechen(img)}, anzahl=3)
        if not toene:
            continue
        wahl = [farbe] + toene
        for x, y in punkte:
            px[x, y] = wahl[(2 * x + y) % len(wahl)]


def entflechten(img, max_gruppe=3, runden=20, versuche=6):
    """Keine gleichfarbige Flaeche groesser als max_gruppe - waagerecht und
    senkrecht gemessen, diagonal zaehlt nicht.

    Erst wird jede zu grosse Flaeche als Verlauf aufgeloest, damit die
    gesetzten Pixel Schattierung zeigen. Was danach uebrig bleibt, geht durch
    das grobe Verfahren.
    """
    for _ in range(3):
        offen = [(c, t) for c, t in flaechen(img) if len(t) > max_gruppe]
        if not offen:
            return img
        gemacht = False
        for farbe, punkte in offen:
            gemacht |= _verlauf(img, farbe, punkte, max_gruppe)
        if not gemacht:
            break
    for _ in range(versuche):
        if _greedy(img, max_gruppe, runden):
            return img
        _erzwingen(img, max_gruppe)
    _greedy(img, max_gruppe, runden)
    return img


def bericht(img):
    """Kurzer Befund fuer die Pruefung im Generator."""
    gross = groesste_flaeche(img)
    return None if gross <= 3 else 'Flaeche aus %d gleichen Pixeln' % gross
