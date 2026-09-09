extends PanelContainer
class_name UICard

## Einheitliche Karte: farbiger Akzentstreifen oben, klarer Innenabstand.
## Inhalt kommt in `content`.

var content: VBoxContainer

func _init(accent: Color = Palette.GOLD, fill: Color = Palette.SHADOW, strip_height: float = 3.0) -> void:
	var box := StyleBoxFlat.new()
	box.bg_color = fill
	box.set_corner_radius_all(0)
	box.set_border_width_all(2)
	box.border_color = Color(accent, 0.3)
	box.content_margin_left = 0.0
	box.content_margin_right = 0.0
	box.content_margin_top = 0.0
	box.content_margin_bottom = 0.0
	add_theme_stylebox_override("panel", box)

	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 0)
	add_child(column)

	var strip := ColorRect.new()
	strip.color = accent
	strip.custom_minimum_size = Vector2(0.0, strip_height)
	column.add_child(strip)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 12)
	margin.add_theme_constant_override("margin_right", 12)
	margin.add_theme_constant_override("margin_top", 10)
	margin.add_theme_constant_override("margin_bottom", 10)
	column.add_child(margin)

	content = VBoxContainer.new()
	content.add_theme_constant_override("separation", 4)
	margin.add_child(content)
