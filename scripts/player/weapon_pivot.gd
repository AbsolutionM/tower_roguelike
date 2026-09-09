extends Node2D
class_name WeaponPivot

## Dreht Hand und Waffe zum Ziel. Das Ziel bestimmt der WeaponController -
## so zeigt der Arm immer auf genau den Gegner, der auch getroffen wird.

@export var rotation_speed: float = 12.0
@export var pivot_radius: float = 10.0
@export var pivot_radius_up: float = -30.0
@export var hand: HandController
@export var off_hand: OffHandController
@export var sword: SwordWeapon

var current_target: Node2D = null

## Richtung zum Ziel. Getrennt vom tatsächlichen `rotation`, weil da der
## Schwung obendrauf kommt.
var aim_rotation: float = 0.0
## Auslenkung des Schlags. Der Schwung dreht den ganzen Arm, damit die Hand
## die Waffe führt, statt dass die Waffe um die Hand kreist.
var swing_offset: float = 0.0

func _process(delta: float) -> void:
	if current_target and is_instance_valid(current_target):
		var raw_angle := global_position.direction_to(current_target.global_position).angle()
		aim_rotation = lerp_angle(aim_rotation, raw_angle, rotation_speed * delta)

	rotation = aim_rotation + swing_offset
	update_visuals()

func update_visuals() -> void:
	# Für Blickrichtung und Spiegelung zählt das Ziel, nicht der Schwung -
	# sonst kippt die Figur mitten im Schlag auf die andere Seite.
	var dir := Vector2.RIGHT.rotated(aim_rotation)
	var facing_left := dir.x < 0
	var facing_up := dir.y < -0.5

	scale.y = -1.0 if facing_left else 1.0

	var radius := pivot_radius_up if facing_up else pivot_radius

	if hand:
		hand.set_radius(radius)
		hand.z_index = -5 if facing_up else 5

	if off_hand:
		off_hand.set_side(facing_left)

	if sword:
		sword.z_index = -5 if facing_up else 5
