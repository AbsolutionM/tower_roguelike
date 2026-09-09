extends Resource
class_name UpgradeTree

@export var tree_name: String = "Upgrades"
@export var upgrades: Array[UpgradeData] = []

func get_upgrade(upgrade_id: String) -> UpgradeData:
	for upgrade in upgrades:
		if upgrade and upgrade.upgrade_id == upgrade_id:
			return upgrade
	return null

## Summe aller additiven Boni auf ein Stat über die gekauften Stufen.
## `prefix` trennt den Fortschritt, wenn sich mehrere Objekte einen Baum teilen
## (z.B. bekommt jede Waffe ihren eigenen Fortschritt im gemeinsamen Waffenbaum).
func get_stat_add(stat_name: String, prefix: String = "") -> float:
	var total: float = 0.0
	for upgrade in upgrades:
		if not upgrade or not upgrade.stat_add.has(stat_name):
			continue
		var level := RunState.get_upgrade_level(prefix + upgrade.upgrade_id)
		if level > 0:
			total += float(upgrade.stat_add[stat_name]) * level
	return total

## Produkt aller multiplikativen Boni auf ein Stat über die gekauften Stufen.
func get_stat_mult(stat_name: String, prefix: String = "") -> float:
	var total: float = 1.0
	for upgrade in upgrades:
		if not upgrade or not upgrade.stat_mult.has(stat_name):
			continue
		var level := RunState.get_upgrade_level(prefix + upgrade.upgrade_id)
		if level > 0:
			total *= pow(float(upgrade.stat_mult[stat_name]), level)
	return total
