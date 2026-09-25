extends Resource
class_name WeaponData

enum Category {
	SHORTSWORD, BROADSWORD, KATANA, REVOLVER, PISTOL, SMG, SHOTGUN,
	BOW, STAFF, WHIP, THROWN, SHIELD
}

## Skalierungsnoten wie in Elden Ring: wie stark ein Attribut die Waffe trägt.
enum Scaling { NONE, E, D, C, B, A, S }

const SCALING_VALUE := {
	Scaling.NONE: 0.0,
	Scaling.E: 0.25,
	Scaling.D: 0.40,
	Scaling.C: 0.60,
	Scaling.B: 0.85,
	Scaling.A: 1.15,
	Scaling.S: 1.50
}

## Grenzwerte für die Anzeige - eine hochgeschmiedete Waffe klettert sichtbar
## von D auf C, so wie im Vorbild.
const SCALING_LETTERS := [
	{"value": 1.40, "letter": "S"},
	{"value": 1.05, "letter": "A"},
	{"value": 0.78, "letter": "B"},
	{"value": 0.55, "letter": "C"},
	{"value": 0.36, "letter": "D"},
	{"value": 0.01, "letter": "E"}
]

## Wie stark die Attributskalierung insgesamt auf den Schaden durchschlägt.
const SCALING_WEIGHT := 0.55
## Schadensabzug, solange die Attributanforderungen nicht erfüllt sind.
const REQUIREMENT_PENALTY := 0.55

const CATEGORY_NAMES := {
	Category.SHORTSWORD: "Kurzschwert",
	Category.BROADSWORD: "Breitschwert",
	Category.KATANA: "Katana",
	Category.REVOLVER: "Revolver",
	Category.PISTOL: "Pistole",
	Category.SMG: "MP",
	Category.SHOTGUN: "Schrotflinte",
	Category.BOW: "Bogen",
	Category.STAFF: "Stab",
	Category.WHIP: "Peitsche",
	Category.THROWN: "Wurfwaffe",
	Category.SHIELD: "Schild"
}

@export var weapon_id: String = ""
@export var weapon_name: String = "Waffe"
@export var category: Category = Category.SHORTSWORD
## Icon fürs UI / Inventar.
@export var icon: Texture2D
## Sprite, das der Charakter in der Hand hält. Leer = gezeichneter Platzhalter.
@export var hold_texture: Texture2D
## 1.0 = ein Texturpixel ist so gross wie ein Pixel der Figur. Nur fuer
## Waffen ohne eigenes Bild abweichen, dort skaliert es den Platzhalter.
@export var hold_scale: float = 1.0
## Dreht das Haltesprite gegenüber der Szenen-Grundhaltung (die auf Klingen
## ausgelegt ist). Waffen, die nach rechts zeigen, brauchen -90.
@export_range(-180.0, 180.0) var hold_rotation_degrees: float = 0.0
@export_multiline var description: String = ""

@export var rarity: ItemData.Rarity = ItemData.Rarity.COMMON

@export_group("Kampfwerte")
@export var damage: float = 10.0
## Sekunden zwischen zwei Angriffen.
@export var cooldown: float = 1.0
@export var weapon_range: float = 300.0
@export var knockback: float = 180.0
@export var screen_shake: float = 3.0
## Kritische Trefferchance dieser Waffe (0-1).
@export var crit_bonus: float = 0.0
## Zusätzlicher kritischer Schaden (0.5 = +50% Krit-Multiplikator).
@export var crit_damage_bonus: float = 0.0
## Multiplikator auf das Angriffstempo des Trägers.
@export var attack_speed_mult: float = 1.0
## Anteil des Schadens, der als Leben zurückkommt (0-1).
@export var lifesteal: float = 0.0
## Gewicht: schwere Waffen bremsen, leichte machen schneller.
@export var move_speed_bonus: float = 0.0

@export_group("Skalierung")
## Wie stark Kraft den Schaden dieser Waffe trägt.
@export var scaling_power: Scaling = Scaling.D
## Wie stark Geschick den Schaden dieser Waffe trägt.
@export var scaling_agility: Scaling = Scaling.D
## Wie stark Glück den Schaden dieser Waffe trägt (Blutungswaffen).
@export var scaling_fortune: Scaling = Scaling.NONE
## Mindest-Kraft. Darunter schlägt die Waffe deutlich schwächer zu.
@export_range(0, 10) var required_power: int = 0
## Mindest-Geschick. Darunter schlägt die Waffe deutlich schwächer zu.
@export_range(0, 10) var required_agility: int = 0

@export_group("Handhabung")
## Wie weit die Fäuste über den Körperrand hinaus vorgestreckt werden, in
## Figurpixeln. Große Klingen werden so vom Körper weggehalten, statt ihn
## zu verdecken.
@export_range(0, 16) var hand_reach_texels: int = 0
## Beide Hände am Griff. Die freie Hand sitzt dann neben der Waffenhand und
## schwingt mit, statt gegenüber am Kreis zu stehen.
@export var two_handed: bool = false
## Gewicht bremst den Träger - schwere Waffen kosten Tempo.
@export var weight: float = 3.0
## Standfestigkeitsschaden: wie sehr ein Treffer den Gegner aus dem Takt bringt.
@export var stagger: float = 10.0
## Blutungsaufbau pro Treffer. Voll = ein Schlag extra Schaden.
@export var bleed_buildup: float = 0.0

