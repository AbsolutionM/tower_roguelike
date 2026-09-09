"""Haengt die erzeugten Sprites an die Waffen und legt neue Waffen an.

Bestehende .tres werden nur ergaenzt (Icon, Haltesprite, Groesse, Drehung),
ihre handgepflegten Werte und Beschreibungen bleiben unangetastet.
Neue Waffen werden komplett erzeugt und in die GameDatabase eingetragen.

Aufruf aus dem Projektwurzelverzeichnis:  python tools/wire_weapons.py
"""
import io, os, re, glob
from PIL import Image

SPRITES = "assets/sprites/weapons"
WEAPONS = "resources/weapons"
DB = "resources/database/game_database.tres"

# Zielgroesse des Sprites auf dem Bildschirm, in Textur-Pixeln gerechnet.
# Die Szene skaliert das Haltesprite anschliessend mit Faktor 5.
TARGET_MELEE = 21.0
TARGET_RANGED = 15.0

CAT = dict(SHORTSWORD=0, BROADSWORD=1, KATANA=2, REVOLVER=3, PISTOL=4, SMG=5,
           SHOTGUN=6, BOW=7, STAFF=8, WHIP=9, THROWN=10, SHIELD=11)
# Peitsche und Schild schlagen zu, statt zu schiessen.
MELEE = {0, 1, 2, 9, 11}

# Klingen zeigen im Sprite nach schraeg oben (-45 Grad), Schusswaffen nach
# rechts (0 Grad). Die Grundhaltung der Szene dreht um +90 Grad; die Werte
# hier gleichen das aus, damit beides zum Ziel zeigt.
ROT_MELEE = -45.0
ROT_RANGED = -90.0

SPECIAL_EXT_PREFIX = '[ext_resource type="Resource" path="res://resources/weapons/specials/'


# Nur Schusswaffen sind im Sprite nach rechts gezeichnet, alles andere
# diagonal nach oben rechts.
GUN_CATEGORIES = {"REVOLVER", "PISTOL", "SMG", "SHOTGUN"}
# Schilde sind flaechig - in Originalgroesse verdecken sie die Figur.
SIZE_OVERRIDE = {"SHIELD": 16.0, "THROWN": 17.0}


def sprite_scale(path, ranged, cat_name=None):
    w, h = Image.open(path).size
    target = SIZE_OVERRIDE.get(cat_name, TARGET_RANGED if ranged else TARGET_MELEE)
    return round(target / max(w, h), 2)


def hold_rotation(cat_name):
    return ROT_RANGED if cat_name in GUN_CATEGORIES else ROT_MELEE


# --- 1. Bestehende Waffen mit ihren Sprites verbinden ----------------------

EXISTING = {
    "sword_melee":      "shortsword_iron",
    "shortsword_bone":  "shortsword_bone",
    "broadsword_iron":  "broadsword_iron",
    "broadsword_titan": "broadsword_titan",
    "katana_moon":      "katana_moon",
    "katana_storm":     "katana_storm",
    "revolver":         "revolver",
    "revolver_heavy":   "revolver_heavy",
    "pistol_burst":     "pistol_burst",
    "pistol_scrap":     "pistol_scrap",
    "smg_buzz":         "smg_buzz",
    "smg_needle":       "smg_needle",
    "shotgun_boom":     "shotgun_boom",
    "shotgun_scatter":  "shotgun_scatter",
}


def set_prop(text, key, value, anchor):
    line = "%s = %s" % (key, value)
    pat = re.compile(r"^%s = .*$" % re.escape(key), re.M)
    if pat.search(text):
        return pat.sub(line, text, count=1)
    m = re.search(r"^%s = .*$" % re.escape(anchor), text, re.M)
    if not m:
        return text.rstrip("\n") + "\n" + line + "\n"
    return text[:m.end()] + "\n" + line + text[m.end():]


