extends Node

## Entwickler-Modus: Effekte einzeln abschalten, Waffe/Held/Raum wechseln,
## Cheats. Nur in Debug-Builds (Editor, Debug-Export) verfügbar - in einem
## Release-Export ist alles aus und das Menü lässt sich nicht öffnen.
##
## Tasten (am Schreibtisch):
##   F1  Menü auf/zu          F2  alle Effekte an/aus
##   1   nächster Held        2   nächste Waffe        3   nächster Raum
##   4   alle Gegner töten    5   Unverwundbar an/aus
## Auf dem Handy öffnet der "DEV"-Knopf neben der Pause das Menü.
##
## Andere Skripte fragen nur `DevMode.fx("name")` bzw. die Cheat-Variablen ab.
## Die Einstellungen werden in user://dev_settings.json gespeichert.

signal settings_changed

const SAVE_PATH := "user://dev_settings.json"

## Schlüssel -> Anzeigename. Reihenfolge = Reihenfolge im Menü.
const EFFECTS := {
	"hitstop": "Hitstop",
	"shake": "Screenshake & Zoom-Stoß",
	"screen_flash": "Bildschirmblitze",
	"particles": "Partikel (Funken, Ringe, Staub)",
	"light_flash": "Lichtblitze",
	"texts": "Schadenszahlen & Texte",
	"hit_flash": "Aufblitzen & Quetschen bei Treffern",
	"afterimage": "Nachbilder (Dash)",
	"outlines": "Outlines",
	"lighting": "Beleuchtung & Dunkelheit",
	"weather": "Wetter-Overlay",
}

## Debug-Build? Nur dann gibt es den Dev-Modus überhaupt.
var available: bool = OS.is_debug_build()

var effects: Dictionary = {}
var god_mode: bool = false
var freeze_timer: bool = false
var one_hit_kill: bool = false
## Grundtempo des Spiels. Der Hitstop kehrt zu diesem Wert zurück statt zu 1.0.
var time_scale: float = 1.0

var _menu: DevMenu = null

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for key in EFFECTS:
		effects[key] = true
	_load()
	get_tree().node_added.connect(_on_node_added)
	_apply_all.call_deferred()

## True = Effekt ist an. Ohne Dev-Modus ist immer alles an.
func fx(key: String) -> bool:
	if not available:
		return true
	return bool(effects.get(key, true))

func set_effect(key: String, on: bool) -> void:
	effects[key] = on
	_apply_all()
	_save()
	settings_changed.emit()

## Schaltet alle Effekte gemeinsam: sind welche an, gehen alle aus, sonst alle an.
func toggle_all_effects() -> void:
	var any_on := false
	for key in effects:
		if effects[key]:
			any_on = true
			break
	for key in effects:
		effects[key] = not any_on
	_apply_all()
	_save()
	settings_changed.emit()
	_toast("Effekte " + ("aus" if any_on else "an"))

func set_cheat(cheat: String, on: bool) -> void:
	set(cheat, on)
	_save()
	settings_changed.emit()

func set_time_scale(value: float) -> void:
	time_scale = clampf(value, 0.1, 4.0)
	Engine.time_scale = time_scale
	settings_changed.emit()

# --- Eingaben --------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if not available or not (event is InputEventKey) or not event.pressed or event.echo:
		return
	match event.physical_keycode:
		KEY_F1:
			toggle_menu()
		KEY_F2:
			toggle_all_effects()
		KEY_1:
			next_character()
		KEY_2:
			next_weapon()
		KEY_3:
			next_room()
		KEY_4:
			kill_all_enemies()
		KEY_5:
			set_cheat("god_mode", not god_mode)
			_toast("Unverwundbar " + ("an" if god_mode else "aus"))
		_:
			return
	get_viewport().set_input_as_handled()

func toggle_menu() -> void:
	if not available:
		return
	if is_instance_valid(_menu):
		_menu.close()
		_menu = null
		return
	_menu = DevMenu.new()
	get_tree().root.add_child(_menu)

# --- Anwenden auf die Szene ------------------------------------------------

## Outlines hängen an einer globalen Shader-Variable, Licht an den
## CanvasModulate- und Light-Knoten der Szene.
func _apply_all() -> void:
	RenderingServer.global_shader_parameter_set("dev_outlines", fx("outlines"))
	if not is_inside_tree():
		return
	for node in get_tree().root.find_children("*", "CanvasModulate", true, false):
		node.visible = fx("lighting")
	for node in get_tree().root.find_children("*", "PointLight2D", true, false):
		if not (node is LightFlash):
			node.visible = fx("lighting")
	for node in get_tree().root.find_children("*", "WeatherOverlay", true, false):
		node.visible = fx("weather")

## Neue Lichter und Wetter-Overlays kommen gleich richtig eingestellt auf die Welt.
func _on_node_added(node: Node) -> void:
	if not available:
		return
	if node is CanvasModulate or (node is PointLight2D and not node is LightFlash):
		node.visible = fx("lighting")
	elif node is WeatherOverlay:
		node.visible = fx("weather")

