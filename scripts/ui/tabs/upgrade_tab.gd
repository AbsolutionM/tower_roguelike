extends TownTab

## Ganz rechter Reiter: dauerhafter Fortschritt.
##
## Waffen  -> jede Waffe im Besitz einzeln schmieden (+0..+10, Elden Ring):
##            Material aus dem Lager plus Gold, Skalierungsnoten steigen mit.
## Helden  -> jeder Held einzeln auf Kraftstufe bringen (1..11, Brawl Stars):
##            Gold plus Essenz, pauschal Leben und Schaden, plus Freischaltungen.

enum Mode { WEAPON, CHARACTER }

var _mode: Mode = Mode.WEAPON
## Aufgeklappte Karte - nur eine, sonst wird die Liste unlesbar lang.
var _expanded_id: String = ""

func build() -> void:
	var column := make_page("Upgrades")
	column.add_child(_make_mode_switch())

	var content := make_scroll(column, 10)
	if _mode == Mode.WEAPON:
		_build_weapons(content)
	else:
		_build_characters(content)

func _make_mode_switch() -> Control:
	var row := UIKit.make_row(10)
	row.add_child(_make_mode_button("Schmiede", Mode.WEAPON, UIKit.COOL))
	row.add_child(_make_mode_button("Helden", Mode.CHARACTER, UIKit.ACCENT))
	return row

## Der aktive Modus wird gefüllt hervorgehoben. Ihn nur zu deaktivieren würde
## ihn ausgegraut aussehen lassen - also genau falsch herum.
func _make_mode_button(text: String, mode: Mode, accent: Color) -> Button:
	var is_active: bool = _mode == mode
	var button := UIKit.make_button(text, 18, accent)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.custom_minimum_size = Vector2(0.0, 52.0)

	if is_active:
		button.add_theme_stylebox_override("normal", UIKit.panel_style(Color(accent, 0.24), 0, accent))
		button.add_theme_stylebox_override("hover", UIKit.panel_style(Color(accent, 0.32), 0, accent))
		button.add_theme_color_override("font_color", Palette.highlight(accent))
	else:
		button.add_theme_color_override("font_color", UIKit.TEXT_DIM)
		button.pressed.connect(func() -> void: _switch(mode))

	return button

func _switch(mode: Mode) -> void:
	_mode = mode
	_expanded_id = ""
	refresh()

func _toggle(id: String) -> void:
	_expanded_id = "" if _expanded_id == id else id
	refresh()

# --- Schmiede --------------------------------------------------------------

func _build_weapons(content: VBoxContainer) -> void:
	var character := RunState.get_selected_character()
	var weapons := RunState.get_owned_weapons()

	content.add_child(UIKit.make_label(
		"Werte gelten für %s. Ein anderer Held holt aus derselben Waffe andere Zahlen." % (
			character.character_name if character else "niemanden"
		),
		15, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_LEFT, true
	))

	if weapons.is_empty():
		content.add_child(UIKit.make_label(
			"Noch keine Waffen. Kaufe im Shop oder baue in der Werkstatt.",
			16, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_LEFT, true
		))
		return

	var equipped := RunState.get_equipped_weapon()
	for weapon in weapons:
		content.add_child(_make_weapon_card(weapon, character, weapon == equipped))

