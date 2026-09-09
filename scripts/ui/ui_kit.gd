extends RefCounted
class_name UIKit

## Gemeinsame Farben und Bausteine für alle Menüs, damit alles gleich aussieht.

const BG := Palette.INK
const BG_SOFT := Palette.SHADOW
const PANEL := Palette.STONE
const PANEL_HI := Palette.STONE_LIGHT
const TEXT := Palette.BONE
const TEXT_DIM := Palette.MIST
const ACCENT := Palette.GOLD
const GOOD := Palette.MOSS
const BAD := Palette.BLOOD
const COOL := Palette.AZURE
## Zweitwährung - überall dieselbe Farbe (Stadt-Chip wie HUD-Zähler).
const ESSENCE := Palette.TEAL

## Kantenlänge eines UI-Pixels (im 720x1280-Raster).
const PIXEL := 4.0

static var _pixel_font: Font
static var _pixel_theme: Theme

## Standardschrift ohne Kantenglättung - dadurch wirken Texte pixelig.
static func pixel_font() -> Font:
	if _pixel_font:
		return _pixel_font

	var base := ThemeDB.fallback_font
	var copy := base.duplicate()
	if copy:
		if "antialiasing" in copy:
			copy.antialiasing = TextServer.FONT_ANTIALIASING_NONE
		if "hinting" in copy:
			copy.hinting = TextServer.HINTING_NONE
		if "subpixel_positioning" in copy:
			copy.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
		_pixel_font = copy
	else:
		_pixel_font = base
	return _pixel_font

static func pixel_theme() -> Theme:
	if _pixel_theme:
		return _pixel_theme
	var theme := Theme.new()
	theme.default_font = pixel_font()
	_pixel_theme = theme
	return _pixel_theme

## Einmal pro Szene aufrufen - setzt die Pixelschrift für den gesamten Baum.
static func apply_pixel_theme(node: Node) -> void:
	if not node.is_inside_tree():
		return
	var window := node.get_tree().root
	if window.theme != pixel_theme():
		window.theme = pixel_theme()

## Rechteckiger Kasten mit harten Ecken - `radius` wird bewusst ignoriert,
## damit die gesamte UI zum Pixel-Look passt.
static func panel_style(fill: Color, _radius: int = 0, border: Color = Color(1.0, 1.0, 1.0, 0.09), border_width: int = 2) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = fill
	box.set_corner_radius_all(0)
	box.set_border_width_all(border_width)
	box.border_color = border
	box.content_margin_left = 14.0
	box.content_margin_right = 14.0
	box.content_margin_top = 10.0
	box.content_margin_bottom = 10.0
	return box

## `wrap` nur für Fließtext einschalten - in einer HBox schrumpfen umbrechende
## Labels sonst auf ein Zeichen Breite zusammen.
static func make_label(text: String, font_size: int = 22, color: Color = TEXT, alignment: int = HORIZONTAL_ALIGNMENT_LEFT, wrap: bool = false) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	label.horizontal_alignment = alignment
	if wrap:
		label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return label

static func make_button(text: String, font_size: int = 22, accent: Color = ACCENT) -> Button:
	var button := Button.new()
	button.text = text
	button.add_theme_font_size_override("font_size", font_size)
	button.add_theme_color_override("font_color", TEXT)
	button.add_theme_color_override("font_hover_color", Color(1.0, 1.0, 1.0))
	button.add_theme_color_override("font_pressed_color", Color(1.0, 1.0, 1.0))
	button.add_theme_color_override("font_disabled_color", TEXT_DIM)
	button.add_theme_stylebox_override("normal", panel_style(PANEL, 12, Color(accent, 0.35)))
	button.add_theme_stylebox_override("hover", panel_style(PANEL_HI, 12, Color(accent, 0.75)))
	button.add_theme_stylebox_override("pressed", panel_style(Color(accent, 0.3), 12, accent))
	button.add_theme_stylebox_override("disabled", panel_style(Color(PANEL, 0.45), 12, Color(1.0, 1.0, 1.0, 0.05)))
	button.add_theme_stylebox_override("focus", panel_style(Color(0.0, 0.0, 0.0, 0.0), 12, Color(accent, 0.45)))
	button.custom_minimum_size = Vector2(0.0, 54.0)
	# Jeder Knopf im Spiel läuft durch hier - der Tastton hängt deshalb an
	# einer Stelle statt an fünfzig Aufrufern.
	button.pressed.connect(func() -> void: Audio.play(Audio.ID_UI_TAP))
	return button