# --- Aktionen --------------------------------------------------------------

func _player() -> Node:
	return get_tree().get_first_node_in_group("player")

func _room_controller() -> Node:
	return get_tree().get_first_node_in_group("room_controller")

func set_weapon(weapon: WeaponData) -> void:
	var player := _player()
	if not player or not weapon:
		return
	var controller = player.get_node_or_null("WeaponController")
	if controller:
		controller.equipped_weapon = weapon
		_toast("Waffe: " + weapon.weapon_name)

func next_weapon() -> void:
	var player := _player()
	var weapons := Database.get_weapons()
	if not player or weapons.is_empty():
		return
	var controller = player.get_node_or_null("WeaponController")
	if not controller:
		return
	var index: int = weapons.find(controller.equipped_weapon)
	set_weapon(weapons[(index + 1) % weapons.size()])

func set_character(character: CharacterData) -> void:
	var player := _player()
	if not player or not character:
		return
	player.character_data = character
	if player.has_method("apply_character_data"):
		player.apply_character_data()
	refill_hearts()
	_toast("Held: " + character.character_name)

func next_character() -> void:
	var player := _player()
	var characters := Database.get_characters()
	if not player or characters.is_empty():
		return
	var index: int = characters.find(player.character_data)
	set_character(characters[(index + 1) % characters.size()])

func get_rooms() -> Array:
	var controller := _room_controller()
	return controller.rooms if controller else []

## Springt in einen bestimmten Raum (Index in der Raumliste des Turms).
func goto_room(index: int) -> void:
	var controller := _room_controller()
	if not controller:
		return
	controller.forced_room_index = index
	controller.force_next_room()

func restart_room() -> void:
	var controller := _room_controller()
	if controller:
		goto_room(controller.current_room_index)

func next_room() -> void:
	var controller := _room_controller()
	if controller:
		controller.force_next_room()
		_toast("Nächster Raum")

func kill_all_enemies() -> void:
	for enemy in get_tree().get_nodes_in_group("enemies"):
		if is_instance_valid(enemy) and enemy.has_method("die"):
			enemy.die()

## Container und Seelenherzen wie beim Start des Helden, alles voll.
func refill_hearts() -> void:
	var player := _player()
	if not player:
		return
	var health: PlayerHealth = player.get_node_or_null("PlayerHealth")
	var stats: PlayerStats = player.get_node_or_null("PlayerStats")
	if not health:
		return
	var containers: int = stats.heart_containers if stats else 3
	var soul_hearts: int = stats.soul_hearts if stats else 0
	health.red_max = clampi(containers, 0, PlayerHealth.MAX_HEARTS) * 2
	health.red = health.red_max
	health.soul = maxi(health.soul, mini(soul_hearts * 2, PlayerHealth.MAX_HEARTS * 2 - health.red_max))
	if health.red + health.soul <= 0:
		health.soul = 2
	health.hearts_changed.emit(health.red, health.red_max, health.soul)

func add_soul_heart() -> void:
	var player := _player()
	if player:
		player.get_node("PlayerHealth").add_soul_hearts(2)

func add_container() -> void:
	var player := _player()
	if player:
		player.get_node("PlayerHealth").add_container(1)

## Ein halbes Herz Schaden - zum Testen der Herzleiste.
func hurt_self() -> void:
	var player := _player()
	if not player:
		return
	var health: PlayerHealth = player.get_node("PlayerHealth")
	var was_god := god_mode
	god_mode = false
	health.invuln_timer = 0.0
	health.take_hearts_damage(1)
	god_mode = was_god

func spawn_chest(chest_type: int) -> void:
	var player := _player()
	var scene: PackedScene = load("res://scenes/props/chest.tscn")
	if not player or not scene:
		return
	var chest = scene.instantiate()
	chest.randomize_type = false
	chest.chest_type = chest_type
	get_tree().current_scene.add_child(chest)
	chest.global_position = player.global_position + Vector2(0.0, -110.0)

func _toast(text: String) -> void:
	var player := _player()
	if player:
		FX.floating_text(player.global_position + Vector2(0.0, -90.0), text, Palette.TEAL, 18, 40.0)
	print("[Dev] ", text)

# --- Speichern -------------------------------------------------------------

func _save() -> void:
	var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if not file:
		return
	file.store_string(JSON.stringify({
		"effects": effects,
		"god_mode": god_mode,
		"freeze_timer": freeze_timer,
		"one_hit_kill": one_hit_kill,
	}))

func _load() -> void:
	if not available or not FileAccess.file_exists(SAVE_PATH):
		return
	var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if not file:
		return
	var parsed = JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		return
	var saved: Dictionary = parsed.get("effects", {})
	for key in saved:
		if effects.has(key):
			effects[key] = bool(saved[key])
	god_mode = bool(parsed.get("god_mode", false))
	freeze_timer = bool(parsed.get("freeze_timer", false))
	one_hit_kill = bool(parsed.get("one_hit_kill", false))
