extends TownTab

## Reiter links der Mitte: großes Charakterbild, darunter Waffen und Accessoires.

func build() -> void:
	var character := RunState.get_selected_character()

	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 20)
	margin.add_theme_constant_override("margin_right", 20)
	margin.add_theme_constant_override("margin_top", 10)
	margin.add_theme_constant_override("margin_bottom", 8)
	add_child(margin)

	var column := UIKit.make_column(10)
	margin.add_child(column)

	if not character:
		column.add_child(UIKit.make_label("Keine Charaktere in der Datenbank.", 18, UIKit.BAD))
		return

	column.add_child(_make_character_strip(character))

	var scroll_content := make_scroll(column, 14)
	scroll_content.add_child(_make_portrait(character))
	scroll_content.add_child(_make_info(character))

	scroll_content.add_child(UIKit.make_section("Waffen", character.accent_color))
	scroll_content.add_child(_make_weapon_grid(character))

	scroll_content.add_child(UIKit.make_section(
		"Accessoires  %d/%d" % [RunState.get_equipped_accessory_ids(character.character_id).size(), RunState.MAX_ACCESSORY_SLOTS],
		character.accent_color
	))
	scroll_content.add_child(_make_accessory_grid(character))

# --- Charakterauswahl ------------------------------------------------------

func _make_character_strip(selected: CharacterData) -> Control:
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(0.0, 78.0)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED

	var row := UIKit.make_row(8)
	scroll.add_child(row)

	var selected_panel: Control = null
	for character in Database.get_characters():
		if not character:
			continue
		var is_selected: bool = character == selected
		var panel := UIKit.make_panel(
			UIKit.PANEL_HI if is_selected else UIKit.PANEL,
			character.accent_color if is_selected else Color(1.0, 1.0, 1.0, 0.08),
			12
		)
		panel.custom_minimum_size = Vector2(112.0, 0.0)
		panel.mouse_filter = Control.MOUSE_FILTER_STOP
		panel.add_child(UIKit.make_label(character.character_name, 17, character.accent_color, HORIZONTAL_ALIGNMENT_CENTER))
		panel.gui_input.connect(func(event: InputEvent) -> void:
			if is_click(event):
				RunState.set_selected_character(character.character_id)
				refresh()
		)
		row.add_child(panel)
		if is_selected:
			selected_panel = panel

	# Nach dem Layout: den gewählten Helden in die Mitte der Leiste holen.
	if selected_panel:
		scroll.ready.connect(func() -> void:
			await get_tree().process_frame
			if not is_instance_valid(scroll) or not is_instance_valid(selected_panel):
				return
			var center: float = selected_panel.position.x + selected_panel.size.x * 0.5
			scroll.scroll_horizontal = int(maxf(center - scroll.size.x * 0.5, 0.0))
		, CONNECT_ONE_SHOT)

	return scroll

# --- Großes Bild -----------------------------------------------------------

func _character_texture(character: CharacterData) -> Texture2D:
	if character.portrait:
		return character.portrait
	var frames: SpriteFrames = character.sprite_frames
	if frames and frames.has_animation("Idle_Front") and frames.get_frame_count("Idle_Front") > 0:
		return frames.get_frame_texture("Idle_Front", 0)
	return null

func _make_portrait(character: CharacterData) -> Control:
	var panel := UIKit.make_panel(Color(character.accent_color, 0.1), Color(character.accent_color, 0.45), 0)
	panel.custom_minimum_size = Vector2(0.0, 320.0)

	if not _character_texture(character):
		panel.add_child(UIKit.make_label("Kein Sprite hinterlegt", 16, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_CENTER))
		return panel

	# PanelContainer streckt jedes Kind auf volle Größe - deshalb liegt alles
	# in einer freien Ebene, damit die Marke oben rechts bleiben kann.
	var layer := Control.new()
	layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.add_child(layer)

	# Atmender Körper, separat animierte Hände, Waffe in der rechten Hand.
	var portrait := CharacterPortrait.new()
	portrait.character = character
	portrait.weapon = RunState.get_equipped_weapon()
	portrait.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	layer.add_child(portrait)

	# Kraftstufe als Marke in der Ecke - wie das Level-Abzeichen in Brawl Stars.
	var badge := UIKit.make_chip(
		"Kraftstufe %d" % RunState.get_character_level(character.character_id),
		character.accent_color
	)
	badge.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT, Control.PRESET_MODE_MINSIZE)
	badge.position += Vector2(-16.0, 12.0)
	layer.add_child(badge)
	return panel

