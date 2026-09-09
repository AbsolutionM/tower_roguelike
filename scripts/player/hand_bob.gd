extends Sprite2D
class_name HandController

## Die Hand, die die Waffe hält.
##
## Sie sitzt auf einem Kreis um den Körpermittelpunkt. Den Kreis dreht der
## WeaponPivot zum Ziel; beim Schlag dreht sich die Hand zusätzlich innerhalb
## des Kreises - dadurch führt sie den Bogen aus, während die freie Hand steht.

@export var bob_speed: float = 4.0
## Klein halten: eine angesetzte Hand wippt kaum, eine schwebende fällt auf.
@export var bob_amount: float = 1.1

## Abstand vom Körpermittelpunkt.
var base_radius: float = 20.0
## Ausgleich für Handtexturen, die nicht mittig gezeichnet sind.
## Bewusst als Position und nicht als `offset`: `flip_h` spiegelt den offset
## mit, wodurch eine gespiegelte Hand um den doppelten Betrag wegspringt.
var center: Vector2 = Vector2.ZERO
## Auslenkung des Schlags. Trägt die Hand samt Waffe durch den Bogen.
var swing_angle: float = 0.0

var time_elapsed: float = 0.0

func _ready() -> void:
	z_as_relative = false

func _process(delta: float) -> void:
	time_elapsed += delta
	var bob := sin(time_elapsed * bob_speed) * bob_amount
	position = Vector2(base_radius, bob).rotated(swing_angle) + center
	# Das Handgelenk dreht mit, damit die Waffe den Bogen mitnimmt und
	# der Griff dabei in der Hand bleibt.
	rotation = swing_angle

func set_radius(radius: float) -> void:
	base_radius = radius
