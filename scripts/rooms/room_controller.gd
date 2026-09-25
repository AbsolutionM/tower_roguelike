extends Node2D
class_name RoomController

## Steuert den Raum-Loop: Raum wählen, Gegner + Loot-Quellen spawnen,
## Kamera setzen, nach Ablauf der Zeit (oder wenn leer) zum nächsten Raum.

signal room_started(room: RoomData)
signal room_finished
## Alle Gegner lagen vor Ablauf der Zeit - der HUD zeigt den "Weiter"-Knopf.
signal room_perfect
## Mini-Boss besiegt - der HUD fragt: weiter oder verlassen?
signal mini_boss_defeated(is_last_floor: bool)
## Hauptboss besiegt - der Turm ist geschafft.
signal tower_cleared

@export var enemy_scene: PackedScene
@export var anvil_scene: PackedScene = preload("res://scenes/props/anvil.tscn")
@export var boss_scene: PackedScene
@export var rooms: Array[RoomData] = []
@export var transition_delay: float = 0.55

## Perfekt-Bonus: so viel vom Gold des Raums gibt es obendrauf (0,5 = ×1,5).
@export var perfect_gold_bonus: float = 0.5
## Nachschub: alle so viele Sekunden 1-2 Gegner, solange noch welche leben.
@export var reinforcement_interval: float = 8.0

@export_group("Spawns")
## Aus, wenn Gegner zufällig im Raum verteilt werden sollen.
@export var use_spawn_points: bool = false
@export var spawn_points: Array[Node2D] = []

@export_group("Raum-Optik")
@export var draw_room: bool = true
## Wird gekachelt über den Boden gelegt. Leer = Platzhalter-Schachbrett.
@export var floor_texture: Texture2D
## Wird gekachelt auf den Rand gelegt. Leer = Platzhalter-Rahmen.
@export var wall_texture: Texture2D
@export var wall_thickness: float = 24.0
## Dunkelt die Spielwelt ab, damit die Lichter wirken.
@export var use_ambient_light: bool = true
@export var floor_color: Color = Palette.SHADOW
@export var floor_accent: Color = Palette.INK
@export var wall_color: Color = Palette.STONE_LIGHT
@export var grid_size: float = 76.0

var is_transitioning: bool = false
## Dev-Modus: dieser Raum kommt als nächstes statt eines zufälligen (-1 = aus).
var forced_room_index: int = -1
## Alle Gegner lagen vor Ablauf der Zeit; der Raum läuft weiter, bis man
## "Weiter" drückt oder die Zeit abläuft.
var is_perfect: bool = false

## Mini-Boss- oder Bossraum, der nicht in `rooms` steht.
var _room_override: RoomData = null
var _mini_boss: EnemyData = null
var _used_mini_bosses: Array[EnemyData] = []
var _elite_this_floor: bool = false
var _special_this_floor: bool = false
var _reinforce_timer: float = 0.0
var _reinforcements_left: int = 0
var _boss_down: bool = false
## Perfektionist: wurde der Held in diesem Raum getroffen?
var _hit_this_room: bool = false
var current_room_index: int = -1

var _ambient: CanvasModulate

func _ready() -> void:
	add_to_group("room_controller")
	z_index = -100
	z_as_relative = false
	_apply_tower()
	GameManager.begin_run()
	RunState.start_run()
	GameManager.room_time_up.connect(_on_time_up)
	# Erst nach dem Szenenaufbau spawnen, sonst ist die Root-Node noch gesperrt.
	start_room.call_deferred()

func _process(delta: float) -> void:
	_clamp_player()
	if is_transitioning or not GameManager.room_active:
		return

	var empty: bool = get_tree().get_nodes_in_group("enemies").is_empty()
	if empty:
		_on_room_emptied()
	else:
		_tick_reinforcements(delta)

## Alle Gegner liegen. Normale Räume laufen weiter (Truhen, Erze in Ruhe),
## Bossräume führen zur Belohnung bzw. zur Entscheidung.
func _on_room_emptied() -> void:
	match GameManager.stage:
		GameManager.Stage.MINI_BOSS:
			if not _boss_down:
				_boss_down = true
				_on_mini_boss_down()
		GameManager.Stage.BOSS:
			if not _boss_down:
				_boss_down = true
				_on_boss_down()
		_:
			if not is_perfect:
				is_perfect = true
				_award_perfect_bonus()
				room_perfect.emit()

