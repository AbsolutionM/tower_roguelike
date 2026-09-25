extends Resource
class_name DropTable

@export var entries: Array[DropEntry] = []

@export var gold_item: ItemData
@export_range(0.0, 1.0) var gold_chance: float = 0.8
@export var gold_min: int = 1
@export var gold_max: int = 4

## Gibt Paare { "item": ItemData, "count": int } zurück.
func roll(luck: float = 0.0) -> Array:
	var results: Array = []

	if gold_item and randf() < gold_chance:
		results.append({"item": gold_item, "count": randi_range(gold_min, max(gold_min, gold_max))})

	for entry in entries:
		if not entry or not entry.item:
			continue
		# Glück verstärkt jede Chance anteilig - ein 1-%-Drop wird dadurch
		# nicht plötzlich zum 15-%-Drop.
		if randf() < clampf(entry.chance * (1.0 + luck * 4.0), 0.0, 1.0):
			results.append({"item": entry.item, "count": entry.roll_count()})

	return results