def wire_existing():
    for stem, sprite in EXISTING.items():
        path = os.path.join(WEAPONS, stem + ".tres")
        png = os.path.join(SPRITES, sprite + ".png")
        if not (os.path.exists(path) and os.path.exists(png)):
            print("fehlt:", path, png)
            continue

        text = io.open(path, encoding="utf-8").read()
        ranged = "is_melee = true" not in text

        # Alte Verweise auf Platzhalter-Grafiken entfernen.
        text = re.sub(r'^\[ext_resource type="Texture2D".*\]\n', "", text, flags=re.M)
        text = re.sub(r'^(icon|hold_texture) = ExtResource\("[^"]+"\)\n', "", text, flags=re.M)

        ids = [int(i) for i in re.findall(r'id="(\d+)_', text)]
        n = max(ids) + 1 if ids else 2
        ext = '[ext_resource type="Texture2D" path="res://%s/%s.png" id="%d_art"]' % (SPRITES, sprite, n)

        lines = text.split("\n")
        last = max(i for i, l in enumerate(lines) if l.startswith("[ext_resource"))
        lines.insert(last + 1, ext)
        text = "\n".join(lines)

        ref = 'ExtResource("%d_art")' % n
        text = set_prop(text, "icon", ref, "category")
        text = set_prop(text, "hold_texture", ref, "icon")
        cat_name = EXISTING_CATEGORY[stem]
        text = set_prop(text, "hold_scale", "%.2f" % sprite_scale(png, ranged, cat_name), "hold_texture")
        text = set_prop(text, "hold_rotation_degrees", "%.1f" % hold_rotation(cat_name), "hold_scale")

        # Sonderschlag der Klasse anhaengen. Alte Eintraege raus,
        # damit ein zweiter Lauf nicht doppelt schreibt.
        keep = []
        for line in text.split(chr(10)):
            if line.startswith(SPECIAL_EXT_PREFIX):
                continue
            if line.startswith('special = ExtResource('):
                continue
            keep.append(line)
        text = chr(10).join(keep)

        sp = special_path(stem, EXISTING_CATEGORY[stem])
        ext_sp = '[ext_resource type="Resource" path="%s" id="%d_special"]' % (sp, n + 1)
        keep = text.split(chr(10))
        last = max(i for i, l in enumerate(keep) if l.startswith('[ext_resource'))
        keep.insert(last + 1, ext_sp)
        text = chr(10).join(keep)
        text = set_prop(text, 'special', 'ExtResource("%d_special")' % (n + 1), 'damage')

        io.open(path, "w", encoding="utf-8", newline="\n").write(text)
        print("verbunden: %-20s -> %s" % (stem, sprite))


# Standard-Sonderschlag je Klasse.
CLASS_SPECIAL = {
    "SHORTSWORD": "cls_shortsword", "BROADSWORD": "cls_broadsword",
    "KATANA": "cls_katana", "REVOLVER": "cls_revolver", "PISTOL": "cls_pistol",
    "SMG": "cls_smg", "SHOTGUN": "cls_shotgun", "BOW": "cls_bow",
    "STAFF": "cls_staff", "WHIP": "cls_whip", "THROWN": "cls_thrown",
    "SHIELD": "cls_shield",
}

# Waffen mit eigenem Sonderschlag statt dem der Klasse.
WEAPON_SPECIAL = {
    "dagger_bleed": "w_dagger_bleed", "katar": "w_katar",
    "hammer_war": "w_hammer_war", "greataxe_abyss": "w_greataxe_abyss",
    "greatsword_flame": "w_greatsword_flame", "blade_astral": "w_blade_astral",
    "hammer_astral": "w_hammer_astral", "scythe_void": "w_scythe_void",
    "katana_void": "w_katana_void", "rifle_cobalt": "w_rifle_cobalt",
    "raygun_astral": "w_raygun_astral", "launcher_rocket": "w_launcher_rocket",
    "flamethrower": "w_flamethrower", "staff_abyss": "w_staff_abyss",
    "wand_cobalt": "w_wand_cobalt", "bow_astral": "w_bow_astral",
    "whip_astral": "w_whip_astral", "yoyo_void": "w_yoyo_void",
    "shield_void": "w_shield_void", "bomb_void": "w_bomb_void",
}


def special_path(weapon_id, cat_name):
    sid = WEAPON_SPECIAL.get(weapon_id, CLASS_SPECIAL[cat_name])
    return "res://resources/weapons/specials/%s.tres" % sid


# Klasse jeder bestehenden Waffe - fuer die Zuordnung des Sonderschlags.
EXISTING_CATEGORY = {
    "sword_melee": "SHORTSWORD", "shortsword_bone": "SHORTSWORD",
    "broadsword_iron": "BROADSWORD", "broadsword_titan": "BROADSWORD",
    "katana_moon": "KATANA", "katana_storm": "KATANA",
    "revolver": "REVOLVER", "revolver_heavy": "REVOLVER",
    "pistol_burst": "PISTOL", "pistol_scrap": "PISTOL",
    "smg_buzz": "SMG", "smg_needle": "SMG",
    "shotgun_boom": "SHOTGUN", "shotgun_scatter": "SHOTGUN",
}


# --- 2. Neue Waffen aus den freien Sprites --------------------------------
# (sprite, id, Name, Kategorie, Stufe, Beschreibung)
# Stufe: 0 = Pre-Hardmode, 1 = Hardmode, 2 = Post-Moon-Lord

