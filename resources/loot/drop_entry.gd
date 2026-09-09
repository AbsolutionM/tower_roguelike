extends Resource
class_name DropEntry

@export var item: ItemData
@export_range(0.0, 1.0) var chance: float = 0.25
@export var count_min: int = 1
@export var count_max: int = 1

func roll_count() -> int:
	return randi_range(count_min, max(count_min, count_max))
