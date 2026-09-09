extends Control
class_name StatBar

## Balken mit weicher Füllung und nachlaufendem "Ghost"-Anteil,
## damit Schaden sichtbar wird statt nur zu verschwinden.

@export var fill_color: Color = Palette.MOSS
@export var ghost_color: Color = Palette.BLOOD
@export var background_color: Color = Color(Palette.INK, 0.88)
@export var border_color: Color = Palette.STONE_LIGHT
@export var corner_radius: int = 7
@export var fill_speed: float = 12.0
@export var ghost_speed: float = 3.0

@export_group("Texturen")
## Optionale Texturen statt der gezeichneten Balken.
@export var background_texture: Texture2D
@export var fill_texture: Texture2D

var value: float = 1.0
var max_value: float = 1.0

var _display: float = 1.0
var _ghost: float = 1.0

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func set_value(new_value: float, new_max: float) -> void:
	max_value = maxf(new_max, 0.0001)
	value = clampf(new_value, 0.0, max_value)

func get_ratio() -> float:
	return clampf(value / max_value, 0.0, 1.0)

func _process(delta: float) -> void:
	var ratio := get_ratio()
	_display = lerpf(_display, ratio, clampf(delta * fill_speed, 0.0, 1.0))
	if _ghost > _display:
		_ghost = lerpf(_ghost, ratio, clampf(delta * ghost_speed, 0.0, 1.0))
	else:
		_ghost = _display
	queue_redraw()

func _draw() -> void:
	var full := Rect2(Vector2.ZERO, size)
	var pixel: float = UIKit.PIXEL

	if background_texture:
		draw_texture_rect(background_texture, full, false)
		if fill_texture and _display > 0.001:
			var textured_width: float = PixelDraw.quantize((size.x - pixel * 2.0) * _display, pixel)
			var textured_fill := Rect2(Vector2(pixel, pixel), Vector2(textured_width, size.y - pixel * 2.0))
			draw_texture_rect(fill_texture, textured_fill, false, fill_color)
		return

	draw_rect(full, background_color)

	var inner_position := Vector2(pixel, pixel)
	var inner_size := size - Vector2(pixel, pixel) * 2.0

	# Balken wachsen in ganzen Pixelblöcken statt fließend.
	if _ghost > 0.001:
		var ghost_width: float = PixelDraw.quantize(inner_size.x * _ghost, pixel)
		if ghost_width > 0.0:
			draw_rect(Rect2(inner_position, Vector2(ghost_width, inner_size.y)), ghost_color)

	if _display > 0.001:
		var fill_width: float = PixelDraw.quantize(inner_size.x * _display, pixel)
		if fill_width > 0.0:
			draw_rect(Rect2(inner_position, Vector2(fill_width, inner_size.y)), fill_color)
			draw_rect(Rect2(inner_position, Vector2(fill_width, pixel)), Color(1.0, 1.0, 1.0, 0.22))

	PixelDraw.frame(self, full, pixel * 0.5, border_color, 1)