## Nachschub, damit der Raum nicht leer wird - aber nur, solange noch Gegner
## leben. Wer alle erwischt, schafft den Raum trotzdem perfekt.
func _tick_reinforcements(delta: float) -> void:
	if GameManager.stage != GameManager.Stage.ROOM or _reinforcements_left <= 0:
		return
	if GameManager.is_overview() or GameManager.is_final_spurt():
		return
	_reinforce_timer -= delta
	if _reinforce_timer > 0.0:
		return
	_reinforce_timer = reinforcement_interval
	var count: int = mini(randi_range(1, 2), _reinforcements_left)
	_reinforcements_left -= count
	var room := get_current_room()
	for i in count:
		if not enemy_scene or not room or room.enemy_pool.is_empty():
			return
		var enemy = enemy_scene.instantiate()
		enemy.enemy_data = room.enemy_pool[randi() % room.enemy_pool.size()]
		get_tree().current_scene.add_child(enemy)
		enemy.global_position = _random_spawn_position(room)

## Übernimmt Räume und Grundbeleuchtung des gewählten Turms.
func _apply_tower() -> void:
	var tower := RunState.get_selected_tower()
	if tower and not tower.rooms.is_empty():
		rooms = tower.rooms

	if not use_ambient_light:
		return
	_ambient = CanvasModulate.new()
	add_child(_ambient)
	_update_ambient()

## Zieht das Wetter für den nächsten Raum aus dem Turm.
func _apply_weather_for_room() -> void:
	var tower := RunState.get_selected_tower()
	if tower and not tower.weather_options.is_empty():
		Weather.set_weather(tower.weather_options[randi() % tower.weather_options.size()])
	else:
		Weather.clear()
	_update_ambient()

func _update_ambient() -> void:
	if not _ambient:
		return
	var tower := RunState.get_selected_tower()
	var base: Color = tower.ambient_color if tower else Palette.MIST
	var tint := Weather.get_ambient_tint()
	_ambient.color = Color(base.r * tint.r, base.g * tint.g, base.b * tint.b, 1.0)

func start_room() -> void:
	is_transitioning = false
	is_perfect = false
	_boss_down = false
	_hit_this_room = false
	_connect_player_health()
	var health := _player_health()
	if health and RunState.has_relic("crystal_armor"):
		health.add_shield(1)
	Enemy.time_scale = 1.0
	pick_next_room()
	_apply_weather_for_room()

	var room := get_current_room()
	_setup_camera(room)

	var timed: bool = GameManager.stage == GameManager.Stage.ROOM and not (room and room.disable_timer)
	GameManager.start_room(room.duration_override if room else 0.0, timed)

	if GameManager.stage == GameManager.Stage.MINI_BOSS:
		_spawn_mini_boss(room)
	else:
		spawn_boss()
	# Feste Layouts haben Vorrang; ohne Layout wird zufällig verteilt.
	if GameManager.stage == GameManager.Stage.ROOM and spawn_from_layout(room):
		_top_up_room(room)
	elif GameManager.stage == GameManager.Stage.ROOM:
		spawn_enemies()
		spawn_props()
	else:
		spawn_props()

	if GameManager.stage == GameManager.Stage.ROOM and room and randf() < room.anvil_chance:
		_spawn_layout_prop(anvil_scene, _random_spawn_position(room))

	if GameManager.stage == GameManager.Stage.ROOM and room and randf() < room.anvil_chance:
		_spawn_layout_prop(anvil_scene, _random_spawn_position(room))

	_reinforce_timer = reinforcement_interval
	_reinforcements_left = int(ceil(float(room.enemy_count) * 0.5)) if room else 0
	_overview_zoom()

	Audio.play(Audio.ID_ROOM_CHANGE)
	queue_redraw()
	room_started.emit(room)

