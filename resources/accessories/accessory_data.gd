extends Resource
class_name AccessoryData

## Ausrüstbares Schmuckstück. Wirkt rein über Werte auf PlayerStats.

@export var accessory_id: String = ""
@export var accessory_name: String = "Accessoire"
@export var icon: Texture2D
@export_multiline var description: String = ""
@export var rarity: ItemData.Rarity = ItemData.Rarity.COMMON
## 0 = nicht im Shop erhältlich.
@export var shop_price: int = 0

@export_group("Werte")
@export var flat_damage_bonus: float = 0.0
@export var flat_speed_bonus: float = 0.0
## Zusätzliche Herzcontainer (rote Herzen).
@export var heart_container_bonus: int = 0
## Zusätzliche Seelenherzen (blau) zu Beginn des Laufs.
@export var soul_heart_bonus: int = 0
@export var damage_multiplier: float = 1.0
@export var lifesteal_bonus: float = 0.0
@export var regen_bonus: float = 0.0
@export var crit_bonus: float = 0.0
@export var pickup_radius_bonus: float = 0.0
@export var armor_bonus: float = 0.0

func get_rarity_color() -> Color:
	return ItemData.RARITY_COLORS.get(rarity, Color.WHITE)

func describe() -> String:
	var parts: Array[String] = []
	if not is_zero_approx(flat_damage_bonus):
		parts.append("%+.0f Schaden" % flat_damage_bonus)
	if not is_equal_approx(damage_multiplier, 1.0):
		parts.append("%+d%% Schaden" % int(round((damage_multiplier - 1.0) * 100.0)))
	if not is_zero_approx(flat_speed_bonus):
		parts.append("%+.0f Tempo" % flat_speed_bonus)
	if heart_container_bonus != 0:
		parts.append("%+d Herzcontainer" % heart_container_bonus)
	if soul_heart_bonus != 0:
		parts.append("%+d Seelenherz" % soul_heart_bonus)
	if not is_zero_approx(lifesteal_bonus):
		parts.append("%+.0f%% Lebensraub" % (lifesteal_bonus * 100.0))
	if not is_zero_approx(regen_bonus):
		parts.append("%+.1f Regeneration" % regen_bonus)
	if not is_zero_approx(crit_bonus):
		parts.append("%+.0f%% Krit" % (crit_bonus * 100.0))
	if not is_zero_approx(pickup_radius_bonus):
		parts.append("%+.0f Sammelradius" % pickup_radius_bonus)
	if not is_zero_approx(armor_bonus):
		parts.append("%+.0f Rüstung" % armor_bonus)
	return ", ".join(parts)