NEW = [
    # Kurzschwerter: schnell, kurz, wenig Wucht
    ("shortsword_copper", "shortsword_copper", "Kupfer-Kurzschwert", "SHORTSWORD", 0,
     "Weiches Kupfer, aber sehr schnell in der Hand."),
    ("dagger_bleed", "dagger_bleed", "Blutdolch", "SHORTSWORD", 0,
     "Kaum Wucht, dafuer bluten Getroffene aus."),
    ("katar", "katar", "Katar", "SHORTSWORD", 0,
     "Stossklinge am Unterarm. Trifft schnell und oft kritisch."),
    ("sickle_blood", "sickle_blood", "Blutsichel", "SHORTSWORD", 0,
     "Kurze Sichel, die Wunden offen haelt."),
    ("dagger_cobalt", "dagger_cobalt", "Kobaltdolch", "SHORTSWORD", 1,
     "Kobalt haelt die Schneide scharf, auch nach dem hundertsten Stich."),
    ("dagger_gold", "dagger_gold", "Gnadendolch", "SHORTSWORD", 1,
     "Findet jede Luecke in der Deckung."),
    ("rapier_gold", "rapier_gold", "Goldrapier", "SHORTSWORD", 1,
     "Elegante Stossklinge mit erstaunlicher Reichweite."),
    ("dagger_void", "dagger_void", "Leeredolch", "SHORTSWORD", 2,
     "Schneidet dort, wo eigentlich nichts mehr ist."),

    # Breitschwerter: langsam, schwer, hoher Rueckstoss
    ("broadsword_bone", "broadsword_bone", "Knochen-Breitschwert", "BROADSWORD", 0,
     "Grob geschliffener Knochen. Schwer, aber billig."),
    ("axe_battle", "axe_battle", "Streitaxt", "BROADSWORD", 0,
     "Kopflastig. Wer trifft, raeumt ab."),
    ("hammer_war", "hammer_war", "Kriegshammer", "BROADSWORD", 0,
     "Kein Schnitt, nur Wucht. Wirft Gegner weit zurueck."),
    ("greataxe", "greataxe", "Grossaxt", "BROADSWORD", 0,
     "Zwei Haende, ein Schlag, viel Platz drumherum."),
    ("spear_brim", "spear_brim", "Speer", "BROADSWORD", 0,
     "Haelt Gegner auf Abstand, statt sie umzuwerfen."),
    ("scythe_harvest", "scythe_harvest", "Sense", "BROADSWORD", 0,
     "Weiter Bogen, der mehrere Gegner gleichzeitig erwischt."),
    ("broadsword_cobalt", "broadsword_cobalt", "Kobalt-Breitschwert", "BROADSWORD", 1,
     "Kobaltstahl: leichter als er aussieht, haerter als er wirkt."),
    ("greatsword_flame", "greatsword_flame", "Flammen-Grossschwert", "BROADSWORD", 1,
     "Die Klinge glueht noch, wenn der Schlag laengst vorbei ist."),
    ("halberd_cobalt", "halberd_cobalt", "Kobalt-Hellebarde", "BROADSWORD", 1,
     "Stangenwaffe mit der groessten Reichweite im Nahkampf."),
    ("greataxe_abyss", "greataxe_abyss", "Abgrund-Doppelaxt", "BROADSWORD", 1,
     "Zwei Schneiden, doppelte Wucht, halbes Tempo."),
    ("greatsword_abyss", "greatsword_abyss", "Abgrund-Grossschwert", "BROADSWORD", 1,
     "So breit, dass es fast schon ein Schild ist."),
    ("blade_astral", "blade_astral", "Astralklinge", "BROADSWORD", 2,
     "Leicht wie Licht, schwer wie ein Berg."),
    ("hammer_astral", "hammer_astral", "Astralhammer", "BROADSWORD", 2,
     "Jeder Treffer sitzt wie ein Einschlag."),
    ("scythe_void", "scythe_void", "Leeresense", "BROADSWORD", 2,
     "Maeht ganze Reihen. Fragt nicht, wie."),

    # Katanas: schnell, blutend, geschickabhaengig
    ("curved_fang", "curved_fang", "Krummschwert Fang", "KATANA", 0,
     "Gebogene Klinge, die tiefe Schnitte hinterlaesst."),
    ("twinblade", "twinblade", "Doppelklinge", "KATANA", 0,
     "Zwei Schneiden, ein Griff, doppelte Schlagzahl."),
    ("katana_dawn", "katana_dawn", "Morgen-Katana", "KATANA", 1,
     "Der erste Schnitt sitzt, bevor man ihn sieht."),
    ("katana_void", "katana_void", "Leere-Katana", "KATANA", 2,
     "Schneidet schneller, als die Wunde sich schliessen kann."),
    ("twinblade_astral", "twinblade_astral", "Astral-Doppelklinge", "KATANA", 2,
     "Zwei Klingen aus Sternenlicht. Hoerst du sie, ist es zu spaet."),

    # Revolver: harte Einzelschuesse
    ("rifle_cobalt", "rifle_cobalt", "Kobaltgewehr", "REVOLVER", 1,
     "Grosse Reichweite, harter Einschlag, lange Ladezeit."),
    ("staff_abyss", "staff_abyss", "Abgrundstab", "STAFF", 1,
     "Schleudert verdichtete Dunkelheit. Durchschlaegt Gegner."),
    ("raygun_astral", "raygun_astral", "Astralstrahler", "REVOLVER", 2,
     "Ein Strahl, der nicht abbremst."),

    # Pistolen: schnelle, leichte Schuesse
    ("crossbow_repeater", "crossbow_repeater", "Repetierarmbrust", "BOW", 0,
     "Bolzen statt Kugeln - langsamer, aber sie durchschlagen."),
    ("staff_crystal", "staff_crystal", "Kristallstab", "STAFF", 0,
     "Kristallsplitter im Dauerfeuer."),
    ("magic_gun", "magic_gun", "Magiepistole", "PISTOL", 1,
     "Halb Waffe, halb Zauber. Trifft haeufig kritisch."),
    ("wand_cobalt", "wand_cobalt", "Kobaltrute", "STAFF", 1,
     "Drei Geschosse pro Wink."),

    # MPs: Dauerfeuer
    ("flamethrower", "flamethrower", "Flammenwerfer", "SMG", 1,
     "Kurze Reichweite, aber nichts bleibt stehen."),
    ("smg_astral", "smg_astral", "Astral-MP", "SMG", 2,
     "Feuert schneller, als das Auge folgen kann."),

    # Schrotflinten: Streuung auf kurze Distanz
    ("blunderbuss", "blunderbuss", "Donnerbuechse", "SHOTGUN", 0,
     "Alles, was reinpasst, kommt vorne wieder raus."),
    ("launcher_rocket", "launcher_rocket", "Raketenwerfer", "SHOTGUN", 1,
     "Wenige Schuesse, dafuer raeumt jeder einen halben Raum."),
    # --- Bogen ---
    ("bow_hunter", "bow_hunter", "Jagdbogen", "BOW", 0,
     "Weit, leise und durchschlagend. Braucht eine ruhige Hand."),
    ("bow_cobalt", "bow_cobalt", "Kobaltbogen", "BOW", 1,
     "Kobalt spannt haerter - der Pfeil geht durch zwei Reihen."),
    ("bow_astral", "bow_astral", "Astralbogen", "BOW", 2,
     "Der Pfeil bremst nicht ab, egal wie viel im Weg steht."),

    # --- Staebe ---
    ("wand_spark", "wand_spark", "Funkenrute", "STAFF", 0,
     "Wirft langsame Funken, die von selbst zum Ziel finden."),
    ("summon_copper", "summon_copper", "Kupfertotem", "STAFF", 0,
     "Setzt zaeh fliegende Geister frei, die niemanden auslassen."),
    ("tome_flames", "tome_flames", "Flammenkodex", "STAFF", 1,
     "Blaettert sich selbst um und wirft dabei Feuer."),
    ("summon_totem", "summon_totem", "Beschwoerungsstab", "STAFF", 1,
     "Ruft Begleiter, die auf eigene Faust nachsetzen."),
    ("tome_void", "tome_void", "Leerekodex", "STAFF", 2,
     "Was daraus kommt, sucht sich sein Ziel selbst."),
    ("summon_astral", "summon_astral", "Astraltotem", "STAFF", 2,
     "Sternenlicht, das nicht mehr loslaesst."),

    # --- Peitschen ---
    ("whip_thorn", "whip_thorn", "Dornenpeitsche", "WHIP", 0,
     "Sehr grosse Reichweite, wenig Wucht - dafuer bluten die Treffer."),
    ("whip_astral", "whip_astral", "Astralpeitsche", "WHIP", 2,
     "Der Riemen zieht Leben aus allem, was er streift."),

    # --- Wurfwaffen ---
    ("boomerang_wood", "boomerang_wood", "Bumerang", "THROWN", 0,
     "Fliegt hin, trifft auf dem Weg und kommt zurueck."),
    ("chakram", "chakram", "Wurfring", "THROWN", 0,
     "Kreist heraus und wieder herein. Trifft auf beiden Wegen."),
    ("shuriken_steel", "shuriken_steel", "Wurfstern", "THROWN", 0,
     "Schnell geworfen, schnell zurueck."),
    ("dagger_throw", "dagger_throw", "Wurfdolch", "THROWN", 0,
     "Kurze Bahn, harter Einschlag."),
    ("javelin_bone", "javelin_bone", "Wurfspiess", "THROWN", 0,
     "Fliegt weiter als alles andere in der Klasse."),
    ("spiky_ball", "spiky_ball", "Stachelball", "THROWN", 0,
     "Springt kurz heraus und rollt zurueck."),
    ("bomb_fire", "bomb_fire", "Brandbombe", "THROWN", 0,
     "Kommt nicht zurueck, macht dafuer beim Aufschlag Krach."),
    ("yoyo_disc", "yoyo_disc", "Yoyo", "THROWN", 0,
     "Bleibt an der Schnur und saegt sich durch."),
    ("spikyball_cobalt", "spikyball_cobalt", "Kobalt-Stachelball", "THROWN", 1,
     "Schwerer, weiter, haerter."),
    ("chakram_void", "chakram_void", "Leerering", "THROWN", 2,
     "Kreist immer weiter, bis nichts mehr steht."),
    ("shuriken_astral", "shuriken_astral", "Astralstern", "THROWN", 2,
     "Teilt sich unterwegs und findet trotzdem zurueck."),
    ("yoyo_void", "yoyo_void", "Leereyoyo", "THROWN", 2,
     "Die Schnur reisst nie, das Ziel schon."),
    ("bomb_void", "bomb_void", "Leerebombe", "THROWN", 2,
     "Zuendet erst, wenn genug davon liegen."),

    # --- Schilde ---
    ("shield_tower", "shield_tower", "Turmschild", "SHIELD", 0,
     "Kaum Schaden, dafuer Ruestung und ein Rempler, der alles umwirft."),
    ("shield_cobalt", "shield_cobalt", "Kobaltschild", "SHIELD", 1,
     "Leichter als er aussieht, haerter als alles dahinter."),
    ("shield_void", "shield_void", "Leereschild", "SHIELD", 2,
     "Was dagegenlaeuft, gibt Leben ab."),
    # --- Nachzuegler aus der Sprite-Werkstatt ---
    ("axe_copper", "axe_copper", "Kupferaxt", "BROADSWORD", 0,
     "Billig geschmiedet, aber die Schneide sitzt."),
    ("scythe_copper", "scythe_copper", "Kupfersense", "BROADSWORD", 0,
     "Weiter Bogen aus weichem Metall - trifft viele, aber nicht tief."),
    ("spear_bone", "spear_bone", "Knochenspeer", "BROADSWORD", 0,
     "Haelt alles auf Abstand, was naeher kommen will."),
    ("flail_copper", "flail_copper", "Kupferflegel", "BROADSWORD", 0,
     "Die Kette holt aus - schwer zu zielen, schwer auszuhalten."),
    ("greatsword_crystal", "greatsword_crystal", "Kristall-Grossschwert", "BROADSWORD", 1,
     "Die Klinge singt, wenn sie trifft."),
    ("spear_cobalt", "spear_cobalt", "Kobaltspeer", "BROADSWORD", 1,
     "Kobalt haelt den Stoss aus, den Holz nicht ueberlebt."),
    ("flail_nebula", "flail_nebula", "Nebelflegel", "BROADSWORD", 1,
     "Der Kopf kommt aus einer Richtung, mit der niemand rechnet."),
    ("trident_abyss", "trident_abyss", "Abgrunddreizack", "BROADSWORD", 2,
     "Drei Spitzen, eine Richtung, kein Ausweichen."),
    ("flail_astral", "flail_astral", "Astralflegel", "BROADSWORD", 2,
     "Die Kette reisst nicht, der Getroffene schon."),
    ("kusarigama", "kusarigama", "Kusarigama", "KATANA", 1,
     "Sichel an der Kette. Schneidet weiter, als der Arm reicht."),
    ("gunblade", "gunblade", "Klingenrevolver", "REVOLVER", 1,
     "Halb Klinge, halb Lauf - und beides ernst gemeint."),
    ("staff_skull", "staff_skull", "Schaedelstab", "STAFF", 1,
     "Was daraus kommt, sucht sich sein Ziel selbst."),
    ("longbow_astral", "longbow_astral", "Astral-Langbogen", "BOW", 2,
     "Spannt weiter als jeder andere Bogen und laesst nichts stehen."),
]