## Welcher Raum als nächstes kommt, hängt an der Stufe des Laufs:
## normale Räume gewichtet gezogen, dann der Mini-Boss, am Ende der Hauptboss.
func pick_next_room() -> void:
	_room_override = null
	_mini_boss = null
	if rooms.is_empty():
		current_room_index = -1
		return

	if forced_room_index >= 0 and forced_room_index < rooms.size():
		current_room_index = forced_room_index
		forced_room_index = -1
		# Der Dev-Modus springt auch direkt in den Bossraum.
		if rooms[current_room_index].boss_data:
			GameManager.stage = GameManager.Stage.BOSS
		elif GameManager.stage != GameManager.Stage.ROOM:
			GameManager.stage = GameManager.Stage.ROOM
		return

	match GameManager.stage:
		GameManager.Stage.BOSS:
			current_room_index = maxi(_find_room_index(true), 0)
			return
		GameManager.Stage.MINI_BOSS:
			var tower := RunState.get_selected_tower()
			if tower and tower.mini_boss_room and not tower.mini_bosses.is_empty():
				_room_override = tower.mini_boss_room
				_mini_boss = _pick_mini_boss(tower)
				return
			# Ohne Mini-Boss-Pool gibt es einen normalen Raum statt eines Kampfs.
			GameManager.stage = GameManager.Stage.ROOM

	if GameManager.rooms_cleared_this_floor == 0:
		_elite_this_floor = false
		_special_this_floor = false
	current_room_index = _pick_weighted_room()
	var picked := get_current_room()
	if picked:
		_elite_this_floor = _elite_this_floor or picked.kind == RoomData.Kind.ELITE
		_special_this_floor = _special_this_floor or picked.kind == RoomData.Kind.SPECIAL

## Gewichtet ziehen: nie zweimal derselbe Raum hintereinander, höchstens ein
## Elite-Raum pro Etage, und im letzten Raum ein Sonderraum, falls es noch
## keinen gab und der Turm welche hat.
func _pick_weighted_room() -> int:
	var last_room_of_floor: bool = GameManager.rooms_cleared_this_floor >= GameManager.ROOMS_PER_FLOOR - 1
	var force_special: bool = last_room_of_floor and not _special_this_floor
	var candidates: Array[int] = []
	for i in rooms.size():
		var room := rooms[i]
		if not room or room.boss_data or i == current_room_index:
			continue
		if room.kind == RoomData.Kind.ELITE and _elite_this_floor:
			continue
		candidates.append(i)
	if force_special:
		var specials := candidates.filter(func(i): return rooms[i].kind == RoomData.Kind.SPECIAL)
		if not specials.is_empty():
			candidates.assign(specials)
	if candidates.is_empty():
		return maxi(_find_room_index(false), 0)

	var total: float = 0.0
	for i in candidates:
		total += maxf(rooms[i].weight, 0.0)
	var pick: float = randf() * total
	for i in candidates:
		pick -= maxf(rooms[i].weight, 0.0)
		if pick <= 0.0:
			return i
	return candidates.back()

## Jeder Mini-Boss höchstens einmal pro Lauf; sind alle durch, von vorn.
func _pick_mini_boss(tower: TowerData) -> EnemyData:
	var left: Array[EnemyData] = []
	for boss in tower.mini_bosses:
		if boss and not _used_mini_bosses.has(boss):
			left.append(boss)
	if left.is_empty():
		_used_mini_bosses.clear()
		left = tower.mini_bosses.duplicate()
	var boss: EnemyData = left[randi() % left.size()]
	_used_mini_bosses.append(boss)
	return boss

func _find_room_index(want_boss: bool) -> int:
	for i in rooms.size():
		if not rooms[i]:
			continue
		if (rooms[i].boss_data != null) == want_boss:
			return i
	return -1

func get_current_room() -> RoomData:
	if _room_override:
		return _room_override
	if current_room_index >= 0 and current_room_index < rooms.size():
		return rooms[current_room_index]
	return null

func _setup_camera(room: RoomData) -> void:
	var camera := get_tree().get_first_node_in_group("camera")
	if not camera or not camera.has_method("set_room"):
		return
	var size: Vector2 = room.room_size if room else Vector2.ZERO
	camera.set_room(global_position, room.fixed_camera if room else true, size)

