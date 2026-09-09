extends Resource
class_name CraftingRecipe

## Bauplan für eine Waffe. Materialien kommen aus dem Lager.

@export var recipe_id: String = ""
@export var result_weapon: WeaponData
@export var gold_cost: int = 0
## Material-IDs in derselben Reihenfolge wie material_counts.
@export var material_ids: Array[String] = []
@export var material_counts: Array[int] = []

func get_required() -> Array:
	var required: Array = []
	for i in material_ids.size():
		var count: int = material_counts[i] if i < material_counts.size() else 1
		required.append({"item_id": material_ids[i], "count": count})
	return required

func can_craft() -> bool:
	if not result_weapon:
		return false
	if RunState.is_weapon_owned(result_weapon.weapon_id):
		return false
	if RunState.gold < gold_cost:
		return false
	for entry in get_required():
		if RunState.get_stash_count(str(entry["item_id"])) < int(entry["count"]):
			return false
	return true