# Grundwerte je Kategorie auf Stufe 0. Hoehere Stufen skalieren daraus.
BASE = {
    "SHORTSWORD": dict(damage=5.6, cooldown=0.32, rng=170, knock=150, shake=2.5,
                       reach=84, swing=0.10, angle=130, weight=2.4, stagger=14,
                       bleed=0, crit=0.0, scal=("D", "C", "NONE"), req=(2, 3), price=150),
    "BROADSWORD": dict(damage=17.4, cooldown=0.95, rng=220, knock=380, shake=6.0,
                       reach=105, swing=0.16, angle=160, weight=6.5, stagger=42,
                       bleed=0, crit=0.0, scal=("B", "E", "NONE"), req=(6, 2), price=260),
    "KATANA": dict(damage=9.3, cooldown=0.42, rng=200, knock=170, shake=3.0,
                   reach=93, swing=0.09, angle=140, weight=3.0, stagger=20,
                   bleed=18, crit=0.06, scal=("D", "B", "D"), req=(3, 6), price=280),
    "REVOLVER": dict(damage=9.3, cooldown=0.55, rng=360, knock=160, shake=3.5,
                     speed=700, shots=1, spread=3.0, pierce=0, flash=36,
                     weight=3.2, stagger=18, bleed=0, crit=0.08,
                     scal=("C", "C", "D"), req=(4, 4), price=300),
    "PISTOL": dict(damage=4.3, cooldown=0.26, rng=320, knock=110, shake=1.5,
                   speed=640, shots=1, spread=5.0, pierce=0, flash=26,
                   weight=2.0, stagger=8, bleed=0, crit=0.0,
                   scal=("E", "C", "E"), req=(2, 4), price=190),
    "SMG": dict(damage=2.8, cooldown=0.085, rng=300, knock=60, shake=1.0,
                speed=720, shots=1, spread=8.0, pierce=0, flash=20,
                weight=2.8, stagger=5, bleed=0, crit=0.0,
                scal=("NONE", "B", "E"), req=(2, 7), price=320),
    "SHOTGUN": dict(damage=3.1, cooldown=0.95, rng=230, knock=260, shake=7.0,
                    speed=560, shots=7, spread=36.0, pierce=1, flash=46,
                    weight=5.8, stagger=30, bleed=0, crit=0.0,
                    scal=("C", "D", "NONE"), req=(6, 3), price=380),
    # Bogen: weit, schnell, durchschlagend - lebt von Geschick.
    "BOW": dict(damage=11.0, cooldown=0.85, rng=430, knock=200, shake=3.0,
                speed=900, shots=1, spread=2.0, pierce=2, flash=24,
                weight=3.4, stagger=22, bleed=0, crit=0.05,
                scal=("E", "A", "D"), req=(3, 6), price=300),
    # Stab: langsame Geschosse, die dem Ziel nachziehen.
    "STAFF": dict(damage=7.5, cooldown=0.60, rng=350, knock=90, shake=2.0,
                  speed=420, shots=1, spread=4.0, pierce=0, flash=30,
                  homing=5.0, weight=3.6, stagger=12, bleed=0, crit=0.0,
                  scal=("NONE", "C", "B"), req=(2, 4), price=340),
    # Peitsche: sehr grosse Reichweite, schmaler Bogen, wenig Wucht.
    "WHIP": dict(damage=6.5, cooldown=0.50, rng=270, knock=90, shake=2.0,
                 reach=141, swing=0.12, angle=55, weight=2.2, stagger=10,
                 bleed=12, crit=0.0, scal=("D", "B", "C"), req=(2, 5), price=260),
    # Wurfwaffe: fliegt hin, trifft mehrfach und kommt zurueck.
    "THROWN": dict(damage=8.0, cooldown=0.70, rng=310, knock=140, shake=2.5,
                   speed=520, shots=1, spread=3.0, pierce=0, flash=18,
                   ret=230.0, weight=2.6, stagger=16, bleed=0, crit=0.04,
                   scal=("D", "B", "D"), req=(3, 5), price=280),
    # Schild: kaum Schaden, dafuer Ruestung und massiver Rueckstoss.
    "SHIELD": dict(damage=9.0, cooldown=1.10, rng=160, knock=520, shake=6.0,
                   reach=69, swing=0.18, angle=180, weight=7.5, stagger=55,
                   bleed=0, crit=0.0, armor=8.0,
                   scal=("B", "NONE", "NONE"), req=(6, 1), price=300),
}

