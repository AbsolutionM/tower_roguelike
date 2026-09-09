extends Node

## Bündelt Touch- und Tastatur-Eingaben an einer Stelle.
## Der virtuelle Stick schreibt hier rein, der Player liest nur noch get_move_vector().

signal dash_pressed
signal ability_pressed

var stick_vector: Vector2 = Vector2.ZERO
var stick_active: bool = false

func set_stick(vec: Vector2) -> void:
	stick_vector = vec.limit_length(1.0)
	stick_active = stick_vector.length() > 0.05

func release_stick() -> void:
	stick_vector = Vector2.ZERO
	stick_active = false

func get_move_vector() -> Vector2:
	if stick_active:
		return stick_vector
	var keyboard := Vector2(
		Input.get_action_strength("move_right") - Input.get_action_strength("move_left"),
		Input.get_action_strength("move_down") - Input.get_action_strength("move_up")
	)
	return keyboard.limit_length(1.0)

func request_dash() -> void:
	dash_pressed.emit()

func request_ability() -> void:
	ability_pressed.emit()

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("dash"):
		request_dash()
	elif event.is_action_pressed("ability"):
		request_ability()
