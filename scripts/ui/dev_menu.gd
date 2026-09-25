extends CanvasLayer
class_name DevMenu

## Menü des Entwickler-Modus. Pausiert das Spiel, solange es offen ist.
## Wird von DevMode.toggle_menu() gebaut und wieder entfernt.

var _was_paused: bool = false

func _ready() -> void:
	layer = 120
	process_mode = Node.PROCESS_MODE_ALWAYS
	_was_paused = get_tree().paused
	get_tree().paused = true
	_build()

## Escape schließt das Menü, statt dahinter die Pause zu öffnen.
func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		DevMode.toggle_menu()

func close() -> void:
	get_tree().paused = _was_paused
	queue_free()

func _build() -> void:
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	UIKit.apply_pixel_theme(root)
	add_child(root)

	var dim := ColorRect.new()
	dim.color = Color(Palette.INK, 0.9)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(dim)

	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var insets := UIKit.safe_insets(get_viewport())
	margin.add_theme_constant_override("margin_left", 24)
	margin.add_theme_constant_override("margin_right", 24)
	margin.add_theme_constant_override("margin_top", 24 + int(insets.x))
	margin.add_theme_constant_override("margin_bottom", 24 + int(insets.y))
	root.add_child(margin)

	var outer := UIKit.make_column(12)
	margin.add_child(outer)

	var header := UIKit.make_row(12)
	var title := UIKit.make_label("Dev-Modus", 30, Palette.TEAL)
	title.clip_text = true
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	var close_button := UIKit.make_button("Schließen", 18, Palette.TEAL)
	close_button.pressed.connect(DevMode.toggle_menu)
	header.add_child(close_button)
	outer.add_child(header)
	outer.add_child(UIKit.make_label("F1 Menü · F2/F12 alles aus · 1 Held · 2 Waffe · 3 Raum · 4 Gegner weg · 5 Unverwundbar", 14, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_LEFT, true))

	var scroll := ScrollContainer.new()
	scroll.name = "Scroll"
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	outer.add_child(scroll)

	var column := UIKit.make_column(10)
	column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(column)

	_build_effects(column)
	_build_cheats(column)
	_build_loadout(column)
	_build_rooms(column)
	_build_spawns(column)

# --- Abschnitte ------------------------------------------------------------

func _section(column: VBoxContainer, text: String, color: Color) -> void:
	column.add_child(UIKit.make_spacer(6.0))
	column.add_child(UIKit.make_label(text, 20, color))

func _build_effects(column: VBoxContainer) -> void:
	_section(column, "Effekte", Palette.AMBER)
	var all := UIKit.make_button("Alle an / aus (F2 / F12)", 17, Palette.AMBER)
	all.pressed.connect(func() -> void:
		DevMode.toggle_all_effects()
		_refresh_toggles(column)
	)
	column.add_child(all)
	var grid := _grid(1)
	for key in DevMode.EFFECTS:
		var check := _check(DevMode.EFFECTS[key], DevMode.fx(key))
		check.set_meta("effect", key)
		check.toggled.connect(func(on: bool) -> void: DevMode.set_effect(key, on))
		grid.add_child(check)
	column.add_child(grid)

func _refresh_toggles(column: Node) -> void:
	for check in column.find_children("*", "CheckButton", true, false):
		if check.has_meta("effect"):
			check.set_pressed_no_signal(DevMode.fx(str(check.get_meta("effect"))))

