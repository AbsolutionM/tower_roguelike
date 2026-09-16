extends Area2D
class_name SwordWeapon

@export var swing_duration: float = 0.15
@export var swing_angle_degrees: float = 90.0
@export var return_duration: float = 0.1
## Die Hand, die die Klinge führt - sie lebt in der RigView, diese Trefferbox
## in der Welt. Die Box folgt der Hand jeden Frame.
@export var hand: HandController
@export var sprite: Sprite2D
@export var arc: Polygon2D
## Versatz der Klinge in der Faust, in Hand-Koordinaten.
@export var grip_offset: Vector2 = Vector2(1.365, 0.0)
@export var arc_inner_radius: float = 8.0
@export var arc_outer_radius: float = 34.0
@export var trail_interval: float = 0.028
@export var trail_alpha_step: float = 0.1
@export var hit_sound: AudioStreamPlayer
@export var hitstop_duration: float = 0.06
@export var hitstop_scale: float = 0.05

## Richtung der Trefferbox, einmal aus der Szene übernommen.
var _hitbox_direction: Vector2 = Vector2.ZERO

## Weitester Ausschlag der Hand zu jeder Seite. Ein Bogen über den halben
## Körper herum sah mit langen Klingen wie ein Windrad aus.
const MAX_SWEEP := deg_to_rad(55.0)
## Wie weit die Klinge am Ende des Schlags dem Arm vorausläuft.
const LEAD := 1.15

## Neigung der Klinge gegenüber der Ruhehaltung, vom Schwung getrieben.
var swing_lean: float = 0.0
## Nur während des eigentlichen Schlags: Treffer und Klingenspur.
var _striking: bool = false

var damage: float = 0.0
var is_crit: bool = false
var hit_enemies: Array = []
var is_swinging: bool = false
var trail_timer: float = 0.0
var trail_count: int = 0

func _ready() -> void:
	monitoring = false
	if arc:
		build_arc()
		arc.modulate.a = 0.0
	_follow_hand()

## Die Faust liegt in der RigView im Spielerursprung, diese Box ist ein Kind
## des Spielers - die Koordinaten passen also direkt zusammen.
func _follow_hand() -> void:
	if hand:
		transform = hand.global_transform * Transform2D(0.0, grip_offset)

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
	_follow_hand()
	if _striking:
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
	# Das Sprite lebt in der RigView - in die Welt umrechnen.
	var view := sprite.get_viewport() as RigView
	ghost.global_transform = view.to_world(sprite.get_global_transform()) if view else sprite.get_global_transform()
	ghost.modulate = Color(1, 1, 1, clamp(trail_count * trail_alpha_step, 0.0, 0.45))
	ghost.z_index = z_index
	get_tree().current_scene.add_child(ghost)

	var t := create_tween()
	t.tween_property(ghost, "modulate:a", 0.0, 0.25)
	t.tween_callback(ghost.queue_free)

## Ausholen, Schlag, Rückkehr. Die Hand fährt den Bogen, die Klinge kippt
## dabei voraus (`swing_lean`, siehe WeaponController._update_hold_orientation)
## - so liest sich der Hieb als Schnitt statt als starre Drehung.
func perform_swing(dmg: float, crit: bool = false) -> void:
	Audio.play(Audio.ID_SWING)
	damage = dmg
	is_crit = crit
	hit_enemies.clear()
	is_swinging = true
	trail_timer = 0.0
	trail_count = 0

	if not hand:
		return

	var sweep: float = minf(deg_to_rad(swing_angle_degrees * 0.5), MAX_SWEEP)
	var windup: float = swing_duration * 0.6

	if arc:
		arc.modulate.a = 0.0
		var arc_tween := create_tween()
		arc_tween.tween_interval(windup)
		arc_tween.tween_property(arc, "modulate:a", 0.5, swing_duration * 0.3)
		arc_tween.tween_property(arc, "modulate:a", 0.0, swing_duration * 0.7)

	var tween := create_tween()
	# Ausholen: die Hand ein Stück zurück, die Klinge kippt leicht nach hinten.
	tween.tween_property(hand, "swing_angle", -sweep * 0.55, windup).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(self, "swing_lean", -0.3, windup).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	# Schlag: schnell nach vorn, die Klinge läuft dem Arm voraus. Erst hier trifft sie.
	tween.tween_callback(_begin_strike)
	tween.tween_property(hand, "swing_angle", sweep, swing_duration).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(self, "swing_lean", LEAD, swing_duration).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tween.tween_callback(end_swing)
	# Zurück in die Ruhelage.
	tween.tween_property(hand, "swing_angle", 0.0, return_duration).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.parallel().tween_property(self, "swing_lean", 0.0, return_duration).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)

func _begin_strike() -> void:
	monitoring = true
	_striking = true

func end_swing() -> void:
	monitoring = false
	_striking = false
	is_swinging = false

func _on_area_entered(area: Area2D) -> void:
	try_hit(area)