@export_group("Nahkampf")
@export var is_melee: bool = false
@export var attack_reach: float = 20.0
@export var swing_duration: float = 0.12
@export var swing_angle_degrees: float = 140.0

@export_group("Fernkampf")
@export var projectile_scene: PackedScene
@export var projectile_speed: float = 400.0
@export var pierce_count: int = 0
@export var projectiles_per_shot: int = 1
@export var spread_degrees: float = 0.0
@export var projectile_color: Color = Color(1.0, 0.85, 0.4)
@export var muzzle_flash_size: float = 30.0
## Wie stark das Geschoss dem Ziel nachzieht (0 = fliegt gerade). Stäbe.
@export_range(0.0, 12.0) var homing_strength: float = 0.0
## Ab dieser Strecke kehrt das Geschoss zurück (0 = aus). Wurfwaffen.
@export var return_distance: float = 0.0

@export_group("Sonderschlag")
## Lädt sich mit Treffern auf und löst von selbst aus.
@export var special: WeaponSpecial

@export_group("Passiv")
## Rüstung, solange die Waffe getragen wird. Schilde.
@export var armor_bonus: float = 0.0

@export_group("Lauf-Upgrades")
## Affinität der Waffenlinie: macht passende Upgrade-Karten stärker.
enum Affinity { NONE, BLEED, POISON, BURN, FROST, SHOCK, CRIT, IMPACT, SPECIAL }
@export var affinity: Affinity = Affinity.NONE
## Höchstwerte dieser Stufe. Upgrades im Lauf schieben Schaden und Takt vom
## Grundwert bis hierher; erst die nächste Stufe hebt die Grenze an.
## 0 = automatisch (Schaden ×1,35, Cooldown ×0,86 - wie im Ideensheet).
@export var damage_max: float = 0.0
@export var cooldown_min: float = 0.0

const AFFINITY_NAMES := {
	Affinity.NONE: "-", Affinity.BLEED: "Blutung", Affinity.POISON: "Gift",
	Affinity.BURN: "Brand", Affinity.FROST: "Frost", Affinity.SHOCK: "Blitz",
	Affinity.CRIT: "Krit", Affinity.IMPACT: "Wucht", Affinity.SPECIAL: "Sonderschlag"
}

func get_damage_max() -> float:
	return damage_max if damage_max > 0.0 else damage * 1.35

func get_cooldown_min() -> float:
	return cooldown_min if cooldown_min > 0.0 else cooldown * 0.86

@export_group("Fortschritt")
## Nächste Stufe dieser Waffenlinie. Aufwerten tauscht die Waffe gegen sie
## und nimmt die Schmiedestufe mit. Leer = Ende der Linie.
@export var next_tier: WeaponData
@export var tier_gold: int = 0
@export var tier_material_ids: Array[String] = []
@export var tier_material_counts: Array[int] = []

func get_tier_materials() -> Array:
	var required: Array = []
	for i in tier_material_ids.size():
		var count: int = tier_material_counts[i] if i < tier_material_counts.size() else 1
		required.append({"item_id": tier_material_ids[i], "count": count})
	return required
## 0 = nicht im Shop erhältlich (z.B. nur über Crafting).
@export var shop_price: int = 0

## Klassen, die der Held in der Hand hält, statt sie auf das Ziel zu richten.
## Schusswaffen und Stäbe zeigen auf den Gegner, alles andere steht aufrecht.
const UPRIGHT_CATEGORIES := [
	Category.SHORTSWORD, Category.BROADSWORD, Category.KATANA,
	Category.WHIP, Category.SHIELD, Category.BOW, Category.THROWN
]

func holds_upright() -> bool:
	return UPRIGHT_CATEGORIES.has(category)

func get_category_name() -> String:
	return CATEGORY_NAMES.get(category, "Waffe")

# --- Schmieden und Skalierung ----------------------------------------------

## Skalierungswert eines Attributs auf der aktuellen Schmiedestufe.
func scaling_value(grade: Scaling, level: int) -> float:
	var base: float = float(SCALING_VALUE.get(grade, 0.0))
	if base <= 0.0:
		return 0.0
	return base * (1.0 + Progression.REINFORCE_SCALING_PER_LEVEL * float(level))

## Note als Buchstabe - das ist, was im Menü steht.
func scaling_letter(grade: Scaling, level: int) -> String:
	var value := scaling_value(grade, level)
	for entry in SCALING_LETTERS:
		if value >= float(entry["value"]):
			return str(entry["letter"])
	return "-"

func meets_requirements(character: CharacterData) -> bool:
	if not character:
		return true
	return character.power >= required_power and character.agility >= required_agility