## Gefüllter Knopf für die eine Hauptaktion eines Bildschirms.
## Dadurch gibt es pro Screen genau einen Blickfang statt fünf gleich starker Kästen.
static func make_primary_button(text: String, font_size: int = 26, accent: Color = ACCENT) -> Button:
	# Gefüllt, aber abgedunkelt - ein voll gesättigter Balken über die ganze
	# Breite erschlägt sonst den Rest des Bildschirms.
	var button := make_button(text, font_size, accent)
	var light: Color = Palette.highlight(accent)
	button.add_theme_color_override("font_color", light)
	button.add_theme_color_override("font_hover_color", Palette.BONE)
	button.add_theme_color_override("font_pressed_color", Palette.BONE)
	button.add_theme_stylebox_override("normal", panel_style(accent.darkened(0.62), 0, accent))
	button.add_theme_stylebox_override("hover", panel_style(accent.darkened(0.45), 0, light))
	button.add_theme_stylebox_override("pressed", panel_style(accent.darkened(0.25), 0, light))
	return button

static func make_panel(fill: Color = PANEL, border: Color = Color(1.0, 1.0, 1.0, 0.09), radius: int = 14) -> PanelContainer:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", panel_style(fill, radius, border))
	return panel

## Icon-Kachel. Ohne Textur ein farbiger Platzhalter - so bleibt das Layout gleich,
## sobald echte Icons eingesetzt werden.
static func make_icon(texture: Texture2D, icon_size: float, fallback_color: Color) -> Control:
	if texture:
		var rect := TextureRect.new()
		rect.texture = texture
		rect.custom_minimum_size = Vector2(icon_size, icon_size)
		rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		return rect

	var placeholder := Panel.new()
	placeholder.custom_minimum_size = Vector2(icon_size, icon_size)
	placeholder.add_theme_stylebox_override(
		"panel",
		panel_style(Color(fallback_color, 0.22), 8, Color(fallback_color, 0.55))
	)
	return placeholder

## Icon eines Items. Ohne Textur wird die Form gezeichnet, statt ein
## farbiges Quadrat zu zeigen.
static func make_item_icon(item: ItemData, icon_size: float) -> Control:
	if not item:
		return make_spacer(icon_size)
	if item.icon:
		return make_icon(item.icon, icon_size, item.get_rarity_color())

	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(icon_size, icon_size)
	panel.size_flags_vertical = Control.SIZE_SHRINK_CENTER

	# Eigener Stil mit schmalem Innenrand: der Standardrand von 14 Pixeln
	# würde die Kachel auf das Doppelte aufblasen und Zeilen abschneiden.
	var rarity := item.get_rarity_color()
	var box := panel_style(Color(rarity, 0.14), 0, Color(rarity, 0.45))
	box.content_margin_left = 2.0
	box.content_margin_right = 2.0
	box.content_margin_top = 2.0
	box.content_margin_bottom = 2.0
	panel.add_theme_stylebox_override("panel", box)

	var symbol := ItemSymbol.new()
	symbol.kind = item.symbol
	symbol.tint = item.color
	symbol.symbol_size = icon_size * 0.7
	# Mindestgröße sofort setzen - `_ready` käme zu spät für den Layoutlauf.
	symbol.custom_minimum_size = Vector2.ONE * (icon_size - 8.0)
	panel.add_child(symbol)
	return panel