func _make_weapon_card(weapon: WeaponData, character: CharacterData, is_equipped: bool) -> Control:
	var level := RunState.get_weapon_level(weapon.weapon_id)
	var is_max: bool = level >= Progression.MAX_REINFORCE
	var can_forge := RunState.can_reinforce(weapon)
	var expanded: bool = _expanded_id == weapon.weapon_id

	var accent: Color = Palette.GOLD if is_max else (UIKit.COOL if can_forge else Palette.MIST)
	var panel := UICard.new(accent, UIKit.PANEL_HI if is_equipped else Palette.SHADOW)
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	panel.gui_input.connect(func(event: InputEvent) -> void:
		if is_click(event):
			_toggle(weapon.weapon_id)
	)

	var column := panel.content
	column.add_theme_constant_override("separation", 6)

	# Kopfzeile: Name +Stufe, Kategorie, Stufenbalken
	var header := UIKit.make_row(10)
	column.add_child(header)

	var title := UIKit.make_column(2)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	title.add_child(UIKit.make_label(weapon.display_name(level), 19, UIKit.TEXT))

	var subtitle := weapon.get_category_name()
	if is_equipped:
		subtitle += "  ·  ausgerüstet"
	title.add_child(UIKit.make_label(subtitle, 14, UIKit.TEXT_DIM))

	header.add_child(UIKit.make_label(
		"%.0f Schaden" % weapon.get_effective_damage(character, level),
		18, accent, HORIZONTAL_ALIGNMENT_RIGHT
	))

	column.add_child(_make_level_pips(level, Progression.MAX_REINFORCE, accent))

	var missing := weapon.describe_missing_requirements(character)
	if not missing.is_empty():
		column.add_child(UIKit.make_label(
			"Anforderung nicht erfüllt (%s) - %.0f%% Schaden" % [missing, WeaponData.REQUIREMENT_PENALTY * 100.0],
			14, Palette.EMBER, HORIZONTAL_ALIGNMENT_LEFT, true
		))

	if not expanded:
		column.add_child(UIKit.make_label("Tippen für Werte und Schmieden", 13, UIKit.TEXT_DIM))
		return panel

	column.add_child(UIKit.make_section("Skalierung", accent))
	column.add_child(_make_scaling_row(weapon, level, character))

	column.add_child(UIKit.make_section("Werte", accent))
	column.add_child(UIKit.make_stat_sheet(weapon.describe_sheet(character, level), 2))

	# Der Sonderschlag laedt sich im Kampf von selbst auf.
	if weapon.special:
		var special := weapon.special
		column.add_child(UIKit.make_section("Sonderschlag", special.color))
		column.add_child(UIKit.make_label(
			"%s  ·  nach %d Treffern" % [special.special_name, special.hits_required],
			16, special.color
		))
		if not special.description.is_empty():
			column.add_child(UIKit.make_label(
				special.description, 14, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_LEFT, true
			))

	if not weapon.description.is_empty():
		column.add_child(UIKit.make_label(weapon.description, 14, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_LEFT, true))

	column.add_child(_make_forge_section(weapon, character, level, is_max, can_forge))
	return panel

## Skalierungsnoten nebeneinander - der Kern des Elden-Ring-Gefühls.
func _make_scaling_row(weapon: WeaponData, level: int, character: CharacterData) -> Control:
	var row := UIKit.make_row(8)
	for entry in weapon.describe_scaling(level):
		var letter := str(entry["letter"])
		var box := UIKit.make_column(0)
		box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		box.add_child(UIKit.make_label(str(entry["name"]), 13, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_CENTER))
		box.add_child(UIKit.make_label(letter, 24, _letter_color(letter), HORIZONTAL_ALIGNMENT_CENTER))
		if character:
			box.add_child(UIKit.make_label(
				"%d" % _attribute_for(character, str(entry["name"])),
				13, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_CENTER
			))
		row.add_child(box)
	return row

func _attribute_for(character: CharacterData, attribute_name: String) -> int:
	match attribute_name:
		"Kraft":
			return character.power
		"Geschick":
			return character.agility
		"Glück":
			return character.fortune
	return 0

func _letter_color(letter: String) -> Color:
	match letter:
		"S":
			return Palette.GOLD
		"A":
			return Palette.AMBER
		"B":
			return Palette.MOSS
		"C":
			return Palette.TEAL
		"D":
			return Palette.AZURE
		"E":
			return Palette.MIST
	return Palette.STONE_LIGHT

