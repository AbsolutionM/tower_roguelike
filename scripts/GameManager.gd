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

## Zahlen des laufenden Durchgangs - der Abschlussbildschirm liest sie aus.
var run_rooms_cleared: int = 0
## Raeume, die leergeraeumt wurden, bevor die Zeit ablief.
var run_rooms_perfect: int = 0
var run_enemies_killed: int = 0
var run_gold_earned: int = 0
var run_deepest_floor: int = 1
var run_elapsed: float = 0.0
var run_active: bool = false

## Setzt Etage, Raum und alle Zahlen zurück. Wird beim Betreten des Turms gerufen.
func begin_run() -> void:
	current_floor = 1
	rooms_cleared_this_floor = 0
	run_rooms_cleared = 0
	run_rooms_perfect = 0
	run_enemies_killed = 0
	run_gold_earned = 0
	run_deepest_floor = 1
	run_elapsed = 0.0
	run_active = true

func end_run() -> void:
	run_active = false

func count_room_cleared_early() -> void:
	if run_active:
		run_rooms_perfect += 1

func count_enemy_killed() -> void:
	if run_active:
		run_enemies_killed += 1

func count_gold(amount: int) -> void:
	if run_active and amount > 0:
		run_gold_earned += amount

## Fertige Übersicht für den Abschlussbildschirm.
func get_run_stats() -> Array:
	var minutes: int = int(run_elapsed) / 60
	var seconds: int = int(run_elapsed) % 60
	return [
		{"name": "Etage", "value": "%d" % run_deepest_floor},
		{"name": "Räume", "value": "%d" % run_rooms_cleared},
		{"name": "Geschafft", "value": "%d" % run_rooms_perfect},
		{"name": "Gegner", "value": "%d" % run_enemies_killed},
		{"name": "Gold", "value": "%d" % run_gold_earned},
		{"name": "Dauer", "value": "%d:%02d" % [minutes, seconds]},
		{"name": "Gegner/Raum", "value": "%.1f" % (float(run_enemies_killed) / maxf(float(run_rooms_cleared), 1.0))}
	]

func start_room(duration_override: float = 0.0) -> void:
	current_duration = duration_override if duration_override > 0.0 else room_duration
	room_timer = current_duration
	room_active = true

func _process(delta: float) -> void:
	if run_active:
		run_elapsed += delta
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
	run_rooms_cleared += 1
	if rooms_cleared_this_floor >= ROOMS_PER_FLOOR:
		rooms_cleared_this_floor = 0
		current_floor += 1
		run_deepest_floor = maxi(run_deepest_floor, current_floor)
		floor_completed.emit(current_floor)