extends Sprite2D
class_name OffHandController

## Die freie Hand. Sie sitzt auf demselben Kreis wie die Waffenhand, nur
## gegenüber, und dreht sich mit dem Zielen mit.
##
## Beim Schlag bleibt sie stehen: der Schwung läuft ausschließlich über die
## Waffenhand, und das Zielen ist währenddessen gesperrt. Beim Laufen pumpt
## sie gegenläufig zur Waffenhand (siehe `gait`).

## Abstand vom Körpermittelpunkt - derselbe wie bei der Waffenhand.
var base_radius: float = 20.0
## Ausgleich für nicht mittig gezeichnete Handtexturen. Siehe HandController.
var center: Vector2 = Vector2.ZERO
## Schrittauslenkung in Pivot-Koordinaten.
var gait: Vector2 = Vector2.ZERO

func _ready() -> void:
	z_as_relative = false

func _process(_delta: float) -> void:
	# Gegenüber der Waffenhand: derselbe Kreis, um 180 Grad versetzt.
	position = Vector2(-base_radius, 0.0) + gait + Vector2(-center.x, center.y)

func set_radius(radius: float) -> void:
	base_radius = radius