func _make_forge_section(weapon: WeaponData, character: CharacterData, level: int, is_max: bool, can_forge: bool) -> Control:
	var column := UIKit.make_column(6)

	if is_max:
		column.add_child(UIKit.make_section("Schmieden", Palette.GOLD))
		column.add_child(UIKit.make_label("Höchste Stufe erreicht.", 15, UIKit.GOOD))
		return column

	var cost := RunState.get_reinforce_cost(weapon)
	var next_level := level + 1
	column.add_child(UIKit.make_section("Schmieden auf +%d" % next_level, UIKit.COOL))

	# Vorschau: was der nächste Schlag am Hammer bringt.
	var gain := weapon.get_effective_damage(character, next_level) - weapon.get_effective_damage(character, level)
	column.add_child(UIKit.make_label("+%.0f Schaden" % gain, 15, UIKit.GOOD))

	var have_gold: int = RunState.gold
	var need_gold: int = int(cost["gold"])
	column.add_child(UIKit.make_label(
		"Gold  %d / %d" % [have_gold, need_gold],
		15, UIKit.ACCENT if have_gold >= need_gold else UIKit.TEXT_DIM
	))

	var item: ItemData = cost["item"]
	var item_name: String = item.item_name if item else str(cost["item_id"])
	var have: int = int(cost["have"])
	var need: int = int(cost["need"])
	var material_row := UIKit.make_row(6)
	material_row.add_child(UIKit.make_item_icon(item, 24.0))
	material_row.add_child(UIKit.make_label(
		"%s  %d / %d" % [item_name, have, need],
		15, UIKit.GOOD if have >= need else UIKit.TEXT_DIM
	))
	column.add_child(material_row)

	var forge_button := UIKit.make_primary_button("Schmieden", 20, UIKit.COOL)
	forge_button.custom_minimum_size = Vector2(0.0, 50.0)
	forge_button.disabled = not can_forge
	forge_button.pressed.connect(func() -> void:
		if RunState.reinforce_weapon(weapon):
			refresh()
	)
	column.add_child(forge_button)
	return column

# --- Helden ----------------------------------------------------------------

func _build_characters(content: VBoxContainer) -> void:
	content.add_child(UIKit.make_label(
		"Jede Kraftstufe gibt +%d%% Leben und Schaden. Stufe %d bringt das Gadget, Stufe %d die Sternenkraft." % [
			int(Progression.POWER_LEVEL_BONUS * 100.0),
			Progression.GADGET_LEVEL,
			Progression.STAR_POWER_LEVEL
		],
		15, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_LEFT, true
	))

	var selected := RunState.get_selected_character()
	for character in Database.get_characters():
		if character:
			content.add_child(_make_character_card(character, character == selected))

func _make_character_card(character: CharacterData, is_selected: bool) -> Control:
	var level := RunState.get_character_level(character.character_id)
	var is_max: bool = level >= Progression.MAX_POWER_LEVEL
	var can_level := RunState.can_level_character(character)
	var expanded: bool = _expanded_id == character.character_id

	var accent: Color = character.accent_color
	var panel := UICard.new(accent, UIKit.PANEL_HI if is_selected else Palette.SHADOW)
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	panel.gui_input.connect(func(event: InputEvent) -> void:
		if is_click(event):
			_toggle(character.character_id)
	)

	var column := panel.content
	column.add_theme_constant_override("separation", 6)

	var header := UIKit.make_row(10)
	column.add_child(header)

	var title := UIKit.make_column(2)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	title.add_child(UIKit.make_label(character.character_name, 19, accent))
	title.add_child(UIKit.make_label(
		"Kraftstufe %d / %d" % [level, Progression.MAX_POWER_LEVEL],
		14, UIKit.TEXT_DIM
	))

	# Kraftstufe als große Zahl - so liest man die Liste im Vorbeigehen.
	header.add_child(UIKit.make_label("%d" % level, 30, accent, HORIZONTAL_ALIGNMENT_RIGHT))

	column.add_child(_make_level_pips(level - 1, Progression.MAX_POWER_LEVEL - 1, accent))

	if not expanded:
		column.add_child(UIKit.make_label("Tippen für Werte und Aufstieg", 13, UIKit.TEXT_DIM))
		return panel

	var factor := Progression.power_level_mult(level)
	column.add_child(UIKit.make_section("Aktueller Bonus", accent))
	column.add_child(UIKit.make_stat_sheet([
		{"name": "Leben", "value": "+%.0f%%" % ((factor - 1.0) * 100.0)},
		{"name": "Schaden", "value": "+%.0f%%" % ((factor - 1.0) * 100.0)}
	], 2))

	column.add_child(_make_star_rows(character, level, accent))

	if is_selected:
		column.add_child(UIKit.make_label("Aktuell gewählt", 14, UIKit.GOOD))
	else:
		var select_button := UIKit.make_button("Auswählen", 17, accent)
		select_button.custom_minimum_size = Vector2(0.0, 44.0)
		select_button.pressed.connect(func() -> void:
			RunState.set_selected_character(character.character_id)
			refresh()
		)
		column.add_child(select_button)

	column.add_child(_make_level_section(character, level, is_max, can_level, accent))
	return panel

