extends Sprite2D
class_name HandController

## Die Hand, die die Waffe hält. Sitzt auf `base_radius` vom Körpermittelpunkt
## und wird beim Schlag mitgeführt - die Klinge allein zu drehen sieht aus,
## als läge sie auf einem Drehteller.

@export var bob_speed: float = 4.0
## Klein halten: eine angesetzte Hand wippt kaum, eine schwebende fällt auf.
@export var bob_amount: float = 1.1

var base_radius: float = 20.0
## Ausgleich für Handtexturen, die nicht mittig gezeichnet sind.
## Bewusst als Position und nicht als `offset`: `flip_h` spiegelt den offset
## mit, wodurch eine gespiegelte Hand um den doppelten Betrag wegspringt.
var center: Vector2 = Vector2.ZERO
## Höhe am Körper. Wird aus dem Sprite gemessen, nicht geraten.
var base_y: float = 0.0
## Auslenkung des Schlags. Der Schwung führt die Hand über denselben Bogen,
## nur über einen kleineren Winkel als die Klinge.
var swing_angle: float = 0.0

var time_elapsed: float = 0.0

func _ready() -> void:
	z_as_relative = false

func _process(delta: float) -> void:
	time_elapsed += delta
	var offset := sin(time_elapsed * bob_speed) * bob_amount
	position = (Vector2(base_radius, base_y + offset) + center).rotated(swing_angle)
	# Das Handgelenk dreht mit - sonst wirkt der Arm steif.
	rotation = swing_angle

func set_radius(radius: float) -> void:
	base_radius = radius