static func make_spacer(height: float) -> Control:
	var spacer := Control.new()
	spacer.custom_minimum_size = Vector2(0.0, height)
	return spacer

static func make_column(separation: int = 12) -> VBoxContainer:
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", separation)
	return column

static func make_row(separation: int = 12) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", separation)
	return row

static func make_screen_root(parent: Control, margin: int = 28) -> VBoxContainer:
	var background := ColorRect.new()
	background.color = BG
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(background)

	var margin_box := MarginContainer.new()
	margin_box.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin_box.add_theme_constant_override("margin_left", margin)
	margin_box.add_theme_constant_override("margin_right", margin)
	margin_box.add_theme_constant_override("margin_top", margin)
	margin_box.add_theme_constant_override("margin_bottom", margin)
	parent.add_child(margin_box)

	var column := make_column(14)
	margin_box.add_child(column)
	return column

## Zeile "Name  [Balken]  Wert" für Attribute.
static func make_attribute_row(attribute_name: String, value: int, maximum: int, color: Color) -> HBoxContainer:
	var row := make_row(10)

	var name_label := make_label(attribute_name, 17, TEXT_DIM)
	name_label.custom_minimum_size = Vector2(104.0, 0.0)
	row.add_child(name_label)

	var bar := StatBar.new()
	bar.fill_color = color
	bar.ghost_color = Color(color, 0.3)
	bar.corner_radius = 5
	bar.custom_minimum_size = Vector2(0.0, 16.0)
	bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	bar.set_value(float(value), float(maximum))
	row.add_child(bar)

	var value_label := make_label(str(value), 17, TEXT, HORIZONTAL_ALIGNMENT_RIGHT)
	value_label.custom_minimum_size = Vector2(30.0, 0.0)
	row.add_child(value_label)

	return row

## Abschnittsüberschrift mit Trennlinie, damit lange Listen Struktur bekommen.
static func make_section(title: String, accent: Color = TEXT_DIM) -> Control:
	var row := make_row(10)

	row.add_child(make_label(title, 19, accent))

	var rule := Panel.new()
	rule.custom_minimum_size = Vector2(0.0, 2.0)
	rule.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rule.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	rule.add_theme_stylebox_override("panel", panel_style(Color(accent, 0.22), 0, Color(0.0, 0.0, 0.0, 0.0), 0))
	row.add_child(rule)

	return row

## Kleines umrandetes Feld - für Währungen und Kurzinfos.
static func make_chip(text: String, color: Color) -> Control:
	var panel := PanelContainer.new()
	var box := panel_style(Color(color, 0.16), 0, Color(color, 0.5), 2)
	box.content_margin_left = 10.0
	box.content_margin_right = 10.0
	box.content_margin_top = 3.0
	box.content_margin_bottom = 3.0
	panel.add_theme_stylebox_override("panel", box)
	panel.add_child(make_label(text, 17, color))
	return panel

## Zweispaltige Werteübersicht: [{ "name": ..., "value": ... }, ...]
static func make_stat_sheet(entries: Array, columns: int = 2) -> Control:
	var grid := GridContainer.new()
	grid.columns = maxi(columns, 1) * 2
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	grid.add_theme_constant_override("h_separation", 12)
	grid.add_theme_constant_override("v_separation", 5)

	for entry in entries:
		var name_label := make_label(str(entry["name"]), 15, TEXT_DIM)
		name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		grid.add_child(name_label)
		grid.add_child(make_label(str(entry["value"]), 15, TEXT, HORIZONTAL_ALIGNMENT_RIGHT))

	return grid

static func make_currency_row(gold: int, essence: int) -> HBoxContainer:
	var row := make_row(10)
	row.add_child(make_chip("%d Gold" % gold, ACCENT))
	row.add_child(make_chip("%d Essenz" % essence, ESSENCE))
	return row