# Abweichungen einzelner Waffen vom Kategorie-Grundwert.
# Werte zwischen 0.3 und 3.0 wirken als Faktor, alles andere ersetzt.
TWEAK = {
    "dagger_bleed": dict(damage=0.75, cooldown=0.85, bleed=34),
    "katar": dict(crit=0.12, cooldown=0.8, damage=0.85),
    "sickle_blood": dict(bleed=26, damage=0.9),
    "rapier_gold": dict(rng=1.15, reach=1.2, cooldown=0.9),
    "hammer_war": dict(knock=1.6, stagger=1.5, cooldown=1.15, weight=1.2),
    "greataxe": dict(damage=1.15, cooldown=1.2, weight=1.25),
    "greataxe_abyss": dict(damage=1.2, cooldown=1.25, weight=1.3),
    "spear_brim": dict(reach=1.45, angle=0.45, knock=0.7, damage=0.9),
    "halberd_cobalt": dict(reach=1.5, angle=0.5, knock=0.8, damage=0.95),
    "scythe_harvest": dict(angle=1.35, damage=0.9, reach=1.15),
    "scythe_void": dict(angle=1.35, damage=0.95, reach=1.15),
    "twinblade": dict(cooldown=0.75, damage=0.8),
    "twinblade_astral": dict(cooldown=0.7, damage=0.85),
    "rifle_cobalt": dict(rng=1.35, cooldown=1.5, damage=1.6, speed=1.25),
    "staff_abyss": dict(pierce=2, damage=1.1, cooldown=1.2),
    "raygun_astral": dict(pierce=1, speed=1.4, rng=1.2),
    "crossbow_repeater": dict(pierce=1, cooldown=1.6, damage=1.7, speed=1.2),
    "staff_crystal": dict(cooldown=0.9, damage=1.05),
    "magic_gun": dict(crit=0.14, damage=1.1),
    "wand_cobalt": dict(shots=3, spread=9.0, damage=0.7),
    "flamethrower": dict(rng=0.55, cooldown=0.7, damage=0.8, spread=16.0),
    "smg_astral": dict(cooldown=0.8),
    "blunderbuss": dict(shots=5, spread=30.0, damage=1.1),
    "launcher_rocket": dict(shots=2, spread=8.0, damage=2.6, cooldown=1.4, knock=1.5),
    "javelin_bone": dict(ret=340.0, damage=1.25, cooldown=1.2),
    "bomb_fire": dict(ret=0.0, damage=1.6, cooldown=1.3, knock=1.6),
    "bomb_void": dict(ret=0.0, damage=1.6, cooldown=1.3, knock=1.6),
    "spiky_ball": dict(ret=150.0, cooldown=0.7, damage=0.8),
    "spikyball_cobalt": dict(ret=170.0, cooldown=0.7, damage=0.85),
    "yoyo_disc": dict(ret=170.0, cooldown=0.55, damage=0.75),
    "yoyo_void": dict(ret=190.0, cooldown=0.55, damage=0.8),
    "shuriken_steel": dict(ret=200.0, cooldown=0.55, damage=0.8, speed=1.3),
    "shuriken_astral": dict(ret=220.0, cooldown=0.5, damage=0.85, speed=1.35),
    "dagger_throw": dict(ret=180.0, cooldown=0.6, damage=0.9),
    "chakram": dict(ret=260.0, damage=1.1),
    "chakram_void": dict(ret=290.0, damage=1.15),
    "boomerang_wood": dict(ret=280.0, damage=1.05),
    "summon_copper": dict(homing=8.0, speed=0.7, damage=0.85),
    "summon_totem": dict(homing=9.0, speed=0.7, damage=0.9),
    "summon_astral": dict(homing=11.0, speed=0.75, damage=0.95),
    "tome_flames": dict(shots=2, spread=14.0, damage=0.8),
    "tome_void": dict(shots=3, spread=16.0, damage=0.8),
    "wand_spark": dict(homing=6.0, cooldown=0.85),
    "bow_hunter": dict(pierce=2),
    "bow_cobalt": dict(pierce=3),
    "bow_astral": dict(pierce=4, speed=1.15),
    "whip_thorn": dict(bleed=20),
    "whip_astral": dict(bleed=26, reach=1.15),
    "shield_tower": dict(armor=8.0),
    "shield_cobalt": dict(armor=13.0),
    "shield_void": dict(armor=19.0),
    "axe_copper": dict(damage=1.05, cooldown=1.1),
    "scythe_copper": dict(angle=1.35, damage=0.85, reach=1.15),
    "spear_bone": dict(reach=1.4, angle=0.45, knock=0.7, damage=0.9),
    "spear_cobalt": dict(reach=1.5, angle=0.45, knock=0.75, damage=0.95),
    "flail_copper": dict(knock=1.4, angle=1.2, damage=0.95, cooldown=1.1),
    "flail_nebula": dict(knock=1.45, angle=1.2, damage=1.0, cooldown=1.1),
    "flail_astral": dict(knock=1.5, angle=1.25, damage=1.05, cooldown=1.1),
    "greatsword_crystal": dict(damage=1.1, cooldown=1.05),
    "trident_abyss": dict(reach=1.45, angle=0.5, damage=1.1),
    "kusarigama": dict(reach=1.35, bleed=24, damage=0.9),
    "gunblade": dict(crit=0.16, rng=0.75, damage=1.15),
    "staff_skull": dict(homing=7.0, damage=1.05),
    "longbow_astral": dict(pierce=5, rng=1.2, speed=1.2, cooldown=1.15),
}

