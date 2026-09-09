extends Control
class_name TouchJoystick

## Touch-Stick fürs Handy, funktioniert im Editor auch mit der Maus.
## Sprites optional: base_texture / knob_texture setzen, sonst wird gezeichnet.

@export var base_radius: float = 82.0
@export var knob_radius: float = 36.0
## Stick erscheint dort, wo der Finger aufsetzt (fühlt sich auf dem Handy besser an).
@export var dynamic: bool = true
@export var base_texture: Texture2D
@export var knob_texture: Texture2D
@export var base_color: Color = Color(1.0, 1.0, 1.0, 0.09)
@export var ring_color: Color = Color(1.0, 1.0, 1.0, 0.28)
@export var knob_color: Color = Color(1.0, 1.0, 1.0, 0.55)
@export var idle_alpha: float = 0.35

var _touch_index: int = -1
var _active: bool = false
var _center: Vector2 = Vector2.ZERO
var _knob: Vector2 = Vector2.ZERO
var _alpha: float = 0.0

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	_center = size * 0.5
	_knob = _center
	_alpha = idle_alpha

func _gui_input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		if event.pressed:
			_begin(event.position, event.index)
		elif event.index == _touch_index:
			_end()
	elif event is InputEventScreenDrag:
		if event.index == _touch_index:
			_update_knob(event.position)
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_begin(event.position, -2)
		elif _touch_index == -2:
			_end()
	elif event is InputEventMouseMotion and _active and _touch_index == -2:
		_update_knob(event.position)

func _begin(local_position: Vector2, index: int) -> void:
	_active = true
	_touch_index = index
	_center = local_position if dynamic else size * 0.5
	_update_knob(local_position)

func _update_knob(local_position: Vector2) -> void:
	var offset := local_position - _center
	_knob = _center + offset.limit_length(base_radius)
	PlayerInput.set_stick(offset / base_radius)

func _end() -> void:
	_active = false
	_touch_index = -1
	PlayerInput.release_stick()

func _process(delta: float) -> void:
	var target_alpha: float = 1.0 if _active else idle_alpha
	_alpha = lerpf(_alpha, target_alpha, clampf(delta * 10.0, 0.0, 1.0))

	if not _active:
		var rest := size * 0.5
		_center = _center.lerp(rest, clampf(delta * 12.0, 0.0, 1.0))
		_knob = _knob.lerp(_center, clampf(delta * 18.0, 0.0, 1.0))

	queue_redraw()

func _draw() -> void:
	var pixel: float = UIKit.PIXEL

	if base_texture:
		draw_texture(base_texture, _center - base_texture.get_size() * 0.5, Color(1.0, 1.0, 1.0, _alpha))
	else:
		# Grobes Raster für die Füllung, feines für die Ränder - spart Zeichenaufrufe.
		PixelDraw.disc(self, _center, base_radius, pixel * 3.0, Color(base_color, base_color.a * _alpha))
		PixelDraw.ring(self, _center, base_radius, pixel, Color(ring_color, ring_color.a * _alpha), 1)
		PixelDraw.ring(self, _center, base_radius * 0.32, pixel, Color(ring_color, ring_color.a * _alpha * 0.6), 1)

	if knob_texture:
		draw_texture(knob_texture, _knob - knob_texture.get_size() * 0.5, Color(1.0, 1.0, 1.0, _alpha))
	else:
		PixelDraw.disc(self, _knob, knob_radius, pixel * 2.0, Color(knob_color, knob_color.a * _alpha))
		PixelDraw.ring(self, _knob, knob_radius, pixel, Color(1.0, 1.0, 1.0, 0.7 * _alpha), 1)
		PixelDraw.stamp(self, _knob + Vector2(-knob_radius * 0.3, -knob_radius * 0.32), pixel * 2.0, Color(1.0, 1.0, 1.0, 0.5 * _alpha))
