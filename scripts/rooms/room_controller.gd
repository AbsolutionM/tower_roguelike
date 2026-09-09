extends Node2D
class_name RoomController

## Steuert den Raum-Loop: Raum wählen, Gegner + Loot-Quellen spawnen,
## Kamera setzen, nach Ablauf der Zeit (oder wenn leer) zum nächsten Raum.

signal room_started(room: RoomData)
signal room_finished

@export var enemy_scene: PackedScene
@export var boss_scene: PackedScene
@export var rooms: Array[RoomData] = []
@export var time_label: Label
@export var transition_delay: float = 0.55

## Nach so vielen geschafften Räumen kommt garantiert ein Bossraum (0 = aus).
@export var boss_every: int = 4

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
var current_room_index: int = -1

var _ambient: CanvasModulate

func _ready() -> void:
	add_to_group("room_controller")
	z_index = -100
	z_as_relative = false
	_apply_tower()
	GameManager.begin_run()
	GameManager.room_time_up.connect(_on_time_up)
	# Erst nach dem Szenenaufbau spawnen, sonst ist die Root-Node noch gesperrt.
	start_room.call_deferred()

func _process(_delta: float) -> void:
	if time_label:
		var room := get_current_room()
		var room_name: String = room.room_name if room else ""
		time_label.text = "%s  %.1f" % [room_name, GameManager.get_time_remaining()]

	_clamp_player()

	if not is_transitioning and GameManager.room_active and get_tree().get_nodes_in_group("enemies").is_empty():
		clear_room()

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
	Enemy.time_scale = 1.0
	pick_next_room()
	_apply_weather_for_room()

	var room := get_current_room()
	_setup_camera(room)

	var duration: float = room.duration_override if room else 0.0
	if room and room.disable_timer:
		duration = 99999.0
	GameManager.start_room(duration)

	spawn_boss()
	# Feste Layouts haben Vorrang; ohne Layout wird zufällig verteilt.
	if not spawn_from_layout(room):
		spawn_enemies()
		spawn_props()

	queue_redraw()
	room_started.emit(room)

func pick_next_room() -> void:
	if rooms.is_empty():
		current_room_index = -1
		return
	if rooms.size() == 1:
		current_room_index = 0
		return

	var cleared := GameManager.rooms_cleared_this_floor
	if boss_every > 0 and cleared > 0 and cleared % boss_every == 0:
		var boss_index := _find_room_index(true)
		if boss_index >= 0:
			current_room_index = boss_index
			return

	# Normale Räume: zufällig, aber nie zweimal derselbe und nie ein Bossraum.
	var candidates: Array[int] = []
	for i in rooms.size():
		if not rooms[i] or rooms[i].boss_data or i == current_room_index:
			continue
		candidates.append(i)

	if candidates.is_empty():
		current_room_index = maxi(_find_room_index(false), 0)
		return
	current_room_index = candidates[randi() % candidates.size()]

func _find_room_index(want_boss: bool) -> int:
	for i in rooms.size():
		if not rooms[i]:
			continue
		if (rooms[i].boss_data != null) == want_boss:
			return i
	return -1

func get_current_room() -> RoomData:
	if current_room_index >= 0 and current_room_index < rooms.size():
		return rooms[current_room_index]
	return null

func _setup_camera(room: RoomData) -> void:
	var camera := get_tree().get_first_node_in_group("camera")
	if not camera or not camera.has_method("set_room"):
		return
	camera.set_room(global_position, room.fixed_camera if room else true)

func _clamp_player() -> void:
	var room := get_current_room()
	if not room:
		return
	var player := get_tree().get_first_node_in_group("player")
	if not player:
		return

	var half: Vector2 = room.room_size * 0.5 - Vector2(18.0, 18.0)
	var clamped: Vector2 = player.global_position
	clamped.x = clampf(clamped.x, global_position.x - half.x, global_position.x + half.x)
	clamped.y = clampf(clamped.y, global_position.y - half.y, global_position.y + half.y)
	player.global_position = clamped

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

	var boss = boss_scene.instantiate()
	boss.enemy_data = room.boss_data
	get_tree().current_scene.add_child(boss)
	boss.global_position = global_position + Vector2(0.0, -room.room_size.y * 0.28)

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
				"o":
					_spawn_layout_prop(room.harvestable_scene, cell)

	return true

func _cell_to_world(x: int, y: int, columns: int, rows: int, half: Vector2) -> Vector2:
	var fx: float = (float(x) + 0.5) / float(columns)
	var fy: float = (float(y) + 0.5) / float(maxi(rows, 1))
	return global_position + Vector2(lerpf(-half.x, half.x, fx), lerpf(-half.y, half.y, fy))

## Sicherheitsnetz: nie einen Felsen auf den Spieler setzen.
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

func clear_room() -> void:
	if is_transitioning:
		return
	is_transitioning = true

	GameManager.on_room_cleared()
	room_finished.emit()

	_collect_remaining_pickups()
	_despawn_group("pickups")
	_despawn_group("enemies")
	_despawn_group("projectiles")
	_despawn_group("chests")
	_despawn_group("harvestables")
	_despawn_group("obstacles")

	await get_tree().create_timer(transition_delay).timeout
	if is_inside_tree():
		start_room()

## Übrig gebliebenes Loot fliegt beim Raumwechsel automatisch zum Spieler.
func _collect_remaining_pickups() -> void:
	for pickup in get_tree().get_nodes_in_group("pickups"):
		if is_instance_valid(pickup) and pickup.has_method("collect"):
			pickup.collect()

func _despawn_group(group_name: String) -> void:
	for node in get_tree().get_nodes_in_group(group_name):
		if is_instance_valid(node):
			node.queue_free()

func _draw() -> void:
	if not draw_room:
		return
	var room := get_current_room()
	if not room:
		return

	var half: Vector2 = room.room_size * 0.5
	var rect := Rect2(-half, room.room_size)

	if floor_texture:
		draw_texture_rect(floor_texture, rect, true)
	else:
		draw_rect(rect, floor_color)
		var x := -half.x
		while x < half.x:
			var y := -half.y
			while y < half.y:
				if int((x + half.x) / grid_size) % 2 == int((y + half.y) / grid_size) % 2:
					var tile := Rect2(
						Vector2(x, y),
						Vector2(minf(grid_size, half.x - x), minf(grid_size, half.y - y))
					)
					draw_rect(tile, floor_accent)
				y += grid_size
			x += grid_size

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
	for i in 6:
		var inset: float = 12.0 + float(i) * 11.0
		var strength: float = 0.05 * (1.0 - float(i) / 6.0)
		draw_rect(rect.grow(-inset), Color(0.0, 0.0, 0.0, strength), false, 11.0)