TIER_DAMAGE = [1.0, 1.75, 2.9]
TIER_REQ = [0, 2, 3]
TIER_SCAL = [0, 1, 2]
TIER_PRICE = [1.0, 3.2, 8.0]

GRADES = ["NONE", "E", "D", "C", "B", "A", "S"]
SCAL_ENUM = {g: i for i, g in enumerate(GRADES)}

PROJECTILE_COLORS = {
    "REVOLVER": "Color(0.949, 0.694, 0.204, 1)",
    "PISTOL": "Color(0.29, 0.565, 0.851, 1)",
    "SMG": "Color(0.247, 0.824, 0.78, 1)",
    "SHOTGUN": "Color(0.91, 0.4, 0.235, 1)",
    "BOW": "Color(0.435, 0.749, 0.353, 1)",
    "STAFF": "Color(0.545, 0.435, 0.831, 1)",
    "THROWN": "Color(1, 0.851, 0.541, 1)",
}

FACTOR_KEYS_EXCLUDED = ("shots", "pierce", "spread", "bleed", "crit",
                        "homing", "ret", "armor", "angle")


def bump(grade, steps):
    if grade == "NONE":
        return "NONE"
    return GRADES[min(SCAL_ENUM[grade] + steps, len(GRADES) - 1)]


def build_new():
    written = []
    for sprite, wid, name, cat_name, tier, desc in NEW:
        png = os.path.join(SPRITES, sprite + ".png")
        if not os.path.exists(png):
            print("Sprite fehlt:", png)
            continue

        base = BASE[cat_name]
        tweak = TWEAK.get(sprite, {})
        cat = CAT[cat_name]
        melee = cat in MELEE

        def val(key, default=0.0):
            start = base.get(key, default)
            mod = tweak.get(key)
            if mod is None:
                return start
            if key in FACTOR_KEYS_EXCLUDED or not (0.3 <= mod <= 3.0):
                return mod
            return start * mod

        damage = val("damage") * TIER_DAMAGE[tier]
        scal = tuple(bump(g, TIER_SCAL[tier]) for g in base["scal"])
        req = tuple(min(r + TIER_REQ[tier], 10) for r in base["req"])
        price = int(round(val("price") * TIER_PRICE[tier] / 10.0) * 10)

        out = []
        add = out.append
        add('[gd_resource type="Resource" script_class="WeaponData" format=3]')
        add("")
        add('[ext_resource type="Script" path="res://resources/weapons/weapon_data.gd" id="1_script"]')
        add('[ext_resource type="Texture2D" path="res://%s/%s.png" id="2_art"]' % (SPRITES, sprite))
        if not melee:
            add('[ext_resource type="PackedScene" path="res://scenes/projectiles/projectile.tscn" id="3_proj"]')
        add('[ext_resource type="Resource" path="res://resources/upgrades/tree_weapon.tres" id="4_tree"]')
        add('[ext_resource type="Resource" path="%s" id="5_special"]' % special_path(wid, cat_name))
        add("")
        add("[resource]")
        add('script = ExtResource("1_script")')
        add('weapon_id = "%s"' % wid)
        add('weapon_name = "%s"' % name)
        add("category = %d" % cat)
        add('icon = ExtResource("2_art")')
        add('hold_texture = ExtResource("2_art")')
        add("hold_scale = %.2f" % sprite_scale(png, not melee, cat_name))
        add("hold_rotation_degrees = %.1f" % hold_rotation(cat_name))
        add('description = "%s"' % desc)
        add("rarity = %d" % min(tier + 1, 4))
        add("damage = %.1f" % damage)
        add("cooldown = %.3f" % val("cooldown"))
        add("weapon_range = %.1f" % val("rng"))
        add("knockback = %.1f" % val("knock"))
        add("screen_shake = %.1f" % val("shake"))
        add("crit_bonus = %.2f" % val("crit"))
        add("scaling_power = %d" % SCAL_ENUM[scal[0]])
        add("scaling_agility = %d" % SCAL_ENUM[scal[1]])
        add("scaling_fortune = %d" % SCAL_ENUM[scal[2]])
        add("required_power = %d" % req[0])
        add("required_agility = %d" % req[1])
        add("weight = %.1f" % val("weight"))
        add("stagger = %.1f" % (val("stagger") * (1.0 + 0.35 * tier)))
        add("bleed_buildup = %.1f" % val("bleed"))
        add("is_melee = %s" % ("true" if melee else "false"))
        if melee:
            add("attack_reach = %.1f" % val("reach"))
            add("swing_duration = %.2f" % val("swing"))
            add("swing_angle_degrees = %.1f" % val("angle"))
        else:
            add('projectile_scene = ExtResource("3_proj")')
            add("projectile_speed = %.1f" % val("speed"))
            add("pierce_count = %d" % int(val("pierce")))
            add("projectiles_per_shot = %d" % int(val("shots")))
            add("spread_degrees = %.1f" % val("spread"))
            add("projectile_color = %s" % PROJECTILE_COLORS[cat_name])
            add("muzzle_flash_size = %.1f" % val("flash"))
            if val("homing", 0.0):
                add("homing_strength = %.1f" % val("homing", 0.0))
            if val("ret", 0.0):
                add("return_distance = %.1f" % val("ret", 0.0))
        if val("armor", 0.0):
            add("armor_bonus = %.1f" % val("armor", 0.0))
        add('special = ExtResource("5_special")')
        add('upgrade_tree = ExtResource("4_tree")')
        add("shop_price = %d" % price)

        path = os.path.join(WEAPONS, wid + ".tres")
        io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
        written.append((wid, cat_name, tier, damage, price))
    return written


