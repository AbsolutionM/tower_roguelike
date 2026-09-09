"""Baupläne für die Werkstatt.

Die staerksten Waffen (Post-Moon-Lord) sind nicht im Shop zu haben - sie
entstehen nur aus Material, das man im Turm sammelt und lebend heraustraegt.
Das gibt der Werkstatt einen eigenen Zweck, statt den Shop zu doppeln.

Aufruf aus dem Projektwurzelverzeichnis:  python tools/generate_recipes.py
"""
import io
import os
import re

WEAPONS = "resources/weapons"
RECIPES = "resources/crafting"
DB = "resources/database/game_database.tres"

# Waffe -> (Gold, [(Material, Anzahl), ...])
# Grundpreis richtet sich nach der Klasse: schwere Waffen brauchen mehr Metall,
# schnelle mehr Kristall, alle einen Bosskern.
PLAN = [
    # Leichte, schnelle Waffen ziehen Kristall und Schleim.
    ("dagger_void",      900,  [("crystal_shard", 12), ("slime_gel", 20), ("boss_core", 1)]),
    ("katana_void",      1300, [("crystal_shard", 16), ("slime_gel", 24), ("boss_core", 2)]),
    ("twinblade_astral", 1300, [("crystal_shard", 15), ("slime_gel", 26), ("boss_core", 2)]),
    ("whip_astral",      1100, [("crystal_shard", 12), ("slime_gel", 22), ("boss_core", 1)]),
    ("shuriken_astral",  1000, [("crystal_shard", 12), ("slime_gel", 18), ("boss_core", 1)]),
    ("yoyo_void",        1000, [("crystal_shard", 11), ("slime_gel", 20), ("boss_core", 1)]),

    # Schwere Waffen brauchen Metall und Erz aus dem Abbau.
    ("blade_astral",     1500, [("iron_scrap", 16), ("ore_chunk", 20), ("boss_core", 2)]),
    ("hammer_astral",    1500, [("iron_scrap", 18), ("ore_chunk", 24), ("boss_core", 2)]),
    ("scythe_void",      1400, [("iron_scrap", 14), ("ore_chunk", 18), ("boss_core", 2)]),
    ("shield_void",      1400, [("iron_scrap", 20), ("ore_chunk", 26), ("boss_core", 2)]),
    ("bomb_void",        1100, [("iron_scrap", 12), ("ore_chunk", 14), ("boss_core", 1)]),
    ("chakram_void",     1100, [("iron_scrap", 10), ("ore_chunk", 16), ("boss_core", 1)]),

    # Schusswaffen und Stäbe: Metall für den Lauf, Kristall für den Kern.
    ("raygun_astral",    1600, [("iron_scrap", 12), ("crystal_shard", 18), ("boss_core", 2)]),
    ("smg_astral",       1500, [("iron_scrap", 14), ("crystal_shard", 16), ("boss_core", 2)]),
    ("bow_astral",       1200, [("ore_chunk", 14), ("crystal_shard", 14), ("boss_core", 1)]),
    ("tome_void",        1200, [("slime_gel", 24), ("crystal_shard", 20), ("boss_core", 2)]),
    ("summon_astral",    1200, [("slime_gel", 20), ("crystal_shard", 18), ("boss_core", 2)]),

    # Mittlere Stufe: ohne Bosskern, dafür früher erreichbar.
    ("broadsword_titan", 320, [("iron_scrap", 12), ("ore_chunk", 10)]),
    ("katana_storm",     280, [("crystal_shard", 6), ("slime_gel", 14)]),
    ("revolver_heavy",   300, [("iron_scrap", 10), ("crystal_shard", 4)]),
    ("shotgun_scatter",  340, [("iron_scrap", 14), ("ore_chunk", 8)]),
    ("smg_needle",       300, [("crystal_shard", 8), ("slime_gel", 12)]),
]

def write_recipe(weapon_id, gold, materials):
    ids = ", ".join('"%s"' % m for m, _ in materials)
    counts = ", ".join(str(c) for _, c in materials)
    body = '''[gd_resource type="Resource" script_class="CraftingRecipe" format=3]

[ext_resource type="Script" path="res://resources/crafting/crafting_recipe.gd" id="1_script"]
[ext_resource type="Resource" path="res://%s/%s.tres" id="2_weapon"]

[resource]
script = ExtResource("1_script")
recipe_id = "craft_%s"
result_weapon = ExtResource("2_weapon")
gold_cost = %d
material_ids = Array[String]([%s])
material_counts = Array[int]([%s])
''' % (WEAPONS, weapon_id, weapon_id, gold, ids, counts)
    path = os.path.join(RECIPES, "recipe_%s.tres" % weapon_id)
    io.open(path, "w", encoding="utf-8", newline="\n").write(body)
    return "recipe_%s" % weapon_id


def make_craft_only(weapon_id):
    """Nimmt die Waffe aus dem Shop - sie ist nur noch baubar."""
    path = os.path.join(WEAPONS, weapon_id + ".tres")
    if not os.path.exists(path):
        print("fehlt:", path)
        return
    text = io.open(path, encoding="utf-8").read()
    if re.search(r"^shop_price = ", text, re.M):
        text = re.sub(r"^shop_price = .*$", "shop_price = 0", text, count=1, flags=re.M)
    else:
        text = text.rstrip("\n") + "\nshop_price = 0\n"
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def update_database(recipe_names):
    text = io.open(DB, encoding="utf-8").read()
    text = re.sub(
        r'^\[ext_resource type="Resource" path="res://resources/crafting/[^"]+"[^\]]*\]\n',
        "", text, flags=re.M)

    refs, exts = [], []
    for i, name in enumerate(recipe_names):
        rid = "r%d_recipe" % (300 + i)
        exts.append('[ext_resource type="Resource" path="res://%s/%s.tres" id="%s"]'
                    % (RECIPES, name, rid))
        refs.append('ExtResource("%s")' % rid)

    lines = text.split("\n")
    last = max(i for i, l in enumerate(lines) if l.startswith("[ext_resource"))
    lines[last + 1:last + 1] = exts
    text = "\n".join(lines)
    text = re.sub(r"^recipes = Array\[CraftingRecipe\]\(\[[^\]]*\]\)$",
                  "recipes = Array[CraftingRecipe]([%s])" % ", ".join(refs),
                  text, flags=re.M)
    io.open(DB, "w", encoding="utf-8", newline="\n").write(text)
    print("Datenbank: %d Baupläne" % len(recipe_names))


def main():
    os.makedirs(RECIPES, exist_ok=True)
    names = []

    for weapon_id, gold, materials in PLAN:
        if not os.path.exists(os.path.join(WEAPONS, weapon_id + ".tres")):
            print("Waffe fehlt:", weapon_id)
            continue
        names.append(write_recipe(weapon_id, gold, materials))
        make_craft_only(weapon_id)
        print("Bauplan: %-18s %5d Gold  %s" % (
            weapon_id, gold, ", ".join("%s x%d" % (m, c) for m, c in materials)))

    update_database(names)


if __name__ == "__main__":
    main()
