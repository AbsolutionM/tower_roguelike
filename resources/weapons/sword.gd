extends Area2D
class_name SwordWeapon

@export var swing_duration: float = 0.15
@export var swing_angle_degrees: float = 90.0
@export var return_duration: float = 0.1
@export var sprite: Sprite2D
@export var arc: Polygon2D
@export var arc_inner_radius: float = 8.0
@export var arc_outer_radius: float = 34.0
@export var trail_interval: float = 0.015
@export var trail_alpha_step: float = 0.1
@export var hit_sound: AudioStreamPlayer
@export var hitstop_duration: float = 0.06
@export var hitstop_scale: float = 0.05

## Richtung der Trefferbox, einmal aus der Szene übernommen.
var _hitbox_direction: Vector2 = Vector2.ZERO

var damage: float = 0.0
var is_crit: bool = false
var hit_enemies: Array = []
var is_swinging: bool = false
var trail_timer: float = 0.0
var trail_count: int = 0

func _ready() -> void:
	monitoring = false
	rotation = 0.0
	z_as_relative = false
	if arc:
		build_arc()
		arc.modulate.a = 0.0

## Wird vom WeaponController gesetzt, damit Waffenklassen sich unterschiedlich anfühlen.
func configure(duration: float, angle_degrees: float, knockback: float, reach: float = 0.0) -> void:
	swing_duration = duration
	swing_angle_degrees = angle_degrees
	knockback_force = knockback
	if reach > 0.0:
		_resize_hitbox(reach)
	if arc:
		build_arc()

## Die Trefferbox steckte fest in der Szene, die Zielreichweite kommt aber aus
## den Waffendaten. Ein Speer zielte dadurch weiter, als er trifft.
func _resize_hitbox(reach: float) -> void:
	var collision := get_node_or_null("CollisionShape2D") as CollisionShape2D
	if not collision or not (collision.shape is RectangleShape2D):
		return

	# Von Weltpixeln in die lokalen Einheiten der Klinge zurückrechnen.
	var factor: float = absf(global_scale.x)
	if factor <= 0.001:
		return

	if not _hitbox_direction:
		_hitbox_direction = collision.position.normalized()
		if _hitbox_direction == Vector2.ZERO:
			_hitbox_direction = Vector2.RIGHT

	var length: float = reach / factor
	var rect: RectangleShape2D = collision.shape
	rect.size.y = length
	collision.position = _hitbox_direction * length * 0.5

func build_arc() -> void:
	var half_angle := deg_to_rad(swing_angle_degrees / 2)
	var segments := 16
	var points := PackedVector2Array()
	var colors := PackedColorArray()

	for i in range(segments + 1):
		var t := -half_angle + (2.0 * half_angle) * (i / float(segments))
		points.append(Vector2(arc_outer_radius, 0).rotated(t))
		colors.append(Color(1, 1, 1, float(i) / float(segments)))

	for i in range(segments, -1, -1):
		var t := -half_angle + (2.0 * half_angle) * (i / float(segments))
		points.append(Vector2(arc_inner_radius, 0).rotated(t))
		colors.append(Color(1, 1, 1, float(i) / float(segments)))

	arc.polygon = points
	arc.vertex_colors = colors

func _process(delta: float) -> void:
	if is_swinging:
		check_hits()

		trail_timer -= delta
		if trail_timer <= 0.0:
			spawn_trail()
			trail_timer = trail_interval

func check_hits() -> void:
	for area in get_overlapping_areas():
		try_hit(area)

@export var knockback_force: float = 180.0
@export var shake_amount: float = 4.0

func try_hit(area: Area2D) -> void:
	if not area.is_in_group("damageable") or area in hit_enemies:
		return

	hit_enemies.append(area)
	var knock_dir: Vector2 = (area.global_position - global_position).normalized()

	if area is Enemy:
		area.take_damage(damage, global_position, is_crit)
	elif area.has_method("take_damage"):
		area.take_damage(damage)

	if area.has_method("apply_knockback"):
		area.apply_knockback(knock_dir, knockback_force)

	Audio.play(Audio.ID_ENEMY_HIT)

	var stats = get_tree().get_first_node_in_group("player_stats")
	if stats:
		stats.report_damage(damage)
		stats.report_hit()

	FX.shake(shake_amount * (1.6 if is_crit else 1.0))

	if hit_sound:
		hit_sound.play()

	HitStop.trigger(hitstop_duration * (1.6 if is_crit else 1.0), hitstop_scale)

func spawn_trail() -> void:
	if not sprite or not sprite.texture:
		return
	trail_count += 1

	var ghost := Sprite2D.new()
	ghost.texture = sprite.texture
	ghost.flip_h = sprite.flip_h
	ghost.flip_v = sprite.flip_v
	ghost.global_transform = sprite.get_global_transform()
	ghost.modulate = Color(1, 1, 1, clamp(trail_count * trail_alpha_step, 0.0, 1.0))
	ghost.z_index = z_index
	get_tree().current_scene.add_child(ghost)

	var t := create_tween()
	t.tween_property(ghost, "modulate:a", 0.0, 0.25)
	t.tween_callback(ghost.queue_free)

func perform_swing(dmg: float, crit: bool = false) -> void:
	Audio.play(Audio.ID_SWING)
	damage = dmg
	is_crit = crit
	hit_enemies.clear()
	monitoring = true
	is_swinging = true
	trail_timer = 0.0
	trail_count = 0

	if arc:
		arc.modulate.a = 0.6
		var arc_tween := create_tween()
		arc_tween.tween_property(arc, "modulate:a", 0.0, swing_duration)

	# Den Bogen fährt die Hand. Die Klinge selbst dreht sich nicht mehr um
	# ihren eigenen Punkt - nur so bleibt der Griff in der Faust.
	var half_angle := deg_to_rad(swing_angle_degrees / 2)
	var hand := get_parent() as HandController
	rotation = 0.0

	if not hand:
		return

	hand.swing_angle = -half_angle
	var tween := create_tween()
	tween.tween_property(hand, "swing_angle", half_angle, swing_duration)
	tween.tween_callback(end_swing)
	tween.tween_property(hand, "swing_angle", 0.0, return_duration)

func end_swing() -> void:
	monitoring = false
	is_swinging = false

func _on_area_entered(area: Area2D) -> void:
	try_hit(area)
