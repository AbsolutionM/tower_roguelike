extends Sprite2D
class_name OffHandController

## Die freie Hand. Sie sitzt auf demselben Kreis wie die Waffenhand, nur
## gegenüber, und dreht sich mit dem Zielen mit.
##
## Beim Schlag bleibt sie stehen: der Schwung läuft ausschließlich über die
## Waffenhand, und das Zielen ist währenddessen gesperrt. Beim Laufen pumpt
## sie gegenläufig zur Waffenhand (siehe `gait`).
##
## Bei beidhändigen Waffen (`grip` gesetzt) greift sie mit an den Griff: sie
## sitzt ein Stück unter der Waffenhand und führt deren Schwung mit aus.

## Abstand vom Körpermittelpunkt - derselbe wie bei der Waffenhand.
var base_radius: float = 20.0
## Ausgleich für nicht mittig gezeichnete Handtexturen. Siehe HandController.
var center: Vector2 = Vector2.ZERO
## Schrittauslenkung in Pivot-Koordinaten.
var gait: Vector2 = Vector2.ZERO
## Waffenhand, an deren Griff diese Hand mitgreift. Null = eigene Seite.
var grip: HandController = null

## Versatz der zweiten Faust am Griff, in Pivot-Pixeln: etwas näher am
## Körper und ein Stück tiefer, damit beide Fäuste als zwei lesbar bleiben.
const GRIP_OFFSET := Vector2(-6.0, 5.0)

func _ready() -> void:
	z_as_relative = false

func _process(_delta: float) -> void:
	if grip:
		# Am Griff: derselbe Kreis wie die Waffenhand, um den Griffversatz
		# verschoben, und mit dem Schlag mitgedreht.
		position = (Vector2(base_radius, 0.0) + GRIP_OFFSET).rotated(grip.swing_angle) + gait + center
		rotation = grip.swing_angle
		return
	# Gegenüber der Waffenhand: derselbe Kreis, um 180 Grad versetzt.
	position = Vector2(-base_radius, 0.0) + gait + Vector2(-center.x, center.y)
	rotation = 0.0

func set_radius(radius: float) -> void:
	base_radius = radius
