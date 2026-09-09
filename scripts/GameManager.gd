extends Node

signal room_time_up
signal floor_completed(floor_number: int)

@export var room_duration: float = 10.0
const ROOMS_PER_FLOOR: int = 10
const TOTAL_FLOORS: int = 50

var current_floor: int = 1
var rooms_cleared_this_floor: int = 0
var room_timer: float = 0.0
var room_active: bool = false
var current_duration: float = 10.0

func start_room(duration_override: float = 0.0) -> void:
	current_duration = duration_override if duration_override > 0.0 else room_duration
	room_timer = current_duration
	room_active = true

func _process(delta: float) -> void:
	if not room_active:
		return
	room_timer -= delta
	if room_timer <= 0.0:
		room_active = false
		room_time_up.emit()

func get_time_remaining() -> float:
	return max(room_timer, 0.0)

## Gegner werden pro Etage zäher und gefährlicher.
func get_health_scale() -> float:
	return 1.0 + float(current_floor - 1) * 0.2

func get_damage_scale() -> float:
	return 1.0 + float(current_floor - 1) * 0.12

func get_progress_text() -> String:
	return "Etage %d  ·  Raum %d/%d" % [current_floor, rooms_cleared_this_floor + 1, ROOMS_PER_FLOOR]

func on_room_cleared() -> void:
	room_active = false
	rooms_cleared_this_floor += 1
	if rooms_cleared_this_floor >= ROOMS_PER_FLOOR:
		rooms_cleared_this_floor = 0
		current_floor += 1
		floor_completed.emit(current_floor)

func get_next_room_type() -> String:
	if current_floor == TOTAL_FLOORS and rooms_cleared_this_floor == ROOMS_PER_FLOOR - 1:
		return "final_boss"
	elif rooms_cleared_this_floor == ROOMS_PER_FLOOR - 1:
		return "mini_boss"
	else:
		return "normal"