func _clamp_player() -> void:
	var room := get_current_room()
	if not room:
		return
	var player := get_tree().get_first_node_in_group("player")
	if not player:
		return

	var half: Vector2 = room.room_size * 0.5 - Vector2.ONE * _wall_inset()
	var clamped: Vector2 = player.global_position
	clamped.x = clampf(clamped.x, global_position.x - half.x, global_position.x + half.x)
	clamped.y = clampf(clamped.y, global_position.y - half.y, global_position.y + half.y)
	player.global_position = clamped

## Wie weit der Spieler von der Raumkante wegbleibt. Liegt ein Kachelrand
## vor, endet der begehbare Boden an dessen Innenkante - sonst stünde der Held
## mitten in der Wand.
func _wall_inset() -> float:
	var tileset := _get_tileset()
	if tileset and tileset.has_walls():
		return tileset.tile_size + 8.0
	return 18.0

func spawn_enemies() -> void:
	var room := get_current_room()
	if not enemy_scene or not room or room.enemy_pool.is_empty():
		return

	var count: int = room.enemy_count
	if use_spawn_points and not spawn_points.is_empty():
		count = mini(count, spawn_points.size())

	for i in count:
		var enemy = enemy_scene.instantiate()
		enemy.enemy_data = room.enemy_pool[randi() % room.enemy_pool.size()]
		get_tree().current_scene.add_child(enemy)
		if use_spawn_points and not spawn_points.is_empty():
			enemy.global_position = spawn_points[i].global_position
		else:
			enemy.global_position = _random_spawn_position(room)

func spawn_boss() -> void:
	var room := get_current_room()
	if not room or not room.boss_data or not boss_scene:
		return
	_spawn_boss_enemy(room.boss_data, room)

func _spawn_mini_boss(room: RoomData) -> void:
	if _mini_boss and boss_scene:
		_spawn_boss_enemy(_mini_boss, room)

func _spawn_boss_enemy(data: EnemyData, room: RoomData) -> void:
	var boss = boss_scene.instantiate()
	boss.enemy_data = data
	get_tree().current_scene.add_child(boss)
	boss.global_position = global_position + Vector2(0.0, -room.room_size.y * 0.28)

	Audio.play(Audio.ID_BOSS_SPAWN)
	FX.screen_flash(Color(Palette.BLOOD, 0.35), 0.6)
	FX.shake(8.0)

## Baut einen Raum aus einem festen Raster. False = kein Layout hinterlegt.
func spawn_from_layout(room: RoomData) -> bool:
	if not room or not room.layout_set:
		return false

	var layout := room.layout_set.get_random_layout()
	if layout.is_empty():
		return false

	var columns: int = maxi(room.layout_set.columns, 1)
	var rows: int = layout.size()
	var half: Vector2 = room.room_size * 0.5 - Vector2.ONE * room.spawn_margin
	var player := get_tree().get_first_node_in_group("player")

	for y in rows:
		var line: String = layout[y]
		for x in mini(line.length(), columns):
			var symbol := line.substr(x, 1)
			if symbol == "." or symbol == " ":
				continue

			var cell := _cell_to_world(x, y, columns, rows, half)
			match symbol:
				"#":
					_spawn_layout_obstacle(room, cell, player)
				"e":
					_spawn_layout_enemy(room, cell)
				"c":
					_spawn_layout_prop(room.chest_scene, cell)
				"k":
					_spawn_layout_chest(room.chest_scene, cell, Chest.ChestType.GOLD)
				"o":
					_spawn_layout_prop(room.harvestable_scene, cell)

	return true

func _cell_to_world(x: int, y: int, columns: int, rows: int, half: Vector2) -> Vector2:
	var fx: float = (float(x) + 0.5) / float(columns)
	var fy: float = (float(y) + 0.5) / float(maxi(rows, 1))
	return global_position + Vector2(lerpf(-half.x, half.x, fx), lerpf(-half.y, half.y, fy))

