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
@export var pivot_radius: float = 10.0
@export var hand: HandController
@export var off_hand: OffHandController
@export var sword: SwordWeapon

var current_target: Node2D = null

## Ruhelage des Kreises. Der Spieler setzt sie auf den Körpermittelpunkt;
## der Rückstoß kehrt hierher zurück statt auf den Szenenwert.
var rest_position: Vector2 = Vector2.ZERO

## Richtung zum Ziel. Blickrichtung und Spiegelung hängen hieran, nicht an
## `rotation` - sonst kippt die Figur mitten im Schlag auf die andere Seite.
var aim_rotation: float = 0.0

func _process(delta: float) -> void:
	if not is_swinging() and current_target and is_instance_valid(current_target):
		var raw_angle := global_position.direction_to(current_target.global_position).angle()
		aim_rotation = lerp_angle(aim_rotation, raw_angle, rotation_speed * delta)

	rotation = aim_rotation
	update_visuals()

## Während der Schlag läuft, ist das Zielen gesperrt.
func is_swinging() -> bool:
	return sword != null and sword.is_swinging

## Schrittauslenkung beider Hände, in Weltrichtung angegeben. Der Kreis dreht
## und spiegelt sich zum Ziel - hier wird das herausgerechnet, damit die Arme
## in Laufrichtung pumpen und nicht in Zielrichtung.
func set_gait(hand_world: Vector2, off_hand_world: Vector2) -> void:
	if hand:
		hand.gait = global_transform.basis_xform_inv(hand_world)
	if off_hand:
		off_hand.gait = global_transform.basis_xform_inv(off_hand_world)

func update_visuals() -> void:
	var dir := Vector2.RIGHT.rotated(aim_rotation)
	var facing_left := dir.x < 0
	var facing_up := dir.y < -0.5

	# Ohne diese Spiegelung stünde die Waffe beim Zielen nach links auf dem Kopf.
	scale.y = -1.0 if facing_left else 1.0

	if hand:
		hand.set_radius(pivot_radius)
		hand.z_index = -2 if facing_up else 2
	if off_hand:
		off_hand.set_radius(pivot_radius)
		# Die freie Hand liegt gegenüber - beim Zielen nach oben also vorn.
		off_hand.z_index = 2 if facing_up else -2

	# Die Waffe liegt vor der Hand, sonst verdeckt die Faust den Griff.
	if sword:
		sword.z_index = -3 if facing_up else 3
