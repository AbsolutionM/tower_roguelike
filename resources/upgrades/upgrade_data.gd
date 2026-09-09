extends Resource
class_name UpgradeData

## Ein Knoten im Upgrade-Tree eines Charakters.
## stat_add / stat_mult greifen direkt auf die Felder von PlayerStats zu,
## z.B. { "damage_mult": 0.1 } oder { "move_speed": 15.0 }.

@export var upgrade_id: String = ""
@export var display_name: String = "Upgrade"
@export_multiline var description: String = ""
@export var icon: Texture2D
@export var tier: int = 0
@export var max_level: int = 5
@export var requires: Array[String] = []

@export var base_gold_cost: int = 25
@export var gold_cost_growth: float = 1.6
@export var essence_id: String = ""
@export var base_essence_cost: int = 0

@export var stat_add: Dictionary = {}
@export var stat_mult: Dictionary = {}

func get_gold_cost(current_level: int) -> int:
	return int(round(base_gold_cost * pow(gold_cost_growth, current_level)))

func get_essence_cost(current_level: int) -> int:
	if base_essence_cost <= 0:
		return 0
	return base_essence_cost + current_level