func _build_cheats(column: VBoxContainer) -> void:
	_section(column, "Cheats", Palette.BLOOD)
	var grid := _grid(1)
	for entry in [["god_mode", "Unverwundbar"], ["one_hit_kill", "Ein Treffer tötet"], ["freeze_timer", "Raumuhr anhalten"]]:
		var cheat: String = entry[0]
		var check := _check(entry[1], bool(DevMode.get(cheat)))
		check.toggled.connect(func(on: bool) -> void: DevMode.set_cheat(cheat, on))
		grid.add_child(check)
	var collisions := _check("Kollisionsformen anzeigen", DevMode.show_collisions)
	collisions.toggled.connect(DevMode.set_show_collisions)
	grid.add_child(collisions)
	column.add_child(grid)

	column.add_child(UIKit.make_label("Kamera-Zoom", 16, UIKit.TEXT_DIM))
	var zooms := _grid(5)
	for value in [1.0, 1.25, 1.5, 1.75, 2.0]:
		var button := UIKit.make_button("%sx" % str(value), 15, Palette.AZURE)
		button.pressed.connect(func() -> void: DevMode.set_camera_zoom(value))
		zooms.add_child(button)
	column.add_child(zooms)

	column.add_child(UIKit.make_label("Spieltempo", 16, UIKit.TEXT_DIM))
	var speeds := _grid(5)
	for value in [0.25, 0.5, 1.0, 2.0, 3.0]:
		var button := UIKit.make_button("%sx" % str(value), 15, Palette.VIOLET)
		button.pressed.connect(func() -> void: DevMode.set_time_scale(value))
		speeds.add_child(button)
	column.add_child(speeds)

	var actions := _grid(2)
	_action(actions, "Herzen voll", DevMode.refill_hearts)
	_action(actions, "+ Seelenherz", DevMode.add_soul_heart)
	_action(actions, "+ Container", DevMode.add_container)
	_action(actions, "½ Herz Schaden", DevMode.hurt_self)
	_action(actions, "+ Schlüssel", func() -> void: RunState.add_keys(1))
	_action(actions, "+ 100 Gold", func() -> void: RunState.add_gold(100))
	_action(actions, "+ 10 Essenz", func() -> void: RunState.add_essence("slime", 10))
	_action(actions, "Gegner töten", DevMode.kill_all_enemies)
	_action(actions, "+ Level", func() -> void: RunState.add_xp(RunState.xp_needed(RunState.run_level) - RunState.run_xp), true)
	column.add_child(actions)

func _build_loadout(column: VBoxContainer) -> void:
	_section(column, "Waffe", Palette.GOLD)
	var weapons := _grid(2)
	for weapon in Database.get_weapons():
		_action(weapons, weapon.weapon_name, func() -> void: DevMode.set_weapon(weapon))
	column.add_child(weapons)

	_section(column, "Held", Palette.MOSS)
	var characters := _grid(2)
	for character in Database.get_characters():
		_action(characters, character.character_name, func() -> void: DevMode.set_character(character))
	column.add_child(characters)

func _build_rooms(column: VBoxContainer) -> void:
	_section(column, "Raum", Palette.AZURE)
	var controls := _grid(2)
	_action(controls, "Nächster Raum", DevMode.next_room, true)
	_action(controls, "Raum neu starten", DevMode.restart_room, true)
	column.add_child(controls)
	var rooms := _grid(2)
	var list: Array = DevMode.get_rooms()
	for i in list.size():
		var room: RoomData = list[i]
		if not room:
			continue
		var label: String = room.room_name + (" (Boss)" if room.boss_data else "")
		_action(rooms, label, func() -> void: DevMode.goto_room(i), true)
	if list.is_empty():
		column.add_child(UIKit.make_label("Nur im Turm verfügbar.", 15, UIKit.TEXT_DIM))
	column.add_child(rooms)

func _build_spawns(column: VBoxContainer) -> void:
	_section(column, "Truhe spawnen", Palette.EMBER)
	var chests := _grid(2)
	for chest_type in Chest.TYPE_NAMES:
		_action(chests, Chest.TYPE_NAMES[chest_type], func() -> void: DevMode.spawn_chest(chest_type), true)
	column.add_child(chests)

# --- Bausteine -------------------------------------------------------------

func _grid(columns: int) -> GridContainer:
	var grid := GridContainer.new()
	grid.columns = columns
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	grid.add_theme_constant_override("h_separation", 8)
	grid.add_theme_constant_override("v_separation", 8)
	return grid

func _check(text: String, on: bool) -> CheckButton:
	var check := CheckButton.new()
	check.text = text
	check.button_pressed = on
	check.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	check.add_theme_font_size_override("font_size", UIKit.font_size(15))
	check.custom_minimum_size = Vector2(0.0, 48.0)
	return check

## `closes` = Menü danach schließen, damit man das Ergebnis sofort sieht.
func _action(parent: Control, text: String, callback: Callable, closes: bool = false) -> void:
	var button := UIKit.make_button(text, 15, Palette.TEAL)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.clip_text = true
	button.pressed.connect(func() -> void:
		if closes:
			DevMode.toggle_menu()
		callback.call()
	)
	parent.add_child(button)