## Sicherheitsnetz: nie einen Felsen auf den Spieler setzen.
## Layouts legen Felsen und ein paar Gegner fest; was die Raumdaten darüber
## hinaus verlangen (Gegnerzahl, Truhen, Erzadern), kommt zufällig dazu.
func _top_up_room(room: RoomData) -> void:
	var missing_enemies: int = room.enemy_count - get_tree().get_nodes_in_group("enemies").size()
	for i in maxi(missing_enemies, 0):
		if not enemy_scene or room.enemy_pool.is_empty():
			break
		var enemy = enemy_scene.instantiate()
		enemy.enemy_data = room.enemy_pool[randi() % room.enemy_pool.size()]
		get_tree().current_scene.add_child(enemy)
		enemy.global_position = _random_spawn_position(room)
	var missing_chests: int = room.chest_count - get_tree().get_nodes_in_group("chests").size()
	for i in maxi(missing_chests, 0):
		_spawn_layout_prop(room.chest_scene, _random_spawn_position(room))
	var missing_ores: int = room.harvestable_count - get_tree().get_nodes_in_group("harvestables").size()
	for i in maxi(missing_ores, 0):
		_spawn_layout_prop(room.harvestable_scene, _random_spawn_position(room))

func _spawn_layout_obstacle(room: RoomData, position: Vector2, player: Node2D) -> void:
	if not room.obstacle_scene:
		return
	if player and position.distance_to(player.global_position) < 90.0:
		return
	var obstacle = room.obstacle_scene.instantiate()
	get_tree().current_scene.add_child(obstacle)
	obstacle.global_position = position

func _spawn_layout_enemy(room: RoomData, position: Vector2) -> void:
	if not enemy_scene or room.enemy_pool.is_empty():
		return
	var enemy = enemy_scene.instantiate()
	enemy.enemy_data = room.enemy_pool[randi() % room.enemy_pool.size()]
	get_tree().current_scene.add_child(enemy)
	enemy.global_position = position

func _spawn_layout_prop(scene: PackedScene, position: Vector2) -> void:
	if not scene:
		return
	var prop = scene.instantiate()
	get_tree().current_scene.add_child(prop)
	prop.global_position = position

## Truhe mit fester Art statt ausgewürfelter.
func _spawn_layout_chest(scene: PackedScene, position: Vector2, chest_type: Chest.ChestType) -> void:
	if not scene:
		return
	var chest = scene.instantiate()
	if chest is Chest:
		chest.randomize_type = false
		chest.chest_type = chest_type
	get_tree().current_scene.add_child(chest)
	chest.global_position = position

## Rote Truhe: Gegner aus dem Pool des Raums springen im Kreis um `origin`
## heraus. Gibt zurück, wie viele es wurden.
func spawn_ambush(origin: Vector2, count: int) -> int:
	var room := get_current_room()
	if not enemy_scene or not room or room.enemy_pool.is_empty() or is_transitioning:
		return 0
	var half: Vector2 = room.room_size * 0.5 - Vector2.ONE * _wall_inset()
	var start_angle: float = randf() * TAU
	for i in count:
		var angle: float = start_angle + TAU * float(i) / float(maxi(count, 1))
		var position := origin + Vector2(cos(angle), sin(angle)) * 80.0
		position.x = clampf(position.x, global_position.x - half.x, global_position.x + half.x)
		position.y = clampf(position.y, global_position.y - half.y, global_position.y + half.y)
		var enemy = enemy_scene.instantiate()
		enemy.enemy_data = room.enemy_pool[randi() % room.enemy_pool.size()]
		get_tree().current_scene.add_child.call_deferred(enemy)
		enemy.set_deferred("global_position", position)
		FX.ring_burst(position, Palette.BLOOD, 6.0, 48.0, 0.35, 4.0)
	return count

func spawn_props() -> void:
	var room := get_current_room()
	if not room:
		return

	for i in room.obstacle_count:
		if not room.obstacle_scene:
			break
		var obstacle = room.obstacle_scene.instantiate()
		get_tree().current_scene.add_child(obstacle)
		obstacle.global_position = _random_spawn_position(room)

	for i in room.chest_count:
		if not room.chest_scene:
			break
		var chest = room.chest_scene.instantiate()
		get_tree().current_scene.add_child(chest)
		chest.global_position = _random_spawn_position(room)

	for i in room.harvestable_count:
		if not room.harvestable_scene:
			break
		var harvestable = room.harvestable_scene.instantiate()
		get_tree().current_scene.add_child(harvestable)
		harvestable.global_position = _random_spawn_position(room)

