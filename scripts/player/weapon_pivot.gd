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

func _process(delta: float) -> void:
	if current_target and is_instance_valid(current_target):
		var raw_angle := global_position.direction_to(current_target.global_position).angle()
		rotation = lerp_angle(rotation, raw_angle, rotation_speed * delta)

	update_visuals()

func update_visuals() -> void:
	var dir := Vector2.RIGHT.rotated(rotation)
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
