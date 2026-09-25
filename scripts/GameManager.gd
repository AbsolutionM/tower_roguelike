extends Node

## Ablauf eines Laufs: 5 Etagen, jede Etage = 5 zufällige Räume + 1 Mini-Boss.
## Nach dem Mini-Boss der letzten Etage kommt der Hauptboss.
## Räume dauern 30 s; wer früher fertig ist, legt die Restzeit in die Zeitbank.

signal room_time_up
signal floor_completed(floor_number: int)

enum Stage { ROOM, MINI_BOSS, BOSS }

@export var room_duration: float = 30.0
const ROOMS_PER_FLOOR: int = 5
## Überblick zu Beginn jedes Raums: Gegner bewegen sich, greifen aber nicht an.
const OVERVIEW_TIME := 2.0
## Letzte Sekunden: Timer rot, Loot mit doppeltem Sammelradius.
const FINAL_SPURT_TIME := 6.0
## So viel Restzeit darf in den nächsten Raum mitgenommen werden.
const TIME_BANK_MAX := 10.0
## Gegner-HP wachsen pro Etage um diesen Faktor. Schaden bleibt gleich -
## er springt nur pro Turmstufe (TowerData.damage_mult).
const HEALTH_PER_FLOOR := 1.15

var total_floors: int = 5
var current_floor: int = 1
var rooms_cleared_this_floor: int = 0
var stage: Stage = Stage.ROOM
var room_timer: float = 0.0
var room_active: bool = false
var current_duration: float = 30.0
## Sekunden seit Raumbeginn (echte Zeit, unabhängig vom Hitstop).
var room_elapsed: float = 0.0
## Restzeit aus dem letzten Raum, kommt auf den nächsten drauf.
var time_bank: float = 0.0

## Zahlen des laufenden Durchgangs - der Abschlussbildschirm liest sie aus.
var run_rooms_cleared: int = 0
## Raeume, die leergeraeumt wurden, bevor die Zeit ablief.
var run_rooms_perfect: int = 0
var run_enemies_killed: int = 0
var run_gold_earned: int = 0
var run_deepest_floor: int = 1
var run_elapsed: float = 0.0
var run_active: bool = false
## Gold, das im laufenden Raum eingesammelt wurde - Grundlage des Perfekt-Bonus.
var room_gold_earned: int = 0

## Setzt Etage, Raum und alle Zahlen zurück. Wird beim Betreten des Turms gerufen.
func begin_run() -> void:
	var tower := RunState.get_selected_tower()
	total_floors = maxi(tower.floors if tower else 5, 1)
	current_floor = 1
	rooms_cleared_this_floor = 0
	stage = Stage.ROOM
	time_bank = 0.0
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
		room_gold_earned += amount

## Fertige Übersicht für den Abschlussbildschirm.
func get_run_stats() -> Array:
	var minutes: int = int(run_elapsed) / 60
	var seconds: int = int(run_elapsed) % 60
	return [
		{"name": "Etage", "value": "%d / %d" % [run_deepest_floor, total_floors]},
		{"name": "Räume", "value": "%d" % run_rooms_cleared},
		{"name": "Geschafft", "value": "%d" % run_rooms_perfect},
		{"name": "Gegner", "value": "%d" % run_enemies_killed},
		{"name": "Gold", "value": "%d" % run_gold_earned},
		{"name": "Dauer", "value": "%d:%02d" % [minutes, seconds]},
		{"name": "Gegner/Raum", "value": "%.1f" % (float(run_enemies_killed) / maxf(float(run_rooms_cleared), 1.0))}
	]

## `timed` = false für Bossräume: die Uhr steht, der Raum endet mit dem Boss.
func start_room(duration_override: float = 0.0, timed: bool = true) -> void:
	var base: float = duration_override if duration_override > 0.0 else room_duration
	if timed:
		current_duration = base + time_bank + _bonus_room_time()
		time_bank = 0.0
	else:
		current_duration = 99999.0
	room_timer = current_duration
	room_elapsed = 0.0
	room_gold_earned = 0
	room_active = true

## Zusätzliche Sekunden pro Raum aus Relikten (z.B. Taschenuhr).
func _bonus_room_time() -> float:
	var stats := get_tree().get_first_node_in_group("player_stats") if is_inside_tree() else null
	return float(stats.bonus_room_time) if stats and "bonus_room_time" in stats else 0.0

## Restzeit in die Zeitbank legen (gedeckelt) und die Uhr anhalten.
func bank_remaining_time() -> void:
	if current_duration < 999.0:
		time_bank = minf(get_time_remaining(), TIME_BANK_MAX)
	room_active = false

func add_room_time(seconds: float) -> void:
	if room_active and current_duration < 999.0:
		room_timer += seconds
		current_duration = maxf(current_duration, room_timer)

func is_timed_room() -> bool:
	return current_duration < 999.0

## Die ersten zwei Sekunden: Gegner greifen noch nicht an.
func is_overview() -> bool:
	return room_active and room_elapsed < OVERVIEW_TIME

## Letzte Sekunden des Raums: roter Timer, Loot wird stärker angezogen.
func is_final_spurt() -> bool:
	return room_active and is_timed_room() and get_time_remaining() <= FINAL_SPURT_TIME

func _process(delta: float) -> void:
	# Der Hit-Stop verlangsamt die ganze Engine. Die Raumuhr laeuft trotzdem in
	# echten Sekunden - sonst dehnt jeder Treffer den Raum ein Stueck laenger.
	var real_delta: float = delta / maxf(Engine.time_scale, 0.001)
	if run_active:
		run_elapsed += real_delta
	if not room_active:
		return
	room_elapsed += real_delta
	if DevMode.freeze_timer:
		return
	room_timer -= real_delta
	if room_timer <= 0.0:
		room_active = false
		room_time_up.emit()

func get_time_remaining() -> float:
	return max(room_timer, 0.0)

## Gegner werden pro Etage zäher (×1,15). Der Schaden bleibt gleich und
## springt nur mit der Turmstufe - wie in Isaac.
func get_health_scale() -> float:
	return pow(HEALTH_PER_FLOOR, float(current_floor - 1))

func get_damage_scale() -> float:
	var tower := RunState.get_selected_tower()
	return tower.damage_mult if tower else 1.0

func get_progress_text() -> String:
	match stage:
		Stage.MINI_BOSS:
			return "Etage %d/%d  ·  Mini-Boss" % [current_floor, total_floors]
		Stage.BOSS:
			return "Hauptboss"
	return "Etage %d/%d  ·  Raum %d/%d" % [current_floor, total_floors, rooms_cleared_this_floor + 1, ROOMS_PER_FLOOR]

func is_last_floor() -> bool:
	return current_floor >= total_floors

## Nach dem Mini-Boss: nächste Etage oder - auf der letzten - der Hauptboss.
func advance_after_mini_boss() -> void:
	if is_last_floor():
		stage = Stage.BOSS
		return
	current_floor += 1
	run_deepest_floor = maxi(run_deepest_floor, current_floor)
	rooms_cleared_this_floor = 0
	stage = Stage.ROOM
	floor_completed.emit(current_floor)

## Ein normaler Raum ist vorbei. Nach fünf Räumen wartet der Mini-Boss.
func on_room_cleared() -> void:
	room_active = false
	run_rooms_cleared += 1
	if stage != Stage.ROOM:
		return
	rooms_cleared_this_floor += 1
	if rooms_cleared_this_floor >= ROOMS_PER_FLOOR:
		stage = Stage.MINI_BOSS
