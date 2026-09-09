extends Sprite2D
class_name OffHandController

## Die freie Hand. Sie sitzt auf demselben Kreis wie die Waffenhand, nur
## gegenüber, und dreht sich mit dem Zielen mit.
##
## Beim Schlag bleibt sie stehen: der Schwung läuft ausschließlich über die
## Waffenhand, und das Zielen ist währenddessen gesperrt.

@export var bob_speed: float = 4.0
@export var bob_amount: float = 1.1

## Abstand vom Körpermittelpunkt - derselbe wie bei der Waffenhand.
var base_radius: float = 20.0
## Ausgleich für nicht mittig gezeichnete Handtexturen. Siehe HandController.
var center: Vector2 = Vector2.ZERO

var time_elapsed: float = 0.0

func _ready() -> void:
	z_as_relative = false

func _process(delta: float) -> void:
	time_elapsed += delta
	var bob := sin(time_elapsed * bob_speed + PI) * bob_amount
	# Gegenüber der Waffenhand: derselbe Kreis, um 180 Grad versetzt.
	position = Vector2(-base_radius, bob) + Vector2(-center.x, center.y)

func set_radius(radius: float) -> void:
	base_radius = radius
