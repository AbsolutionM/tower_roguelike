extends Resource
class_name CharacterData

@export var character_id: String = ""
@export var character_name: String = "Charakter"
@export_multiline var description: String = ""
@export var portrait: Texture2D
@export var sprite_frames: SpriteFrames
## Die Sprites haben keine Hände - diese Textur wird separat animiert.
@export var hand_texture: Texture2D
@export var sprite_modulate: Color = Color(1.0, 1.0, 1.0)
@export var accent_color: Color = Color(1.0, 1.0, 1.0)

@export_group("Attribute")
## 1-10. Steigert Schaden.
@export_range(1, 10) var power: int = 5
## 1-10. Steigert Lauftempo und Angriffstempo.
@export_range(1, 10) var agility: int = 5
## 1-10. Steigert maximale Leben.
@export_range(1, 10) var vitality: int = 5
## 1-10. Steigert Krit-Chance und Loot-Glück.
@export_range(1, 10) var fortune: int = 5
## 1-10. Steigert Rüstung und senkt eingehenden Schaden.
@export_range(1, 10) var toughness: int = 5
## 1-10. Verkürzt die Abklingzeit der Fähigkeit.
@export_range(1, 10) var focus: int = 5

@export_group("Basiswerte")
@export var base_speed: float = 190.0
@export var base_health: float = 90.0

@export_group("Dash")
@export var dash_speed: float = 780.0
@export var dash_duration: float = 0.17
@export var dash_cooldown: float = 1.0

@export_group("Ausrüstung")
@export var starting_weapon: WeaponData
@export var ability: AbilityData
@export var upgrade_tree: UpgradeTree
## Boni für ganze Waffenklassen.
@export var affinities: Array[WeaponAffinity] = []

@export_group("Kraftstufen")
## Freischaltung auf Kraftstufe 5.
@export var gadget: StarPowerData
## Freischaltung auf Kraftstufe 9.
@export var star_power: StarPowerData

## Trennt den Upgrade-Fortschritt pro Charakter im gemeinsamen Charakterbaum.
func upgrade_prefix() -> String:
	return character_id + ":"

func get_affinity(category: WeaponData.Category) -> WeaponAffinity:
	for affinity in affinities:
		if affinity and affinity.category == category:
			return affinity
	return null

## Freischaltungen, die auf dieser Kraftstufe schon aktiv sind.
func get_unlocked_stars(power_level: int) -> Array[StarPowerData]:
	var result: Array[StarPowerData] = []
	if gadget and power_level >= Progression.GADGET_LEVEL:
		result.append(gadget)
	if star_power and power_level >= Progression.STAR_POWER_LEVEL:
		result.append(star_power)
	return result

func describe_affinities() -> String:
	var parts: Array[String] = []
	for affinity in affinities:
		if affinity:
			parts.append("%s: %s" % [WeaponData.CATEGORY_NAMES.get(affinity.category, "?"), affinity.describe()])
	return "\n".join(parts)