## Fehlende Attribute als Text, leer wenn alles erfüllt ist.
func describe_missing_requirements(character: CharacterData) -> String:
	if not character:
		return ""
	var parts: Array[String] = []
	if character.power < required_power:
		parts.append("Kraft %d" % required_power)
	if character.agility < required_agility:
		parts.append("Geschick %d" % required_agility)
	return ", ".join(parts)

## Grundschaden allein aus der Schmiedestufe, ohne Träger.
func get_base_damage(level: int) -> float:
	return damage * Progression.reinforce_damage_mult(level)

## Endgültiger Waffenschaden für diesen Träger auf dieser Schmiedestufe.
## Genau diese Zahl steht im Upgrade-Tab und wird im Kampf benutzt.
func get_effective_damage(character: CharacterData, level: int) -> float:
	var base := get_base_damage(level)
	if not character:
		return base

	var bonus: float = 0.0
	bonus += scaling_value(scaling_power, level) * float(character.power) / 10.0
	bonus += scaling_value(scaling_agility, level) * float(character.agility) / 10.0
	bonus += scaling_value(scaling_fortune, level) * float(character.fortune) / 10.0

	var total := base * (1.0 + bonus * SCALING_WEIGHT)
	if not meets_requirements(character):
		total *= REQUIREMENT_PENALTY
	return total

## Schaden pro Schuss als Text. Eine Schrotflinte mit "2 Schaden" liest sich
## kaputt, solange nicht danebensteht, dass sie zehn Kugeln auf einmal wirft.
func describe_damage(character: CharacterData = null, level: int = 0) -> String:
	var value := get_effective_damage(character, level)
	if projectiles_per_shot > 1:
		return "%d x %.0f Schaden" % [projectiles_per_shot, value]
	return "%.0f Schaden" % value

## Einzeiler für Listen: Klasse, Schaden, Takt.
func describe_line(character: CharacterData = null, level: int = 0) -> String:
	return "%s · %s · %.2fs" % [get_category_name(), describe_damage(character, level), cooldown]

## Bildschirmpixel je Texturpixel der Figur - Waffen liegen im selben Maßstab.
const PIXEL_SCALE := 3.0
## Anteil der Texturgröße, um den der Griff in die Faust rückt (Diagonale).
const GRIP_FRACTION := 0.34

## Reichweite der Klinge in Weltpixeln: vom Griff in der Faust bis zur Spitze,
## gemessen am gemalten Haltesprite. Klingen sind diagonal nach oben rechts
## gemalt, die Spitze ist also die obere rechte Ecke der bemalten Fläche.
## Ohne Sprite gilt attack_reach aus den Daten.
func get_blade_reach() -> float:
	if not hold_texture or not holds_upright():
		return attack_reach
	var full: Vector2 = hold_texture.get_size()
	var used: Vector2 = PixelDraw.used_size(hold_texture)
	var painted_centre: Vector2 = full * 0.5 - PixelDraw.center_offset(hold_texture)
	var tip := Vector2(painted_centre.x + used.x * 0.5, painted_centre.y - used.y * 0.5)
	var grip := Vector2(full.x * 0.5 - full.x * GRIP_FRACTION, full.y * 0.5 + full.y * GRIP_FRACTION)
	return tip.distance_to(grip) * hold_scale * PIXEL_SCALE

## Werteblatt für die Menüs: [{ "name": String, "value": String }, ...]
func describe_sheet(character: CharacterData, level: int) -> Array:
	return [
		{"name": "Angriff", "value": "%.0f" % get_effective_damage(character, level)},
		{"name": "Angriffe/s", "value": "%.2f" % (attack_speed_mult / maxf(cooldown, 0.01))},
		{"name": "Geschosse", "value": "%d" % maxi(projectiles_per_shot, 1)},
		{"name": "Reichweite", "value": "%.0f" % (get_blade_reach() if is_melee else weapon_range)},
		{"name": "Gewicht", "value": "%.1f" % weight},
		{"name": "Führung", "value": "beidhändig" if two_handed else "einhändig"},
		{"name": "Standfestigkeit", "value": "%.0f" % (stagger * Progression.reinforce_stagger_mult(level))},
		{"name": "Rückstoß", "value": "%.0f" % knockback},
		{"name": "Krit-Chance", "value": "%.0f%%" % (crit_bonus * 100.0)},
		{"name": "Krit-Schaden", "value": "+%.0f%%" % (crit_damage_bonus * 100.0)},
		{"name": "Blutung", "value": "%.0f" % bleed_buildup},
		{"name": "Lebensraub", "value": "%.1f%%" % (lifesteal * 100.0)}
	]

## Skalierungsnoten für die Anzeige: [{ "name", "letter" }, ...]
func describe_scaling(level: int) -> Array:
	return [
		{"name": "Kraft", "letter": scaling_letter(scaling_power, level)},
		{"name": "Geschick", "letter": scaling_letter(scaling_agility, level)},
		{"name": "Glück", "letter": scaling_letter(scaling_fortune, level)}
	]

## "Eisen-Kurzschwert +4" - der Name, wie ihn der Spieler überall sieht.
func display_name(level: int) -> String:
	return weapon_name if level <= 0 else "%s +%d" % [weapon_name, level]
