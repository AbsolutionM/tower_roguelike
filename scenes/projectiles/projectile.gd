extends Area2D
class_name Projectile

## Leuchtendes Geschoss mit Trail und eigenem Licht.
## Sieht ohne Sprite gut aus - sobald `texture` gesetzt ist, wird der Sprite benutzt.

const LIGHT_TEXTURE := preload("res://resources/materials/light_gradient.tres")

@export var texture: Texture2D
@export var color: Color = Color(1.0, 0.85, 0.4)
@export var bullet_length: float = 18.0
@export var bullet_width: float = 7.0
@export var trail_length: int = 14
@export var trail_width: float = 8.0
@export var lifetime: float = 2.5
@export var hostile: bool = false
@export var light_energy: float = 1.1
@export var light_scale: float = 0.4

var direction: Vector2 = Vector2.RIGHT
var speed: float = 400.0
var damage: float = 10.0
var pierce_remaining: int = 0
var is_crit: bool = false
var hit_targets: Array = []

var _trail: Line2D
var _visual: Node2D
var _glow: Polygon2D
var _body: Polygon2D
var _light: PointLight2D
var _elapsed: float = 0.0
var _dead: bool = false

func _ready() -> void:
	add_to_group("projectiles")
	z_index = 40
	z_as_relative = false
	area_entered.connect(_on_area_entered)
	body_entered.connect(_on_body_entered)
	_build_visuals()

## Wird nach dem Einhängen in die Szene aufgerufen.
func setup(dir: Vector2, spd: float, dmg: float, pierce: int, tint: Color = Color(0.0, 0.0, 0.0, 0.0), crit: bool = false) -> void:
	direction = dir.normalized()
	speed = spd
	damage = dmg
	pierce_remaining = pierce
	is_crit = crit
	if tint.a > 0.0:
		color = tint
	rotation = direction.angle()
	_refresh_colors()

func _build_visuals() -> void:
	var additive := CanvasItemMaterial.new()
	additive.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD

	_trail = Line2D.new()
	_trail.top_level = true
	_trail.width = trail_width
	_trail.z_index = 38
	_trail.z_as_relative = false
	# Eckige Enden ohne Kantenglättung, damit der Trail pixelig bleibt.
	_trail.joint_mode = Line2D.LINE_JOINT_SHARP
	_trail.begin_cap_mode = Line2D.LINE_CAP_BOX
	_trail.end_cap_mode = Line2D.LINE_CAP_BOX
	_trail.antialiased = false
	_trail.material = additive
	_trail.gradient = Gradient.new()

	var width_curve := Curve.new()
	width_curve.add_point(Vector2(0.0, 0.1))
	width_curve.add_point(Vector2(1.0, 1.0))
	_trail.width_curve = width_curve
	add_child(_trail)

	_visual = Node2D.new()
	add_child(_visual)

	if texture:
		var sprite := Sprite2D.new()
		sprite.texture = texture
		_visual.add_child(sprite)
	else:
		_glow = Polygon2D.new()
		_glow.polygon = _bullet_shape(bullet_length * 1.7, bullet_width * 2.1)
		_glow.material = additive
		_visual.add_child(_glow)

		_body = Polygon2D.new()
		_body.polygon = _bullet_shape(bullet_length, bullet_width)
		_body.material = additive
		_visual.add_child(_body)

		var core := Polygon2D.new()
		core.polygon = _bullet_shape(bullet_length * 0.6, bullet_width * 0.45)
		core.color = Color(1.0, 1.0, 1.0, 0.95)
		core.material = additive
		_visual.add_child(core)

	_light = PointLight2D.new()
	_light.texture = LIGHT_TEXTURE
	_light.blend_mode = Light2D.BLEND_MODE_ADD
	_light.energy = light_energy
	_light.texture_scale = light_scale
	add_child(_light)

	_refresh_colors()

	_visual.scale = Vector2(0.4, 1.4)
	var tween := _visual.create_tween()
	tween.tween_property(_visual, "scale", Vector2.ONE, 0.09).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)

func _refresh_colors() -> void:
	if _glow:
		_glow.color = Color(color, 0.35)
	if _body:
		_body.color = color
	if _light:
		_light.color = color
	if _trail and _trail.gradient:
		_trail.gradient.set_color(0, Color(color, 0.0))
		_trail.gradient.set_color(1, Color(color, 0.7))

## Rechteckiger Leuchtkörper auf dem Pixelraster statt einer runden Kapsel.
func _bullet_shape(length: float, width: float) -> PackedVector2Array:
	var pixel: float = FX.pixel_size()
	var half_length: float = maxf(roundf(length * 0.5 / pixel), 1.0) * pixel
	var half_width: float = maxf(roundf(width * 0.5 / pixel), 1.0) * pixel
	return PackedVector2Array([
		Vector2(half_length, -half_width),
		Vector2(half_length, half_width),
		Vector2(-half_length, half_width),
		Vector2(-half_length, -half_width)
	])

func _physics_process(delta: float) -> void:
	if _dead:
		return

	global_position += direction * speed * delta
	_update_trail()

	_elapsed += delta
	if _elapsed >= lifetime:
		_expire()

func _update_trail() -> void:
	if not _trail:
		return
	_trail.add_point(global_position)
	while _trail.get_point_count() > trail_length:
		_trail.remove_point(0)

func _on_area_entered(area: Area2D) -> void:
	if _dead or hostile or area in hit_targets:
		return
	if not area.is_in_group("damageable"):
		return
	hit_targets.append(area)
	_damage_target(area)
	_register_hit(area.global_position)

func _on_body_entered(body: Node) -> void:
	if _dead:
		return

	# Felsen fangen jeden Schuss ab - egal von welcher Seite.
	if body.is_in_group("obstacles"):
		FX.impact(global_position, direction, color, 0.5)
		_expire()
		return

	if not hostile or body in hit_targets:
		return
	if not body.is_in_group("player"):
		return
	hit_targets.append(body)
	var health = body.get_node_or_null("PlayerHealth")
	if health and health.has_method("take_damage"):
		health.take_damage(damage, global_position)
	_register_hit(body.global_position)

func _damage_target(target: Node) -> void:
	if not target.has_method("take_damage"):
		return

	var stats = get_tree().get_first_node_in_group("player_stats")
	if stats:
		stats.report_damage(damage)

	if target is Enemy:
		target.take_damage(damage, global_position, is_crit)
		if target.has_method("apply_knockback"):
			target.apply_knockback(direction, 140.0)
	else:
		target.take_damage(damage)

func _register_hit(hit_position: Vector2) -> void:
	FX.impact(hit_position, direction, color, 0.8)
	FX.shake(1.5)

	if pierce_remaining <= 0:
		_expire()
	else:
		pierce_remaining -= 1

func _expire() -> void:
	if _dead:
		return
	_dead = true
	set_deferred("monitoring", false)
	_release_trail()

	if _visual:
		var tween := _visual.create_tween()
		tween.set_parallel(true)
		tween.tween_property(_visual, "scale", Vector2(1.6, 0.2), 0.09)
		tween.tween_property(_visual, "modulate:a", 0.0, 0.09)
		if _light:
			tween.tween_property(_light, "energy", 0.0, 0.09)
		tween.chain().tween_callback(queue_free)
	else:
		queue_free()

func _release_trail() -> void:
	if not _trail:
		return
	var host := get_tree().current_scene
	var trail := _trail
	_trail = null
	if not host:
		trail.queue_free()
		return
	trail.reparent(host)
	var tween := trail.create_tween()
	tween.tween_property(trail, "modulate:a", 0.0, 0.22)
	tween.tween_callback(trail.queue_free)