func _make_info(character: CharacterData) -> Control:
	var card := UICard.new(character.accent_color)
	var column := card.content
	column.add_theme_constant_override("separation", 8)

	column.add_child(UIKit.make_label(character.character_name, 26, character.accent_color))
	if not character.description.is_empty():
		column.add_child(UIKit.make_label(character.description, 15, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_LEFT, true))

	# Freigeschaltete Gadgets und Sternenkräfte stehen direkt beim Helden.
	var level := RunState.get_character_level(character.character_id)
	for star in character.get_unlocked_stars(level):
		column.add_child(UIKit.make_section(star.star_name, Palette.GOLD))
		if not star.description.is_empty():
			column.add_child(UIKit.make_label(star.description, 15, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_LEFT, true))

	if character.ability:
		# Fähigkeiten tragen überall ihre eigene Farbe - im Menü wie am Knopf im Spiel.
		var ability_color: Color = character.ability.color
		column.add_child(UIKit.make_section("Fähigkeit", ability_color))
		column.add_child(UIKit.make_label(
			"%s  ·  %.0fs" % [character.ability.ability_name, character.ability.cooldown],
			17, ability_color
		))
		if not character.ability.description.is_empty():
			column.add_child(UIKit.make_label(character.ability.description, 15, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_LEFT, true))

	column.add_child(UIKit.make_section("Attribute", character.accent_color))
	column.add_child(UIKit.make_attribute_row("Kraft", character.power, 10, Palette.EMBER))
	column.add_child(UIKit.make_attribute_row("Geschick", character.agility, 10, Palette.MOSS))
	column.add_child(UIKit.make_attribute_row("Vitalität", character.vitality, 10, Palette.GOLD))
	column.add_child(UIKit.make_attribute_row("Zähigkeit", character.toughness, 10, Palette.BONE))
	column.add_child(UIKit.make_attribute_row("Fokus", character.focus, 10, Palette.VIOLET))
	column.add_child(UIKit.make_attribute_row("Glück", character.fortune, 10, Palette.TEAL))

	# Endwerte inklusive Waffe, Accessoires, Upgrades und Wetter.
	column.add_child(UIKit.make_section("Werte mit Ausrüstung", character.accent_color))
	var stats := PlayerStats.preview(character)
	column.add_child(UIKit.make_stat_sheet(stats.describe_sheet(), 2))
	stats.free()

	var affinities := character.describe_affinities()
	if not affinities.is_empty():
		column.add_child(UIKit.make_section("Waffen-Boni", UIKit.GOOD))
		column.add_child(UIKit.make_label(affinities, 15, UIKit.GOOD, HORIZONTAL_ALIGNMENT_LEFT, true))

	return card

# --- Waffen ----------------------------------------------------------------

func _make_weapon_grid(character: CharacterData) -> Control:
	var grid := GridContainer.new()
	grid.columns = 2
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	grid.add_theme_constant_override("h_separation", 10)
	grid.add_theme_constant_override("v_separation", 10)

	var owned := RunState.get_owned_weapons()
	if owned.is_empty():
		grid.add_child(UIKit.make_label("Noch keine Waffen. Schau im Shop oder in der Werkstatt vorbei.", 15, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_LEFT, true))
		return grid

	var equipped_id := RunState.get_equipped_weapon_id(character.character_id)
	for weapon in owned:
		grid.add_child(_make_weapon_card(character, weapon, weapon.weapon_id == equipped_id))
	return grid

func _make_weapon_card(character: CharacterData, weapon: WeaponData, is_equipped: bool) -> Control:
	var affinity := character.get_affinity(weapon.category)
	var accent: Color = UIKit.GOOD if affinity else UIKit.ACCENT

	var panel := UICard.new(accent, UIKit.PANEL_HI if is_equipped else UIKit.PANEL)
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var row := UIKit.make_row(8)
	panel.content.add_child(row)
	row.add_child(UIKit.make_icon(weapon.icon, 44.0, accent))

	var card := UIKit.make_column(3)
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(card)
	var level := RunState.get_weapon_level(weapon.weapon_id)
	card.add_child(UIKit.make_label(weapon.display_name(level), 17, UIKit.TEXT))
	card.add_child(UIKit.make_label(weapon.get_category_name(), 14, UIKit.TEXT_DIM))
	# Der Schaden, den genau dieser Held mit genau dieser Schmiedestufe macht.
	card.add_child(UIKit.make_label(
		"%s · %.2fs" % [weapon.describe_damage(character, level), weapon.cooldown],
		14, UIKit.TEXT_DIM
	))
	var missing := weapon.describe_missing_requirements(character)
	if not missing.is_empty():
		card.add_child(UIKit.make_label("Braucht %s" % missing, 13, Palette.EMBER))
	if affinity:
		card.add_child(UIKit.make_label(affinity.describe(), 14, UIKit.GOOD, HORIZONTAL_ALIGNMENT_LEFT, true))
	if is_equipped:
		card.add_child(UIKit.make_label("Ausgerüstet", 14, accent))

	panel.gui_input.connect(func(event: InputEvent) -> void:
		if is_click(event):
			RunState.set_equipped_weapon(character.character_id, weapon.weapon_id)
			refresh()
	)
	return panel

# --- Accessoires -----------------------------------------------------------

func _make_accessory_grid(character: CharacterData) -> Control:
	var grid := GridContainer.new()
	grid.columns = 2
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	grid.add_theme_constant_override("h_separation", 10)
	grid.add_theme_constant_override("v_separation", 10)

	var owned := RunState.get_owned_accessories()
	if owned.is_empty():
		grid.add_child(UIKit.make_label("Noch keine Accessoires. Im Shop erhältlich.", 15, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_LEFT, true))
		return grid

	for accessory in owned:
		var equipped := RunState.is_accessory_equipped(character.character_id, accessory.accessory_id)
		grid.add_child(_make_accessory_card(character, accessory, equipped))
	return grid

func _make_accessory_card(character: CharacterData, accessory: AccessoryData, is_equipped: bool) -> Control:
	var rarity_color: Color = accessory.get_rarity_color()
	var panel := UICard.new(rarity_color, UIKit.PANEL_HI if is_equipped else UIKit.PANEL)
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var row := UIKit.make_row(8)
	panel.content.add_child(row)
	row.add_child(UIKit.make_icon(accessory.icon, 44.0, rarity_color))

	var card := UIKit.make_column(3)
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(card)
	card.add_child(UIKit.make_label(accessory.accessory_name, 17, rarity_color))
	card.add_child(UIKit.make_label(accessory.describe(), 14, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_LEFT, true))
	if is_equipped:
		card.add_child(UIKit.make_label("Angelegt", 14, rarity_color))

	panel.gui_input.connect(func(event: InputEvent) -> void:
		if is_click(event):
			RunState.toggle_accessory(character.character_id, accessory.accessory_id)
			refresh()
	)
	return panel
