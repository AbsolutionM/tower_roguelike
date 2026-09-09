extends Sprite2D
class_name HandController

@export var bob_speed: float = 4.0
@export var bob_amount: float = 2.0

var base_radius: float = 20.0
var time_elapsed: float = 0.0

func _ready() -> void:
	z_as_relative = false

func _process(delta: float) -> void:
	time_elapsed += delta
	var offset := sin(time_elapsed * bob_speed) * bob_amount
	position = Vector2(base_radius, offset)

func set_radius(radius: float) -> void:
	base_radius = radius
