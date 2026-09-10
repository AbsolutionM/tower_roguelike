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

var trauma: float = 0.0
var fixed_position: Vector2 = Vector2.ZERO
var target: Node2D

var _noise: FastNoiseLite
var _noise_time: float = 0.0
var _base_zoom: Vector2 = Vector2.ONE
var _zoom_punch: float = 0.0

func _ready() -> void:
	add_to_group("camera")
	top_level = true

	_base_zoom = zoom
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
	if trauma <= 0.0:
		offset = Vector2.ZERO
		rotation = 0.0
		return

	trauma = maxf(trauma - trauma_decay * delta, 0.0)
	_noise_time += delta * 55.0

	var strength: float = trauma * trauma
	offset = Vector2(
		_noise.get_noise_2d(_noise_time, 0.0) * max_shake_offset.x,
		_noise.get_noise_2d(0.0, _noise_time) * max_shake_offset.y
	) * strength
	rotation = _noise.get_noise_2d(_noise_time, _noise_time) * max_shake_roll * strength

func _update_zoom(delta: float) -> void:
	if _zoom_punch <= 0.0:
		zoom = _base_zoom
		return
	_zoom_punch = maxf(_zoom_punch - zoom_punch_recovery * _zoom_punch * delta, 0.0)
	if _zoom_punch < 0.001:
		_zoom_punch = 0.0
	zoom = _base_zoom * (1.0 + _zoom_punch)

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
	_apply_limits(center, room_size)

## Hält die folgende Kamera innerhalb der Raumwände. Ist der Raum kleiner als
## der Bildschirm, bleiben die Grenzen aus - sonst zappelt die Kamera.
func _apply_limits(center: Vector2, room_size: Vector2) -> void:
	var view: Vector2 = get_viewport_rect().size / maxf(_base_zoom.x, 0.01)
	if room_size.x <= view.x or room_size.y <= view.y:
		limit_left = -10000000
		limit_right = 10000000
		limit_top = -10000000
		limit_bottom = 10000000
		return

	var half: Vector2 = room_size * 0.5
	limit_left = int(center.x - half.x)
	limit_right = int(center.x + half.x)
	limit_top = int(center.y - half.y)
	limit_bottom = int(center.y + half.y)
