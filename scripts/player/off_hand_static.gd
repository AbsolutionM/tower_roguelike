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
##
## Sie ist bewusst kein Kind des Pivots, sondern ein Geschwister des Körpers
## im Rig: alles im Rig teilt sich einen z-Index (sonst fällt es aus dem
## gemeinsamen Umriss), also entscheidet die Reihenfolge im Baum, was vor
## dem Körper liegt. Ihre Lage ist das Spiegelbild der Waffenhand an der
## Körperachse, siehe _process.

## Der Kreis, auf dem sie sitzt.
@export var pivot: Node2D

## Abstand vom Körpermittelpunkt - derselbe wie bei der Waffenhand.
var base_radius: float = 20.0
## Ausgleich für nicht mittig gezeichnete Handtexturen. Siehe HandController.
var center: Vector2 = Vector2.ZERO
## Schrittauslenkung in Pivot-Koordinaten.
var gait: Vector2 = Vector2.ZERO
## Pendelwinkel des Schritts, siehe HandController. Da diese Hand gegenüber
## sitzt, schwingt sie mit demselben Winkel automatisch zur anderen Seite.
var gait_angle: float = 0.0
## Waffenhand, an deren Griff diese Hand mitgreift. Null = eigene Seite.
var grip: HandController = null

## Versatz der zweiten Faust am Griff, in Pivot-Pixeln: etwas näher am
## Körper und ein Stück tiefer, damit beide Fäuste als zwei lesbar bleiben.
const GRIP_OFFSET := Vector2(-6.0, 5.0)
## Die freie Hand hängt nicht auf Gürtelhöhe wie die Waffenhand, sondern
## vier Figurpixel höher - in Weltrichtung, unabhängig vom Zielen.
const RAISE := 12.0

func _process(_delta: float) -> void:
	if not pivot:
		return

	if grip:
		# Am Griff: derselbe Kreis wie die Waffenhand, um den Griffversatz
		# verschoben, und mit dem Schlag mitgedreht.
		var local_position: Vector2 = (Vector2(base_radius, 0.0) + GRIP_OFFSET).rotated(grip.swing_angle + gait_angle) + gait + center
		var mirrored: bool = pivot.scale.y < 0.0
		global_position = pivot.to_global(local_position)
		global_rotation = pivot.global_rotation + (-grip.swing_angle if mirrored else grip.swing_angle)
		flip_h = false
		flip_v = mirrored
		return

	# Sonst das Spiegelbild der Waffenhand an der Körperachse: ist die Waffe
	# rechts, ist diese Hand links - und wandert die Waffenhand über die
	# Achse, wechselt sie mit. Ohne den Schlag: der Schwung bleibt bei der
	# Waffenhand, diese steht. Vier Figurpixel höher als die Waffenhand.
	var rest: Vector2 = Vector2(base_radius, 0.0).rotated(gait_angle) + gait
	var hand_world: Vector2 = pivot.to_global(rest)
	var axis_x: float = pivot.global_position.x
	global_position = Vector2(2.0 * axis_x - hand_world.x, hand_world.y - RAISE) + Vector2(-center.x, center.y)
	global_rotation = 0.0
	flip_h = true
	flip_v = false

func set_radius(radius: float) -> void:
	base_radius = radius
