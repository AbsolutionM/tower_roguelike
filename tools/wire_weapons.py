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
TARGET_MELEE = 13.0
TARGET_RANGED = 11.0

CAT = dict(SHORTSWORD=0, BROADSWORD=1, KATANA=2, REVOLVER=3, PISTOL=4, SMG=5, SHOTGUN=6)
MELEE = {0, 1, 2}

# Klingen zeigen im Sprite nach schraeg oben (-45 Grad), Schusswaffen nach
# rechts (0 Grad). Die Grundhaltung der Szene dreht um +90 Grad; die Werte
# hier gleichen das aus, damit beides zum Ziel zeigt.
ROT_MELEE = -45.0
ROT_RANGED = -90.0


def sprite_scale(path, ranged):
    w, h = Image.open(path).size
    target = TARGET_RANGED if ranged else TARGET_MELEE
    return round(target / max(w, h), 2)


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
        text = set_prop(text, "hold_scale", "%.2f" % sprite_scale(png, ranged), "hold_texture")
        text = set_prop(text, "hold_rotation_degrees",
                        "%.1f" % (ROT_RANGED if ranged else ROT_MELEE), "hold_scale")

        io.open(path, "w", encoding="utf-8", newline="\n").write(text)
        print("verbunden: %-20s -> %s" % (stem, sprite))


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
    ("staff_abyss", "staff_abyss", "Abgrundstab", "REVOLVER", 1,
     "Schleudert verdichtete Dunkelheit. Durchschlaegt Gegner."),
    ("raygun_astral", "raygun_astral", "Astralstrahler", "REVOLVER", 2,
     "Ein Strahl, der nicht abbremst."),

    # Pistolen: schnelle, leichte Schuesse
    ("crossbow_repeater", "crossbow_repeater", "Repetierarmbrust", "PISTOL", 0,
     "Bolzen statt Kugeln - langsamer, aber sie durchschlagen."),
    ("staff_crystal", "staff_crystal", "Kristallstab", "PISTOL", 0,
     "Kristallsplitter im Dauerfeuer."),
    ("magic_gun", "magic_gun", "Magiepistole", "PISTOL", 1,
     "Halb Waffe, halb Zauber. Trifft haeufig kritisch."),
    ("wand_cobalt", "wand_cobalt", "Kobaltrute", "PISTOL", 1,
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
]


# Grundwerte je Kategorie auf Stufe 0. Hoehere Stufen skalieren daraus.
BASE = {
    "SHORTSWORD": dict(damage=5.6, cooldown=0.32, rng=170, knock=150, shake=2.5,
                       reach=140, swing=0.10, angle=130, weight=2.4, stagger=14,
                       bleed=0, crit=0.0, scal=("D", "C", "NONE"), req=(2, 3), price=150),
    "BROADSWORD": dict(damage=17.4, cooldown=0.95, rng=220, knock=380, shake=6.0,
                       reach=175, swing=0.16, angle=160, weight=6.5, stagger=42,
                       bleed=0, crit=0.0, scal=("B", "E", "NONE"), req=(6, 2), price=260),
    "KATANA": dict(damage=9.3, cooldown=0.42, rng=200, knock=170, shake=3.0,
                   reach=155, swing=0.09, angle=140, weight=3.0, stagger=20,
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
}

FACTOR_KEYS_EXCLUDED = ("shots", "pierce", "spread", "bleed", "crit")


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
        add("")
        add("[resource]")
        add('script = ExtResource("1_script")')
        add('weapon_id = "%s"' % wid)
        add('weapon_name = "%s"' % name)
        add("category = %d" % cat)
        add('icon = ExtResource("2_art")')
        add('hold_texture = ExtResource("2_art")')
        add("hold_scale = %.2f" % sprite_scale(png, not melee))
        add("hold_rotation_degrees = %.1f" % (ROT_MELEE if melee else ROT_RANGED))
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
