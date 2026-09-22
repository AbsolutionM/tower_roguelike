extends Control

## Stadtbildschirm mit fünf Reitern unten (Shop, Held, Start, Werkstatt, Upgrades).
## Der mittlere Reiter ist der Start-Tab und wird hervorgehoben.

const TAB_SCRIPTS := [
	preload("res://scripts/ui/tabs/shop_tab.gd"),
	preload("res://scripts/ui/tabs/character_tab.gd"),
	preload("res://scripts/ui/tabs/start_tab.gd"),
	preload("res://scripts/ui/tabs/crafting_tab.gd"),
	preload("res://scripts/ui/tabs/upgrade_tab.gd")
]
const TAB_NAMES := ["Shop", "Held", "Start", "Werkstatt", "Upgrades"]
const START_TAB := 2

var _current_tab: int = START_TAB
var _content_host: Control
var _currency_box: HBoxContainer
var _summary_label: Label
var _tab_buttons: Array[Button] = []

func _ready() -> void:
	UIKit.apply_pixel_theme(self)
	_build_layout()
	_select_tab(START_TAB)

	RunState.gold_changed.connect(func(_amount: int) -> void: _update_header())
	RunState.essence_changed.connect(func(_id: String, _amount: int) -> void: _update_header())
	RunState.loadout_changed.connect(_update_header)

func _build_layout() -> void:
	var background := ColorRect.new()
	background.color = UIKit.BG
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(background)

	var root := VBoxContainer.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_theme_constant_override("separation", 0)
	add_child(root)
	# Wird unten um die sicheren Ränder verschoben.

	root.add_child(_build_header())

	_content_host = Control.new()
	_content_host.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_content_host.clip_contents = true
	root.add_child(_content_host)

	root.add_child(_build_tab_bar())

	# Kerbe oben, Home-Indikator unten: der Inhalt rückt hinein, der
	# Hintergrund bleibt randlos.
	var insets := UIKit.safe_insets(get_viewport())
	root.offset_top = insets.x
	root.offset_bottom = -insets.y

func _build_header() -> Control:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UIKit.panel_style(UIKit.BG_SOFT, 0, Color(1.0, 1.0, 1.0, 0.06), 0))

	var row := UIKit.make_row(12)
	panel.add_child(row)

	_summary_label = UIKit.make_flex_label("", 16, UIKit.TEXT_DIM)
	_summary_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(_summary_label)

	_currency_box = UIKit.make_row(8)
	row.add_child(_currency_box)

	_update_header()
	return panel

func _update_header() -> void:
	if _currency_box:
		for child in _currency_box.get_children():
			_currency_box.remove_child(child)
			child.queue_free()
		_currency_box.add_child(UIKit.make_chip("%d Gold" % RunState.gold, UIKit.ACCENT))
		_currency_box.add_child(UIKit.make_chip("%d Essenz" % RunState.get_total_essence(), UIKit.ESSENCE))

	if not _summary_label:
		return

	var character := RunState.get_selected_character()
	var weapon := RunState.get_equipped_weapon()
	var tower := RunState.get_selected_tower()
	var parts: Array[String] = []
	if character:
		parts.append(character.character_name)
	if weapon:
		parts.append(weapon.weapon_name)
	if tower:
		parts.append(tower.tower_name)
	_summary_label.text = "  ·  ".join(parts)

func _build_tab_bar() -> Control:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UIKit.panel_style(UIKit.BG_SOFT, 0, Color(1.0, 1.0, 1.0, 0.08), 0))

	var row := UIKit.make_row(3)
	panel.add_child(row)

	_tab_buttons.clear()
	for i in TAB_NAMES.size():
		var is_start: bool = i == START_TAB
		var button := UIKit.make_button(TAB_NAMES[i], 15 if is_start else 13, _tab_accent(i))
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.custom_minimum_size = Vector2(0.0, 108.0 if is_start else 92.0)
		# Ein Fünftel der Breite ist knapp: der Innenrand muss schmal bleiben,
		# sonst passt "Werkstatt" nicht mehr hinein.
		button.clip_text = false
		for state in ["normal", "hover", "pressed", "disabled", "focus"]:
			var box: StyleBoxFlat = button.get_theme_stylebox(state)
			if box:
				box.content_margin_left = 2.0
				box.content_margin_right = 2.0
		var index := i
		button.pressed.connect(func() -> void: _select_tab(index))
		row.add_child(button)
		_tab_buttons.append(button)

	return panel

## Der Start-Reiter trägt die Gold-Akzentfarbe, die übrigen den kühlen Ton.
func _tab_accent(index: int) -> Color:
	return UIKit.ACCENT if index == START_TAB else UIKit.COOL

## Wie `UIKit.panel_style`, nur mit schmalem Innenrand - sonst passen
## die Reiterbeschriftungen nicht in ein Fünftel der Bildschirmbreite.
func _tab_style(fill: Color, border: Color) -> StyleBoxFlat:
	var box := UIKit.panel_style(fill, 0, border)
	box.content_margin_left = 4.0
	box.content_margin_right = 4.0
	return box

func _select_tab(index: int) -> void:
	_current_tab = index

	for child in _content_host.get_children():
		_content_host.remove_child(child)
		child.queue_free()

	var tab: Control = TAB_SCRIPTS[index].new()
	_content_host.add_child(tab)

	_style_tabs()
	_update_header()

## Der aktive Reiter wird gefüllt hervorgehoben statt ausgegraut.
func _style_tabs() -> void:
	for i in _tab_buttons.size():
		var button := _tab_buttons[i]
		var accent: Color = _tab_accent(i)
		if i == _current_tab:
			button.add_theme_stylebox_override("normal", _tab_style(Color(accent, 0.22), accent))
			button.add_theme_stylebox_override("hover", _tab_style(Color(accent, 0.32), accent))
			button.add_theme_color_override("font_color", Palette.highlight(accent))
		else:
			button.add_theme_stylebox_override("normal", _tab_style(UIKit.PANEL, Color(accent, 0.22)))
			button.add_theme_stylebox_override("hover", _tab_style(UIKit.PANEL_HI, Color(accent, 0.45)))
			button.add_theme_color_override("font_color", UIKit.TEXT_DIM)