func _random_spawn_position(room: RoomData) -> Vector2:
	var half: Vector2 = room.room_size * 0.5 - Vector2.ONE * room.spawn_margin
	half.x = maxf(half.x, 10.0)
	half.y = maxf(half.y, 10.0)

	var player := get_tree().get_first_node_in_group("player")
	for attempt in 12:
		var point := global_position + Vector2(randf_range(-half.x, half.x), randf_range(-half.y, half.y))
		if not player or point.distance_to(player.global_position) >= room.min_player_distance:
			return point

	return global_position + Vector2(randf_range(-half.x, half.x), randf_range(-half.y, half.y))

func force_next_room() -> void:
	clear_room()

func _on_time_up() -> void:
	clear_room()

## Knopf "Weiter" nach einem perfekten Raum: Restzeit in die Zeitbank.
func continue_early() -> void:
	if is_transitioning or GameManager.stage != GameManager.Stage.ROOM:
		return
	GameManager.bank_remaining_time()
	clear_room()

## Raum beenden. In normalen Räumen verfällt liegengebliebener Loot und
## übrige Gegner lösen sich ohne Drop auf; aus Bossräumen wird alles
## eingesammelt.
func clear_room() -> void:
	if is_transitioning:
		return
	is_transitioning = true

	var was_boss_room: bool = GameManager.stage != GameManager.Stage.ROOM
	if not _hit_this_room and RunState.has_relic("perfectionist"):
		RunState.add_shards(1)
	GameManager.on_room_cleared()
	_teardown_and_next(was_boss_room)

func _teardown_and_next(was_boss_room: bool) -> void:
	room_finished.emit()

	if was_boss_room:
		_collect_remaining_pickups()
	_despawn_group("pickups")
	_despawn_group("enemies")
	_despawn_group("projectiles")
	_despawn_group("chests")
	_despawn_group("harvestables")
	_despawn_group("obstacles")
	_despawn_group("room_props")

	await get_tree().create_timer(transition_delay, true, false, true).timeout
	if is_inside_tree():
		start_room()

## Perfekt-Bonus: das Gold dieses Raums ×1,5.
func _award_perfect_bonus() -> void:
	GameManager.count_room_cleared_early()
	var bonus: int = int(round(float(GameManager.room_gold_earned) * perfect_gold_bonus))
	var player := get_tree().get_first_node_in_group("player")
	var origin: Vector2 = player.global_position if player else global_position
	FX.floating_text(origin + Vector2(0.0, -96.0), "Perfekt!", Palette.GOLD, 24, 60.0)
	if bonus > 0:
		RunState.add_gold(bonus)
		FX.floating_text(origin + Vector2(0.0, -62.0), "+%d Gold" % bonus, Palette.AMBER, 20, 48.0)
	FX.ring_burst(origin, Palette.GOLD, 12.0, 190.0, 0.45, 8.0)
	Audio.play(Audio.ID_LEVEL_UP)

func _player_health() -> PlayerHealth:
	var player := get_tree().get_first_node_in_group("player")
	return player.get_node_or_null("PlayerHealth") if player else null

func _connect_player_health() -> void:
	var health := _player_health()
	if health and not health.damaged.is_connected(_on_player_damaged):
		health.damaged.connect(_on_player_damaged)

func _on_player_damaged(_halves: int) -> void:
	_hit_this_room = true

## Mini-Boss liegt: ein Herz zurück, Beute einsammeln, dann fragt der HUD.
func _on_mini_boss_down() -> void:
	var player := get_tree().get_first_node_in_group("player")
	if player:
		var health = player.get_node_or_null("PlayerHealth")
		if health:
			health.heal_hearts(2)
	# Echte Sekunden - der Hitstop beim Todesstoß soll die Pause nicht dehnen.
	await get_tree().create_timer(1.6, true, false, true).timeout
	if not is_inside_tree() or is_transitioning or GameManager.stage != GameManager.Stage.MINI_BOSS:
		return
	_collect_remaining_pickups()
	GameManager.room_active = false
	# Beute des Mini-Bosses: ein Relikt, Wahl aus zwei.
	RunState.relic_offer_requested.emit(2, 0, "Mini-Boss besiegt", Relics.Rarity.COMMON)
	mini_boss_defeated.emit(GameManager.is_last_floor())

