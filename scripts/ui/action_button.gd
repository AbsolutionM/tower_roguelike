extends Control
class_name ActionButton

## Eckiger Touch-Button im Pixelraster. Der Cooldown läuft als Block von
## unten nach oben voll statt als runder Ring. Icon optional - ohne Icon
## wird der Buchstabe aus `label_text` gezeichnet.

signal pressed_action

enum Action { NONE, DASH, ABILITY }

@export var action: Action = Action.NONE
@export var label_text: String = "A"
@export var icon: Texture2D
@export var radius: float = 46.0
@export var button_color: Color = Palette.GOLD
@export var disabled_color: Color = Palette.STONE_LIGHT
## Optionaler Hintergrund statt des gezeichneten Kreises.
@export var background_texture: Texture2D

var cooldown_remaining: float = 0.0
var cooldown_total: float = 0.0

var _touch_index: int = -1
var _scale: float = 1.0
var _ready_pulse: float = 0.0

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	custom_minimum_size = Vector2(radius * 2.0, radius * 2.0)

func _gui_input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		if event.pressed and _inside(event.position):
			_touch_index = event.index
			_press()
		elif not event.pressed and event.index == _touch_index:
			_touch_index = -1
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed and _inside(event.position):
			_press()

## Etwas größer als die gezeichnete Fläche - Daumen treffen selten mittig.
func _inside(local_position: Vector2) -> bool:
	var offset := local_position - size * 0.5
	var reach: float = radius * 1.2
	return absf(offset.x) <= reach and absf(offset.y) <= reach

func _press() -> void:
	if cooldown_remaining > 0.0:
		_scale = 0.94
		return

	_scale = 0.82
	pressed_action.emit()

	match action:
		Action.DASH:
			PlayerInput.request_dash()
		Action.ABILITY:
			PlayerInput.request_ability()
		_:
			pass

func set_cooldown(remaining: float, total: float) -> void:
	var was_on_cooldown := cooldown_remaining > 0.0
	cooldown_remaining = maxf(remaining, 0.0)
	cooldown_total = maxf(total, 0.0001)
	if was_on_cooldown and cooldown_remaining <= 0.0:
		_ready_pulse = 1.0

func _process(delta: float) -> void:
	_scale = lerpf(_scale, 1.0, clampf(delta * 12.0, 0.0, 1.0))
	if _ready_pulse > 0.0:
		_ready_pulse = maxf(_ready_pulse - delta * 2.5, 0.0)
	queue_redraw()

func _draw() -> void:
	var pixel: float = UIKit.PIXEL
	var center: Vector2 = PixelDraw.snap(size * 0.5, pixel)
	var draw_radius: float = maxf(PixelDraw.quantize(radius * _scale, pixel), pixel * 2.0)
	var is_ready: bool = cooldown_remaining <= 0.0
	var main_color: Color = button_color if is_ready else disabled_color
	var block := _block(center, draw_radius)

	if background_texture:
		var background_size := Vector2.ONE * draw_radius * 2.3
		draw_texture_rect(
			background_texture,
			Rect2(center - background_size * 0.5, background_size),
			false,
			Color(1.0, 1.0, 1.0, 1.0 if is_ready else 0.6)
		)
	else:
		# Abgeschrägte Ecken: drei Streifen statt eines Kreises -
		# derselbe Look wie die Pixelrahmen im restlichen Menü.
		_chamfered(block, pixel, Color(Palette.INK, 0.72))
		_chamfered(block, pixel, Color(main_color, 0.22))
		PixelDraw.frame(self, block.grow(-pixel), pixel, Color(main_color, 0.9), 1)

	if not is_ready:
		# Der Block läuft von unten voll, bis die Aktion wieder bereit ist.
		var progress: float = 1.0 - clampf(cooldown_remaining / cooldown_total, 0.0, 1.0)
		var inner := block.grow(-pixel * 2.0)
		var filled: float = PixelDraw.quantize(inner.size.y * progress, pixel)
		if filled > 0.0:
			draw_rect(
				Rect2(Vector2(inner.position.x, inner.end.y - filled), Vector2(inner.size.x, filled)),
				Color(main_color, 0.3)
			)
			draw_rect(
				Rect2(Vector2(inner.position.x, inner.end.y - filled), Vector2(inner.size.x, pixel)),
				Color(main_color, 0.75)
			)

	if _ready_pulse > 0.0:
		var pulse: float = draw_radius + (1.0 - _ready_pulse) * pixel * 4.0
		PixelDraw.frame(self, _block(center, pulse), pixel, Color(main_color, _ready_pulse * 0.7), 1)

	if icon:
		var icon_size: Vector2 = icon.get_size()
		var target := Vector2.ONE * draw_radius * 1.1
		var icon_scale: float = minf(target.x / maxf(icon_size.x, 1.0), target.y / maxf(icon_size.y, 1.0))
		var draw_size := icon_size * icon_scale
		draw_texture_rect(icon, Rect2(center - draw_size * 0.5, draw_size), false, Color(1.0, 1.0, 1.0, 1.0 if is_ready else 0.55))
	else:
		var font := UIKit.pixel_font()
		var font_size := int(draw_radius * 0.75)
		var text_size := font.get_string_size(label_text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, font_size)
		draw_string(
			font,
			center + Vector2(-text_size.x * 0.5, text_size.y * 0.32),
			label_text,
			HORIZONTAL_ALIGNMENT_LEFT,
			-1.0,
			font_size,
			Color(Palette.highlight(main_color), 1.0 if is_ready else 0.5)
		)

func _block(center: Vector2, half_size: float) -> Rect2:
	return Rect2(center - Vector2.ONE * half_size, Vector2.ONE * half_size * 2.0)

## Rechteck mit weggelassenen Eckpixeln - wirkt wie ein gezeichneter Knopf,
## bleibt aber im Raster.
func _chamfered(rect: Rect2, pixel: float, color: Color) -> void:
	draw_rect(Rect2(rect.position + Vector2(pixel, 0.0), Vector2(rect.size.x - pixel * 2.0, pixel)), color)
	draw_rect(Rect2(rect.position + Vector2(0.0, pixel), Vector2(rect.size.x, rect.size.y - pixel * 2.0)), color)
	draw_rect(Rect2(Vector2(rect.position.x + pixel, rect.end.y - pixel), Vector2(rect.size.x - pixel * 2.0, pixel)), color)
