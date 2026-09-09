extends Sprite2D
class_name OffHandController

## Die freie Hand. Sie hält keine Waffe, sieht aber genauso aus wie die
## Waffenhand und wippt im selben Takt - nur auf der anderen Körperseite.

@export var distance: float = 32.0
@export var bob_speed: float = 4.0
@export var bob_amount: float = 2.0

var base_y: float = 0.0
var time_elapsed: float = 0.0
var facing_left: bool = false

func _ready() -> void:
	base_y = position.y
	z_as_relative = false

func _process(delta: float) -> void:
	time_elapsed += delta
	var offset := sin(time_elapsed * bob_speed) * bob_amount
	# Die freie Hand liegt der Waffenhand gegenüber.
	var x := distance if facing_left else -distance
	position = Vector2(x, base_y + offset)
	# Mitspiegeln, damit beide Hände gleich herum stehen.
	flip_h = facing_left

func set_side(is_facing_left: bool) -> void:
	facing_left = is_facing_left