## Nach der Entscheidung "weiter": nächste Etage bzw. Hauptboss.
func continue_after_mini_boss() -> void:
	if is_transitioning:
		return
	is_transitioning = true
	GameManager.run_rooms_cleared += 1
	GameManager.advance_after_mini_boss()
	_teardown_and_next(true)

## Kurz herauszoomen, damit man den Raum überblickt (Überblicksphase).
func _overview_zoom() -> void:
	var camera := get_tree().get_first_node_in_group("camera")
	if camera and camera.has_method("overview"):
		camera.overview(GameManager.OVERVIEW_TIME)

func _on_boss_down() -> void:
	await get_tree().create_timer(2.0, true, false, true).timeout
	if not is_inside_tree() or is_transitioning or GameManager.stage != GameManager.Stage.BOSS:
		return
	_collect_remaining_pickups()
	GameManager.room_active = false
	var tower := RunState.get_selected_tower()
	if tower:
		RunState.mark_tower_cleared(tower.tower_id)
	tower_cleared.emit()

## Übrig gebliebenes Loot fliegt beim Raumwechsel automatisch zum Spieler.
func _collect_remaining_pickups() -> void:
	for pickup in get_tree().get_nodes_in_group("pickups"):
		if is_instance_valid(pickup) and pickup.has_method("collect"):
			pickup.collect()

func _despawn_group(group_name: String) -> void:
	for node in get_tree().get_nodes_in_group(group_name):
		if is_instance_valid(node):
			node.queue_free()

func _get_tileset() -> RoomTileset:
	var tower := RunState.get_selected_tower()
	return tower.tileset if tower else null

## Platzhalter, solange kein Kachelsatz hinterlegt ist.
func _draw_placeholder_floor(half: Vector2, rect: Rect2) -> void:
	draw_rect(rect, floor_color)
	var x := -half.x
	while x < half.x:
		var y := -half.y
		while y < half.y:
			if int((x + half.x) / grid_size) % 2 == int((y + half.y) / grid_size) % 2:
				draw_rect(Rect2(
					Vector2(x, y),
					Vector2(minf(grid_size, half.x - x), minf(grid_size, half.y - y))
				), floor_accent)
			y += grid_size
		x += grid_size

## Boden, Randkante, Lachen und Streudeko aus dem Kachelsatz.
## Der Zufall hängt am Raum-Index, damit ein Raum bei jedem Neuzeichnen
## gleich aussieht und trotzdem jeder Raum anders.
func _draw_tiles(tileset: RoomTileset, half: Vector2, rect: Rect2) -> void:
	var size: float = maxf(tileset.tile_size, 8.0)
	var columns: int = int(ceil(rect.size.x / size))
	var rows: int = int(ceil(rect.size.y / size))

	var rng := RandomNumberGenerator.new()
	rng.seed = hash(Vector2i(current_room_index, rows * 131 + columns))

	# Unterlage, damit an den Rändern keine Lücke aufblitzt.
	draw_rect(rect, floor_color)

	var has_walls := tileset.has_walls()
	var pools := _plan_pools(tileset, columns, rows, rng)

	for row in rows:
		for column in columns:
			var cell := Rect2(
				Vector2(-half.x + float(column) * size, -half.y + float(row) * size),
				Vector2.ONE * size
			)
			var on_left: bool = column == 0
			var on_right: bool = column == columns - 1
			var on_top: bool = row == 0
			var on_bottom: bool = row == rows - 1

			if has_walls and (on_left or on_right or on_top or on_bottom):
				var wall := tileset.pick_wall(on_left, on_right, on_top, on_bottom, rng)
				if wall:
					draw_texture_rect(wall, cell, false)
					continue

			var floor_tile := tileset.pick_floor(rng)
			if floor_tile:
				draw_texture_rect(floor_tile, cell, false)

			var at := Vector2i(column, row)
			if pools.has(at):
				var pool := tileset.pick_pool(_pool_sides(pools, at), _pool_diagonals(pools, at), rng)
				if pool:
					draw_texture_rect(pool, cell, false)
				continue

			var decor := tileset.pick_decor(rng)
			if decor:
				draw_texture_rect(decor, cell, false)

