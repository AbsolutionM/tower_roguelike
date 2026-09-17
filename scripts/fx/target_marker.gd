extends Node2D
class_name TargetMarker

## Zeigt vor dem Schlag, welcher Gegner getroffen wird:
## Pixel-Eckklammern um das Ziel und optional die Reichweite der Waffe.

@export var show_range_ring: bool = true
@export var fade_speed: float = 8.0

var target: Node2D
var accent: Color = Palette.GOLD
var attack_range: float = 200.0
## Versatz des Kegelursprungs gegenüber dem Anker (Mitte des Handkreises).
var origin_offset: Vector2 = Vector2.ZERO
## Mitte und halbe Öffnung des Angriffskegels, in Weltwinkeln.
var cone_direction: float = 0.0
var cone_half_angle: float = PI
## 1.0 = Angriff ist bereit, 0.0 = gerade erst zugeschlagen.
var cooldown_ratio: float = 1.0

var _anchor: Node2D
var _time: float = 0.0
var _strength: float = 0.0
var _was_ready: bool = false
var _pop: float = 0.0

func setup(anchor: Node2D) -> void:
	_anchor = anchor

func _ready() -> void:
	top_level = true
	z_index = 30
	z_as_relative = false

func _process(delta: float) -> void:
	_time += delta

	if _anchor and is_instance_valid(_anchor):
		global_position = _anchor.global_position + origin_offset

	if not is_instance_valid(target):
		target = null
	var has_target: bool = target != null
	_strength = move_toward(_strength, 1.0 if has_target else 0.0, delta * fade_speed)

	# Kleiner Puls, sobald der Angriff wieder bereit ist.
	var is_ready: bool = cooldown_ratio >= 0.999
	if is_ready and not _was_ready:
		_pop = 1.0
	_was_ready = is_ready
	_pop = maxf(_pop - delta * 4.0, 0.0)

	queue_redraw()

func _target_radius() -> float:
	if target and is_instance_valid(target) and target.has_method("get_visual_radius"):
		return target.get_visual_radius()
	return 26.0

## Die Reichweite als Kegel in Angriffsrichtung: Bogen vorn, zwei Kanten
## zum Helden. Ein voller Ring versprach Treffer, die es seitlich nicht gibt.
func _draw_cone(pixel: float) -> void:
	var tint := Color(accent, 0.18)
	var from_angle: float = cone_direction - cone_half_angle
	var to_angle: float = cone_direction + cone_half_angle
	PixelDraw.arc(self, Vector2.ZERO, attack_range, from_angle, to_angle, pixel, tint, 1)
	# Die Kanten beginnen ein Stück vor dem Helden, sonst kreuzen sie die Figur.
	var inner: float = minf(28.0, attack_range * 0.4)
	for angle in [from_angle, to_angle]:
		var direction := Vector2(cos(angle), sin(angle))
		PixelDraw.line(self, direction * inner, direction * attack_range, pixel, tint)

func _draw() -> void:
	var pixel: float = FX.pixel_size()

	if show_range_ring and attack_range > 0.0:
		_draw_cone(pixel)

	if _strength <= 0.01 or not target or not is_instance_valid(target):
		return

	var center := to_local(target.global_position)
	var radius: float = _target_radius() * (1.0 + 0.05 * sin(_time * 7.0) + 0.25 * _pop)
	var arm: float = radius * 0.5

	# Je näher der Angriff, desto heller die Klammern - aber immer gut sichtbar.
	var alpha: float = (0.6 + 0.4 * cooldown_ratio) * _strength
	var tint := Color(accent, alpha)
	var shadow := Color(Palette.INK, alpha * 0.7)

	for sign_x in [-1.0, 1.0]:
		for sign_y in [-1.0, 1.0]:
			var corner := center + Vector2(sign_x * radius, sign_y * radius)
			# Dunkler Versatz darunter, damit die Klammer auf jedem Boden lesbar ist.
			var offset := Vector2(-sign_x * pixel, -sign_y * pixel)
			PixelDraw.line(self, corner + offset, corner + offset - Vector2(sign_x * arm, 0.0), pixel, shadow)
			PixelDraw.line(self, corner + offset, corner + offset - Vector2(0.0, sign_y * arm), pixel, shadow)
			PixelDraw.line(self, corner, corner - Vector2(sign_x * arm, 0.0), pixel, tint)
			PixelDraw.line(self, corner, corner - Vector2(0.0, sign_y * arm), pixel, tint)

	if cooldown_ratio >= 0.999:
		PixelDraw.ring(self, center, radius * 1.2, pixel, Color(accent, 0.45 * _strength), 1)
