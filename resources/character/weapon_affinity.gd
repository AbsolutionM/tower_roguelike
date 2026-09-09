extends Resource
class_name WeaponAffinity

## Bonus eines Charakters für eine ganze Waffenklasse.

@export var category: WeaponData.Category = WeaponData.Category.SHORTSWORD
@export var damage_mult: float = 1.15
@export var attack_speed_mult: float = 1.0
@export var crit_bonus: float = 0.0

func describe() -> String:
	var parts: Array[String] = []
	if not is_equal_approx(damage_mult, 1.0):
		parts.append("%+d%% Schaden" % int(round((damage_mult - 1.0) * 100.0)))
	if not is_equal_approx(attack_speed_mult, 1.0):
		parts.append("%+d%% Tempo" % int(round((attack_speed_mult - 1.0) * 100.0)))
	if not is_zero_approx(crit_bonus):
		parts.append("%+d%% Krit" % int(round(crit_bonus * 100.0)))
	return ", ".join(parts)
