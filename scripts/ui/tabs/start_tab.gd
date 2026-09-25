extends TownTab

## Mittlerer Reiter: zeigt den Turm, den man betreten wird.

const GAME_SCENE := "res://scenes/game.tscn"

func build() -> void:
	var tower := RunState.get_selected_tower()

	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 20)
	margin.add_theme_constant_override("margin_right", 20)
	margin.add_theme_constant_override("margin_top", 10)
	margin.add_theme_constant_override("margin_bottom", 8)
	add_child(margin)

	var column := UIKit.make_column(10)
	margin.add_child(column)

	if not tower:
		column.add_child(UIKit.make_label("Kein Turm in der Datenbank.", 18, UIKit.BAD))
		return

	var header := UIKit.make_row(8)
	var name_label := UIKit.make_flex_label(tower.tower_name, 30, tower.accent_color)
	header.add_child(name_label)
	header.add_child(UIKit.make_label("%d Etagen" % tower.floors, 16, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_RIGHT))
	column.add_child(header)

	var art_panel := UIKit.make_panel(UIKit.BG_SOFT, Color(tower.accent_color, 0.45), 0)
	art_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(art_panel)

	var artwork := TowerArtwork.new()
	artwork.tower = tower
	artwork.custom_minimum_size = Vector2(0.0, 300.0)
	art_panel.add_child(artwork)

	column.add_child(UIKit.make_label(tower.description, 16, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_LEFT, true))

	if not tower.weather_options.is_empty():
		var names: Array[String] = []
		for weather in tower.weather_options:
			if weather:
				names.append(weather.weather_name)
		column.add_child(UIKit.make_label("Wetter: " + ", ".join(names), 15, UIKit.COOL, HORIZONTAL_ALIGNMENT_LEFT, true))

	var towers := Database.get_towers()
	if towers.size() > 1:
		var switch_row := UIKit.make_row(8)
		for other in towers:
			if not other:
				continue
			var open := RunState.is_tower_unlocked(other)
			var button := UIKit.make_button(other.tower_name if open else other.tower_name + " (gesperrt)", 16, other.accent_color)
			button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			button.custom_minimum_size = Vector2(0.0, UIKit.TOUCH_HEIGHT)
			button.disabled = other == tower or not open
			button.pressed.connect(func() -> void:
				RunState.set_selected_tower(other.tower_id)
				refresh()
			)
			switch_row.add_child(button)
		column.add_child(switch_row)

	var enter_button := UIKit.make_primary_button("Turm betreten", 26, tower.accent_color)
	if not RunState.is_tower_unlocked(tower):
		enter_button.text = "Gesperrt - erst den vorigen Turm bezwingen"
		enter_button.disabled = true
	enter_button.custom_minimum_size = Vector2(0.0, UIKit.TOUCH_HEIGHT + 16.0)
	enter_button.pressed.connect(func() -> void: get_tree().change_scene_to_file(GAME_SCENE))
	column.add_child(enter_button)