## Lachen als Vereinigung überlappender Rechtecke im Rauminneren.
## Der Kachelsatz hat keine einzeiligen Streifen - Zellen, für die es kein
## Stück gibt, fliegen raus, so lange bis die Form stabil ist.
func _plan_pools(tileset: RoomTileset, columns: int, rows: int, rng: RandomNumberGenerator) -> Dictionary:
	var cells := {}
	if not tileset.has_pools() or columns < 8 or rows < 8:
		return cells

	for i in tileset.pool_count:
		var width: int = rng.randi_range(2, 4)
		var height: int = rng.randi_range(2, 4)
		# Zwei Kacheln Abstand zum Rand: eine für die Wand, eine Boden dazwischen.
		var x0: int = rng.randi_range(2, columns - 2 - width)
		var y0: int = rng.randi_range(2, rows - 2 - height)
		_fill_pool(cells, x0, y0, width, height)
		# Ein zweites, versetztes Rechteck macht aus dem Kasten einen Fleck.
		if rng.randf() < 0.7:
			var w2: int = rng.randi_range(2, 3)
			var h2: int = rng.randi_range(2, 3)
			var x2: int = clampi(x0 + rng.randi_range(-1, width - 1), 2, columns - 2 - w2)
			var y2: int = clampi(y0 + rng.randi_range(-1, height - 1), 2, rows - 2 - h2)
			_fill_pool(cells, x2, y2, w2, h2)

	for pass_index in 6:
		var removed := false
		for at in cells.keys():
			if tileset.pick_pool(_pool_sides(cells, at), _pool_diagonals(cells, at), rng) == null:
				cells.erase(at)
				removed = true
		if not removed:
			break
	return cells

func _fill_pool(cells: Dictionary, x0: int, y0: int, width: int, height: int) -> void:
	for y in range(y0, y0 + height):
		for x in range(x0, x0 + width):
			cells[Vector2i(x, y)] = true

func _pool_sides(cells: Dictionary, at: Vector2i) -> Array[bool]:
	return [
		cells.has(at + Vector2i(0, -1)),
		cells.has(at + Vector2i(0, 1)),
		cells.has(at + Vector2i(-1, 0)),
		cells.has(at + Vector2i(1, 0)),
	]

func _pool_diagonals(cells: Dictionary, at: Vector2i) -> Array[bool]:
	return [
		cells.has(at + Vector2i(-1, -1)),
		cells.has(at + Vector2i(1, -1)),
		cells.has(at + Vector2i(-1, 1)),
		cells.has(at + Vector2i(1, 1)),
	]

func _draw() -> void:
	if not draw_room:
		return
	var room := get_current_room()
	if not room:
		return

	var half: Vector2 = room.room_size * 0.5
	var rect := Rect2(-half, room.room_size)

	var tileset := _get_tileset()
	if tileset and tileset.has_floor():
		_draw_tiles(tileset, half, rect)
	elif floor_texture:
		draw_texture_rect(floor_texture, rect, true)
	else:
		_draw_placeholder_floor(half, rect)

	if not (tileset and tileset.has_walls()):
		if wall_texture:
			var thickness := wall_thickness
			draw_texture_rect(wall_texture, Rect2(-half, Vector2(room.room_size.x, thickness)), true)
			draw_texture_rect(wall_texture, Rect2(Vector2(-half.x, half.y - thickness), Vector2(room.room_size.x, thickness)), true)
			draw_texture_rect(wall_texture, Rect2(-half, Vector2(thickness, room.room_size.y)), true)
			draw_texture_rect(wall_texture, Rect2(Vector2(half.x - thickness, -half.y), Vector2(thickness, room.room_size.y)), true)
		else:
			draw_rect(rect, wall_color, false, 10.0)
			draw_rect(rect.grow(-10.0), Palette.edge(wall_color), false, 3.0)

	# Weicher Schattenrand nach innen - lässt den Raum tiefer wirken,
	# statt wie eine flache Testfläche auszusehen.
	if not DevMode.fx("shadows"):
		return
	for i in 6:
		var inset: float = 12.0 + float(i) * 11.0
		var strength: float = 0.05 * (1.0 - float(i) / 6.0)
		draw_rect(rect.grow(-inset), Color(0.0, 0.0, 0.0, strength), false, 11.0)
