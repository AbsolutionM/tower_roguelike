extends Camera2D
class_name GameCamera

## Zwei Modi: fest auf den Raum (Isaac-Stil) oder dem Spieler folgend (große Räume).
## Shake läuft über Trauma + Noise, damit es organisch statt zappelig wirkt.

enum Mode { FOLLOW, FIXED }

@export var mode: Mode = Mode.FOLLOW
@export var follow_speed: float = 9.0
@export var look_ahead: float = 0.1
@export var trauma_decay: float = 1.8
@export var max_shake_offset: Vector2 = Vector2(22.0, 18.0)
@export var max_shake_roll: float = 0.04
@export var zoom_punch_recovery: float = 7.0
## Grundzoom der Spielwelt. 1.5 = ein Weltpixelblock (4 px) wird 6 px groß -
## ganzzahlig, damit die Pixel gleich groß bleiben.
@export var base_zoom: float = 1.5

var trauma: float = 0.0
var fixed_position: Vector2 = Vector2.ZERO
var target: Node2D

## Höhe der Steuerleiste am unteren Rand. Das Spielfeld endet darüber:
## der Held sitzt mittig im sichtbaren Teil, und die Raumgrenzen sind so
## verschoben, dass die untere Wand oberhalb der Leiste liegt statt darunter.
var _bottom_reserve: float = 0.0
var _room_center: Vector2 = Vector2.ZERO
var _room_size: Vector2 = Vector2.ZERO

var _noise: FastNoiseLite
var _noise_time: float = 0.0
var _base_zoom: Vector2 = Vector2.ONE
var _zoom_punch: float = 0.0
## 1.0 = normal; im Überblick zu Raumbeginn kurz kleiner (weiter weg).
var _overview_factor: float = 1.0

func _ready() -> void:
	add_to_group("camera")
	top_level = true

	_base_zoom = Vector2.ONE * base_zoom
	zoom = _base_zoom
	_noise = FastNoiseLite.new()
	_noise.seed = randi()
	_noise.frequency = 0.9

	target = get_tree().get_first_node_in_group("player")
	if target:
		global_position = target.global_position
	fixed_position = global_position

func _process(delta: float) -> void:
	_update_position(delta)
	_update_shake(delta)
	_update_zoom(delta)

func _update_position(delta: float) -> void:
	var goal := fixed_position

	if mode == Mode.FOLLOW:
		if not target or not is_instance_valid(target):
			target = get_tree().get_first_node_in_group("player")
		if target:
			goal = target.global_position
			if target is CharacterBody2D:
				goal += target.velocity * look_ahead

	global_position = global_position.lerp(goal, clampf(follow_speed * delta, 0.0, 1.0))

func _update_shake(delta: float) -> void:
	# Der Versatz nach unten bleibt auch ohne Wackeln: er schiebt den Helden
	# aus dem Bereich hinter der Steuerleiste heraus.
	var reserve := Vector2(0.0, _bottom_reserve * 0.5)
	if trauma <= 0.0:
		offset = reserve
		rotation = 0.0
		return

	trauma = maxf(trauma - trauma_decay * delta, 0.0)
	_noise_time += delta * 55.0

	var strength: float = trauma * trauma
	offset = reserve + Vector2(
		_noise.get_noise_2d(_noise_time, 0.0) * max_shake_offset.x,
		_noise.get_noise_2d(0.0, _noise_time) * max_shake_offset.y
	) * strength
	rotation = _noise.get_noise_2d(_noise_time, _noise_time) * max_shake_roll * strength

func _update_zoom(delta: float) -> void:
	if _zoom_punch > 0.0:
		_zoom_punch = maxf(_zoom_punch - zoom_punch_recovery * _zoom_punch * delta, 0.0)
		if _zoom_punch < 0.001:
			_zoom_punch = 0.0
	zoom = _base_zoom * _overview_factor * (1.0 + _zoom_punch)

## Zoom zur Laufzeit ändern (Dev-Modus). Die Raumgrenzen hängen am Zoom.
func set_base_zoom(value: float) -> void:
	base_zoom = maxf(value, 0.1)
	_base_zoom = Vector2.ONE * base_zoom
	zoom = _base_zoom
	_apply_limits()

## Überblick zu Raumbeginn: kurz auf 70 % des Grundzooms, dann zurück.
func overview(duration: float) -> void:
	_overview_factor = 0.7
	var tween := create_tween()
	tween.tween_interval(duration * 0.6)
	tween.tween_property(self, "_overview_factor", 1.0, duration * 0.4).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)

## Kompatibel zum alten Aufruf: shake(4.0)
func shake(amount: float) -> void:
	add_trauma(amount * 0.1)

func add_trauma(amount: float) -> void:
	trauma = clampf(trauma + amount, 0.0, 1.0)

func punch_zoom(amount: float = 0.06) -> void:
	_zoom_punch = maxf(_zoom_punch, amount)

## Vom RoomController aufgerufen, wenn ein neuer Raum startet.
func set_room(center: Vector2, use_fixed_camera: bool, room_size: Vector2 = Vector2.ZERO) -> void:
	fixed_position = center
	mode = Mode.FIXED if use_fixed_camera else Mode.FOLLOW
	_room_center = center
	_room_size = room_size
	_apply_limits()

## Vom HUD gesetzt: so hoch ist die Steuerleiste unten.
func set_bottom_reserve(height: float) -> void:
	_bottom_reserve = maxf(height, 0.0)
	_apply_limits()

## Hält die folgende Kamera innerhalb der Raumwände. Ist der Raum kleiner als
## das Spielfeld, bleiben die Grenzen aus - sonst zappelt die Kamera.
##
## Der Kamera-Versatz (halbe Leistenhöhe) wird nach den Grenzen angewandt.
## Damit die untere Wand an der Leiste endet und nicht dahinter, werden die
## Grenzen oben und unten um genau diesen Versatz aufgeweitet.
func _apply_limits() -> void:
	var view: Vector2 = get_viewport_rect().size / maxf(_base_zoom.x, 0.01)
	view.y -= _bottom_reserve
	if _room_size.x <= view.x or _room_size.y <= view.y:
		limit_left = -10000000
		limit_right = 10000000
		limit_top = -10000000
		limit_bottom = 10000000
		return

	var half: Vector2 = _room_size * 0.5
	var shift: float = _bottom_reserve * 0.5
	limit_left = int(_room_center.x - half.x)
	limit_right = int(_room_center.x + half.x)
	limit_top = int(_room_center.y - half.y - shift)
	limit_bottom = int(_room_center.y + half.y + shift)