## Gadget und Sternenkraft - freigeschaltet oder als Ausblick.
func _make_star_rows(character: CharacterData, level: int, accent: Color) -> Control:
	var column := UIKit.make_column(6)
	var entries := [
		{"star": character.gadget, "at": Progression.GADGET_LEVEL, "label": "Gadget"},
		{"star": character.star_power, "at": Progression.STAR_POWER_LEVEL, "label": "Sternenkraft"}
	]

	for entry in entries:
		var star: StarPowerData = entry["star"]
		if not star:
			continue
		var required: int = int(entry["at"])
		var unlocked: bool = level >= required
		column.add_child(UIKit.make_section(str(entry["label"]), accent if unlocked else UIKit.TEXT_DIM))
		column.add_child(UIKit.make_label(
			star.star_name if unlocked else "%s  (ab Stufe %d)" % [star.star_name, required],
			16, accent if unlocked else UIKit.TEXT_DIM
		))
		if not star.description.is_empty():
			column.add_child(UIKit.make_label(star.description, 14, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_LEFT, true))

	return column

func _make_level_section(character: CharacterData, level: int, is_max: bool, can_level: bool, accent: Color) -> Control:
	var column := UIKit.make_column(6)

	if is_max:
		column.add_child(UIKit.make_section("Aufstieg", Palette.GOLD))
		column.add_child(UIKit.make_label("Höchste Kraftstufe erreicht.", 15, UIKit.GOOD))
		return column

	var cost := RunState.get_power_cost(character)
	var next_level := level + 1
	column.add_child(UIKit.make_section("Aufstieg auf Stufe %d" % next_level, accent))

	var unlock := Progression.unlocks_at(next_level)
	if not unlock.is_empty():
		column.add_child(UIKit.make_label("Schaltet %s frei" % unlock, 15, UIKit.GOOD))

	var need_gold: int = int(cost["gold"])
	column.add_child(UIKit.make_label(
		"Gold  %d / %d" % [RunState.gold, need_gold],
		15, UIKit.ACCENT if RunState.gold >= need_gold else UIKit.TEXT_DIM
	))

	var need_essence: int = int(cost["essence"])
	var have_essence: int = int(cost["have_essence"])
	column.add_child(UIKit.make_label(
		"Essenz  %d / %d" % [have_essence, need_essence],
		15, UIKit.ESSENCE if have_essence >= need_essence else UIKit.TEXT_DIM
	))

	var level_button := UIKit.make_primary_button("Aufsteigen", 20, accent)
	level_button.custom_minimum_size = Vector2(0.0, 50.0)
	level_button.disabled = not can_level
	level_button.pressed.connect(func() -> void:
		if RunState.level_up_character(character):
			refresh()
	)
	column.add_child(level_button)
	return column

# --- Gemeinsames -----------------------------------------------------------

## Stufenanzeige als Kette gefüllter Blöcke - im Pixelraster, ohne Balkenwerte.
func _make_level_pips(filled: int, total: int, accent: Color) -> Control:
	var row := UIKit.make_row(3)
	for i in maxi(total, 1):
		var pip := Panel.new()
		pip.custom_minimum_size = Vector2(0.0, 8.0)
		pip.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var fill: Color = accent if i < filled else Color(accent, 0.14)
		pip.add_theme_stylebox_override("panel", UIKit.panel_style(fill, 0, Color(0.0, 0.0, 0.0, 0.0), 0))
		row.add_child(pip)
	return row