def update_database(new_ids):
    """Traegt genau die Waffen ein, die es auch als Datei gibt."""
    text = io.open(DB, encoding="utf-8").read()
    stems = list(EXISTING.keys()) + new_ids

    text = re.sub(r'^\[ext_resource type="Resource" path="res://resources/weapons/[^"]+"[^\]]*\]\n',
                  "", text, flags=re.M)

    refs, exts = [], []
    for i, stem in enumerate(stems):
        rid = "w%d_weapon" % (100 + i)
        exts.append('[ext_resource type="Resource" path="res://resources/weapons/%s.tres" id="%s"]'
                    % (stem, rid))
        refs.append('ExtResource("%s")' % rid)

    lines = text.split("\n")
    last = max(i for i, l in enumerate(lines) if l.startswith("[ext_resource"))
    lines[last + 1:last + 1] = exts
    text = "\n".join(lines)

    text = re.sub(r"^weapons = Array\[WeaponData\]\(\[[^\]]*\]\)$",
                  "weapons = Array[WeaponData]([%s])" % ", ".join(refs),
                  text, flags=re.M)

    io.open(DB, "w", encoding="utf-8", newline="\n").write(text)
    print("Datenbank: %d Waffen eingetragen" % len(stems))


if __name__ == "__main__":
    wire_existing()
    print()
    made = build_new()
    for wid, cat, tier, dmg, price in made:
        print("neu: %-22s %-11s Stufe %d  %6.1f Schaden  %5d Gold" % (wid, cat, tier, dmg, price))
    print()
    update_database([m[0] for m in made])
