extends Node2D
class_name WeaponPivot

## Der Kreis, auf dem beide Hände sitzen.
##
## Der Knoten liegt im Körpermittelpunkt und dreht sich zum Ziel. Die
## Waffenhand sitzt bei +Radius, die freie Hand gegenüber bei -Radius; damit
## kreisen beide um die Figur, ohne dass jemand sie einzeln setzen muss.
##
## Während eines Schlags bleibt die Drehung stehen. Sonst würde die Figur
## mitten im Schwung nachzielen und der Bogen bräche ab.

@export var rotation_speed: float = 12.0
## Radius, auf dem die Fäuste kreisen: Körperbreite plus Vorstrecken der
## Waffe. Wird jeden Frame aus `body_radius` und `extra_radius` gebildet.
var pivot_radius: float = 10.0
## Anteil aus der Körperbreite, vom Spieler gesetzt.
var body_radius: float = 10.0
## Anteil aus der Waffe (hand_reach_texels), vom WeaponController gesetzt.
var extra_radius: float = 0.0
@export var hand: HandController
@export var off_hand: OffHandController
@export var sword: SwordWeapon
## Der Körper, vor oder hinter den Hände und Waffe sortiert werden.
@export var body: Node2D
## Der Spieler in der Welt. Das Rig lebt in der RigView in seinem Ursprung;
## zum Zielen braucht der Kreis seine Weltposition.
@export var anchor: Node2D
## Das Sprite, das die Ansicht in der Welt zeigt. Die Klinge liegt als echtes
## Sprite davor oder dahinter, je nach Blickrichtung.
@export var display: Node2D

## Richtung, in die der Kreis zeigt - die Laufrichtung des Helden. Der
## WeaponController setzt sie jeden Frame; gezielt wird nicht auf Gegner.
var aim_direction: Vector2 = Vector2.DOWN

## Beidhändige Waffe: die freie Hand greift mit an den Griff.
var two_handed: bool = false

## Ruhelage des Kreises. Der Spieler setzt sie auf den Körpermittelpunkt;
## der Rückstoß kehrt hierher zurück statt auf den Szenenwert.
var rest_position: Vector2 = Vector2.ZERO

## Richtung zum Ziel. Blickrichtung und Spiegelung hängen hieran, nicht an
## `rotation` - sonst kippt die Figur mitten im Schlag auf die andere Seite.
var aim_rotation: float = 0.0

func _process(delta: float) -> void:
	if not is_swinging() and aim_direction.length_squared() > 0.001:
		aim_rotation = lerp_angle(aim_rotation, aim_direction.angle(), rotation_speed * delta)

	rotation = aim_rotation
	pivot_radius = body_radius + extra_radius
	update_visuals()

## Während der Schlag läuft, ist das Zielen gesperrt.
func is_swinging() -> bool:
	return sword != null and sword.is_swinging

## Schrittauslenkung beider Hände, in Weltrichtung angegeben. Der Kreis dreht
## und spiegelt sich zum Ziel - hier wird das herausgerechnet, damit die Arme
## in Laufrichtung pumpen und nicht in Zielrichtung.
func set_gait(hand_world: Vector2, off_hand_world: Vector2, angle: float = 0.0) -> void:
	if hand:
		hand.gait = global_transform.basis_xform_inv(hand_world)
		hand.gait_angle = angle
	if off_hand:
		off_hand.gait = global_transform.basis_xform_inv(off_hand_world)
		off_hand.gait_angle = angle

func update_visuals() -> void:
	var dir := Vector2.RIGHT.rotated(aim_rotation)
	var facing_left := dir.x < 0
	var facing_up := dir.y < -0.5

	# Ohne diese Spiegelung stünde die Waffe beim Zielen nach links auf dem Kopf.
	scale.y = -1.0 if facing_left else 1.0

	if hand:
		hand.set_radius(pivot_radius)
	if off_hand:
		off_hand.set_radius(pivot_radius)
		off_hand.grip = hand if two_handed else null
	_order_rig(facing_up)

## Alles im Rig teilt sich einen z-Index, damit der Umriss um die gemeinsame
## Silhouette läuft. Vorn und hinten entscheidet deshalb die Reihenfolge der
## Kinder: der Pivot (Waffenhand samt Klinge) liegt beim Zielen nach oben
## hinter dem Körper, sonst davor. Die freie Hand liegt gegenüber - oder,
## beidhändig, direkt unter der Waffenhand auf derselben Seite.
func _order_rig(facing_up: bool) -> void:
	var rig := get_parent()
	if not rig or not body or not off_hand or body.get_parent() != rig or off_hand.get_parent() != rig:
		return
	var order: Array
	if two_handed:
		order = [off_hand, self, body] if facing_up else [body, off_hand, self]
	else:
		order = [self, body, off_hand] if facing_up else [off_hand, body, self]
	for index in order.size():
		if rig.get_child(index) != order[index]:
			rig.move_child(order[index], index)

	# Die Klinge ist ein echtes Sprite in der Welt (Kind der Trefferbox), kein
	# Teil der Ansicht: beim Zielen nach oben hinter das Figurbild, sonst davor.
	# move_child zieht den Knoten erst heraus, dann rueckt der Rest nach -
	# darum in beiden Faellen der Index des Figurbilds als Ziel: von hinten
	# davor gesetzt landet die Klinge davor, von vorn dahinter gesetzt dahinter.
	if sword and display and sword.get_parent() == display.get_parent():
		var carrier := display.get_parent()
		var behind: bool = sword.get_index() < display.get_index()
		if facing_up != behind:
			carrier.move_child(sword, display.get_index())
