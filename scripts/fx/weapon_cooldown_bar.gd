extends Node2D
class_name WeaponCooldownBar

## Kleine Leiste über dem Helden, solange die Waffe nachlädt. Sie füllt sich
## bis zum nächsten Schlag, blitzt kurz auf und verschwindet.

@export var bar_size: Vector2 = Vector2(40.0, 6.0)
@export var height: float = 50.0
@export var fill_color: Color = Palette.AMBER
@export var ready_color: Color = Palette.BONE

var controller: Node

var _alpha: float = 0.0
var _ratio: float = 1.0
var _was_cooling: bool = false
var _flash: float = 0.0

func _ready() -> void:
	z_index = 150
	z_as_relative = false
	position = Vector2(0.0, -height)

func _process(delta: float) -> void:
	if not is_instance_valid(controller) or not controller.equipped_weapon:
		visible = false
		return
	var total: float = maxf(controller._last_cooldown, 0.001)
	var remaining: float = controller.fire_timer
	var cooling: bool = remaining > 0.0
	_ratio = clampf(1.0 - remaining / total, 0.0, 1.0)

	if cooling:
		_alpha = minf(_alpha + delta * 12.0, 1.0)
	else:
		# Gerade wieder bereit: kurz hell aufblitzen, dann ausblenden.
		if _was_cooling:
			_flash = 1.0
			_ratio = 1.0
		_alpha = maxf(_alpha - delta * 6.0, 0.0)
	_flash = maxf(_flash - delta * 6.0, 0.0)
	_was_cooling = cooling
	visible = _alpha > 0.01
	if visible:
		queue_redraw()

func _draw() -> void:
	var pixel: float = FX.pixel_size() * 0.5
	var origin := Vector2(-bar_size.x * 0.5, -bar_size.y * 0.5)
	var outer := Rect2(origin - Vector2.ONE * pixel, bar_size + Vector2.ONE * pixel * 2.0)
	draw_rect(outer, Color(Palette.INK, 0.85 * _alpha))
	draw_rect(Rect2(origin, bar_size), Color(Palette.STONE, 0.9 * _alpha))
	var width: float = PixelDraw.quantize(bar_size.x * _ratio, pixel)
	if width > 0.0:
		var tint: Color = fill_color.lerp(ready_color, _flash)
		draw_rect(Rect2(origin, Vector2(width, bar_size.y)), Color(tint, _alpha))
		draw_rect(Rect2(origin, Vector2(width, pixel)), Color(1.0, 1.0, 1.0, 0.25 * _alpha))
