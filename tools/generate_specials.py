"""Erzeugt die Sonderschlaege: einen Standard je Waffenklasse, dazu
eigene fuer einzelne Waffen. Aufruf aus dem Projektwurzelverzeichnis."""
import io, os

OUT = "resources/weapons/specials"
KIND = dict(SHOCKWAVE=0, CLEAVE=1, BLEED_BURST=2, PIERCE_SHOT=3, SPREAD_BURST=4,
            VOLLEY=5, CHAIN_BOLT=6, LIFE_STRIKE=7, FROST_NOVA=8, METEOR=9)

GOLD = "Color(0.949, 0.694, 0.204, 1)"
AMBER = "Color(1, 0.851, 0.541, 1)"
EMBER = "Color(0.91, 0.4, 0.235, 1)"
TEAL = "Color(0.247, 0.824, 0.78, 1)"
AZURE = "Color(0.29, 0.565, 0.851, 1)"
VIOLET = "Color(0.545, 0.435, 0.831, 1)"
MOSS = "Color(0.435, 0.749, 0.353, 1)"
BLOOD = "Color(0.851, 0.31, 0.31, 1)"
ROSE = "Color(1, 0.561, 0.639, 1)"
BONE = "Color(0.847, 0.824, 0.878, 1)"

# id, Name, Beschreibung, Art, Treffer, Schadensfaktor, Radius, Rueckstoss,
# Anzahl, Dauer, Farbe
SPECIALS = [
    # --- Standard je Klasse ---
    ("cls_shortsword", "Klingenwirbel",
     "Nach genug schnellen Stichen dreht sich der Traeger einmal komplett durch.",
     "CLEAVE", 10, 2.2, 150, 240, 0, 0, BONE),
    ("cls_broadsword", "Erdstoss",
     "Ein Hieb in den Boden. Die Druckwelle wirft alles im Umkreis weg.",
     "SHOCKWAVE", 6, 2.8, 210, 520, 0, 0, EMBER),
    ("cls_katana", "Blutmond",
     "Alle angeschnittenen Gegner bluten auf einen Schlag aus.",
     "BLEED_BURST", 8, 2.6, 190, 120, 0, 0, BLOOD),
    ("cls_revolver", "Durchschlag",
     "Ein ueberladener Schuss, der eine ganze Reihe durchbohrt.",
     "PIERCE_SHOT", 6, 3.2, 0, 0, 1, 0, GOLD),
    ("cls_pistol", "Streufeuer",
     "Ein breiter Faecher aus Kugeln nach vorn.",
     "SPREAD_BURST", 12, 1.4, 0, 0, 7, 0, AZURE),
    ("cls_smg", "Rundumschlag",
     "Der Lauf laeuft heiss und feuert in alle Richtungen.",
     "VOLLEY", 30, 1.2, 0, 0, 14, 0, TEAL),
    ("cls_shotgun", "Doppelladung",
     "Beide Laeufe auf einmal, aus naechster Naehe.",
     "SPREAD_BURST", 5, 2.4, 0, 0, 11, 0, EMBER),
    ("cls_bow", "Sperrfeuer",
     "Ein gespannter Pfeil, der nichts aufhaelt.",
     "PIERCE_SHOT", 7, 3.6, 0, 0, 1, 0, MOSS),
    ("cls_staff", "Kettenblitz",
     "Ein Blitz springt von Gegner zu Gegner und wird dabei schwaecher.",
     "CHAIN_BOLT", 8, 2.0, 320, 0, 6, 0, VIOLET),
    ("cls_whip", "Aderlass",
     "Der lange Riemen zieht Leben aus allem, was er streift.",
     "LIFE_STRIKE", 9, 1.8, 220, 0, 0, 0, ROSE),
    ("cls_thrown", "Klingenregen",
     "Wurfgeschosse fliegen in alle Richtungen ab.",
     "VOLLEY", 10, 1.6, 0, 0, 10, 0, AMBER),
    ("cls_shield", "Schildstoss",
     "Ein Rempler, der alles vor dem Traeger umwirft.",
     "SHOCKWAVE", 7, 2.0, 170, 640, 0, 0, AZURE),

    # --- Eigene Sonderschlaege einzelner Waffen ---
    ("w_dagger_bleed", "Verbluten",
     "Der Blutdolch reisst alle offenen Wunden gleichzeitig auf.",
     "BLEED_BURST", 6, 3.4, 200, 90, 0, 0, BLOOD),
    ("w_katar", "Stichserie",
     "Eine Serie so schnell, dass sie wie ein einziger Treffer aussieht.",
     "CLEAVE", 14, 2.6, 130, 180, 0, 0, ROSE),
    ("w_hammer_war", "Bebenschlag",
     "Der Hammer trifft den Boden. Der halbe Raum hebt ab.",
     "SHOCKWAVE", 5, 3.4, 260, 760, 0, 0, EMBER),
    ("w_greataxe_abyss", "Spaltung",
     "Zwei Schneiden, ein Radius, kein Ueberlebender in der Mitte.",
     "CLEAVE", 5, 3.8, 230, 320, 0, 0, VIOLET),
    ("w_greatsword_flame", "Flammenstoss",
     "Die glühende Klinge zuendet alles im Umkreis an.",
     "SHOCKWAVE", 6, 3.2, 225, 420, 0, 0, EMBER),
    ("w_blade_astral", "Sternenfall",
     "Ein Einschlag aus dem Nichts, mitten auf das Ziel.",
     "METEOR", 6, 4.2, 240, 520, 0, 0, VIOLET),
    ("w_hammer_astral", "Meteorschlag",
     "Der Hammer ruft den Einschlag gleich mit herunter.",
     "METEOR", 5, 4.6, 260, 700, 0, 0, AMBER),
    ("w_scythe_void", "Ernte",
     "Was die Sense schneidet, naehrt den Traeger.",
     "LIFE_STRIKE", 7, 3.0, 250, 0, 0, 0, MOSS),
    ("w_katana_void", "Leereschnitt",
     "Ein Schnitt, der ueber jede Entfernung hinweg trifft.",
     "BLEED_BURST", 7, 3.6, 260, 140, 0, 0, VIOLET),
    ("w_rifle_cobalt", "Salve",
     "Ein Schuss, der die ganze Reihe aufmacht.",
     "PIERCE_SHOT", 5, 4.0, 0, 0, 1, 0, AZURE),
    ("w_raygun_astral", "Strahlensturm",
     "Der Strahler entlaedt sich in alle Richtungen.",
     "VOLLEY", 8, 2.2, 0, 0, 18, 0, VIOLET),
    ("w_launcher_rocket", "Bombardement",
     "Die letzte Rakete faellt senkrecht auf das Ziel.",
     "METEOR", 4, 3.8, 250, 600, 0, 0, EMBER),
    ("w_flamethrower", "Feuersturm",
     "Der Druck entlaedt sich als Ring aus Flammen.",
     "SHOCKWAVE", 24, 1.8, 190, 300, 0, 0, EMBER),
    ("w_staff_abyss", "Abgrundschlag",
     "Der Blitz springt weiter als jeder andere.",
     "CHAIN_BOLT", 6, 2.6, 380, 0, 9, 0, VIOLET),
    ("w_wand_cobalt", "Frostnova",
     "Ein Kaelteschock, der alle Gegner spuerbar ausbremst.",
     "FROST_NOVA", 10, 1.8, 230, 0, 0, 3.0, TEAL),
    ("w_bow_astral", "Sternenpfeil",
     "Ein Pfeil, der durch alles hindurchgeht und weiterfliegt.",
     "PIERCE_SHOT", 5, 4.4, 0, 0, 1, 0, VIOLET),
    ("w_whip_astral", "Sternenriemen",
     "Der Riemen zieht Leben aus einem viel groesseren Umkreis.",
     "LIFE_STRIKE", 7, 2.6, 300, 0, 0, 0, ROSE),
    ("w_yoyo_void", "Kreisschnitt",
     "Das Yoyo zerteilt sich und fliegt in jede Richtung.",
     "VOLLEY", 8, 2.0, 0, 0, 12, 0, VIOLET),
    ("w_shield_void", "Bollwerk",
     "Ein Stoss, der alles umwirft und den Traeger heilt.",
     "LIFE_STRIKE", 6, 2.4, 200, 700, 0, 0, AZURE),
    ("w_bomb_void", "Kettenzuendung",
     "Alle geworfenen Bomben gehen gleichzeitig hoch.",
     "SHOCKWAVE", 5, 3.6, 250, 560, 0, 0, VIOLET),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    for sid, name, desc, kind, hits, dmg, radius, knock, count, dur, color in SPECIALS:
        body = '''[gd_resource type="Resource" script_class="WeaponSpecial" format=3]

[ext_resource type="Script" path="res://resources/weapons/weapon_special.gd" id="1_script"]

[resource]
script = ExtResource("1_script")
special_id = "%s"
special_name = "%s"
description = "%s"
kind = %d
hits_required = %d
damage_mult = %.2f
radius = %.1f
knockback = %.1f
count = %d
duration = %.1f
color = %s
''' % (sid, name, desc, KIND[kind], hits, dmg, radius, knock, max(count, 1), dur, color)
        io.open(os.path.join(OUT, sid + ".tres"), "w", encoding="utf-8", newline="\n").write(body)
    print("Sonderschlaege:", len(SPECIALS))


if __name__ == "__main__":
    main()
