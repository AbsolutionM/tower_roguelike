extends Sprite2D
class_name HandController

## Die Hand, die die Waffe hält.
##
## Sie sitzt auf einem Kreis um den Körpermittelpunkt. Den Kreis dreht der
## WeaponPivot zum Ziel; beim Schlag dreht sich die Hand zusätzlich innerhalb
## des Kreises - dadurch führt sie den Bogen aus, während die freie Hand steht.
##
## Beim Laufen pumpt sie mit dem Schritt (siehe `gait`). Die Auslenkung kommt
## vom Spieler, der die Schrittphase aus der Geh-Animation kennt.

## Abstand vom Körpermittelpunkt.
var base_radius: float = 20.0
## Ausgleich für Handtexturen, die nicht mittig gezeichnet sind.
## Bewusst als Position und nicht als `offset`: `flip_h` spiegelt den offset
## mit, wodurch eine gespiegelte Hand um den doppelten Betrag wegspringt.
var center: Vector2 = Vector2.ZERO
## Auslenkung des Schlags. Trägt die Hand samt Waffe durch den Bogen.
var swing_angle: float = 0.0
## Schrittauslenkung in Pivot-Koordinaten. Liegt außerhalb der Schlagdrehung,
## damit der Bogen nicht mit dem Schritt eiert.
var gait: Vector2 = Vector2.ZERO

func _ready() -> void:
	z_as_relative = false

func _process(_delta: float) -> void:
	position = Vector2(base_radius, 0.0).rotated(swing_angle) + gait + center
	# Das Handgelenk dreht mit, damit die Waffe den Bogen mitnimmt und
	# der Griff dabei in der Hand bleibt.
	rotation = swing_angle

func set_radius(radius: float) -> void:
	base_radius = radius
