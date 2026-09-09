extends Node2D
class_name WeaponController

## Sucht das Ziel, dreht die Waffe dorthin und schlägt zu.
## Das Ziel wird jede Sekunde neu bestimmt - auch während der Abklingzeit,
## damit man vor dem Schlag sieht, wen es trifft.

signal target_changed(target: Node2D)

## Der gezeichnete Platzhalter rechnet in ganzen Pixeln - dieser Faktor bringt
## ihn auf dieselbe Größe wie ein echtes Haltesprite.
const PLACEHOLDER_SCALE := 0.55

@export var equipped_weapon: WeaponData
@export var sword: Node
@export var weapon_pivot: Node2D
@export var show_target_marker: bool = true

var fire_timer: float = 0.0
var current_target: Node2D = null

var _stats: PlayerStats
var _pivot_base_position: Vector2 = Vector2.ZERO
var _visualized_weapon: WeaponData
var _hold_sprite_base_scale: Vector2 = Vector2.ONE
var _hold_sprite_base_rotation: float = 0.0
var _hold_sprite_base_position: Vector2 = Vector2.ZERO
var _hold_placeholder: WeaponSymbol
var _marker: TargetMarker
var _last_cooldown: float = 1.0

func _ready() -> void:
	var parent := get_parent()
	if parent:
		_stats = parent.get_node_or_null("PlayerStats")
	if weapon_pivot:
		_pivot_base_position = weapon_pivot.position

	var hold_sprite := _get_hold_sprite()
	if hold_sprite:
		_hold_sprite_base_scale = hold_sprite.scale
		_hold_sprite_base_rotation = hold_sprite.rotation
		_hold_sprite_base_position = hold_sprite.position

	if show_target_marker:
		_marker = TargetMarker.new()
		_marker.setup(parent as Node2D)
		add_child(_marker)

func _process(delta: float) -> void:
	# Freigegebene Objekte sind in GDScript "falsy" - deshalb hier zuerst
	# is_instance_valid prüfen, sonst bleibt eine tote Referenz stehen.
	if not is_instance_valid(current_target):
		current_target = null
		if weapon_pivot:
			weapon_pivot.current_target = null

	if not equipped_weapon:
		_set_target(null)
		return

	if equipped_weapon != _visualized_weapon:
		_apply_weapon_visuals()

	fire_timer -= delta

	_set_target(find_target_in_range())
	_update_marker()

	if fire_timer > 0.0 or not current_target:
		return

	var roll := _roll_damage()
	if equipped_weapon.is_melee:
		if sword and sword.has_method("perform_swing"):
			sword.perform_swing(roll["damage"], roll["crit"])
	else:
		fire_at(current_target, roll["damage"], roll["crit"])

	_last_cooldown = equipped_weapon.cooldown / maxf(_get_attack_speed(), 0.05)
	fire_timer = _last_cooldown

# --- Zielerfassung ---------------------------------------------------------

## Reichweite, in der tatsächlich getroffen wird - Nahkampf rechnet den Arm mit.
func get_attack_range() -> float:
	if not equipped_weapon:
		return 0.0
	if equipped_weapon.is_melee and weapon_pivot:
		return weapon_pivot.pivot_radius + equipped_weapon.attack_reach
	return equipped_weapon.weapon_range

func find_target_in_range() -> Node2D:
	var max_range := get_attack_range()
	var nearest: Node2D = null
	var nearest_distance: float = max_range

	for enemy in get_tree().get_nodes_in_group("enemies"):
		if not is_instance_valid(enemy):
			continue
		var distance := global_position.distance_to(enemy.global_position)
		if distance < nearest_distance:
			nearest_distance = distance
			nearest = enemy

	return nearest

func _set_target(new_target: Node2D) -> void:
	if not is_instance_valid(current_target):
		current_target = null
	if new_target == current_target:
		return

	if is_instance_valid(current_target) and current_target.has_method("set_targeted"):
		current_target.set_targeted(false)

	current_target = new_target

	if current_target and current_target.has_method("set_targeted"):
		current_target.set_targeted(true)
	if weapon_pivot:
		weapon_pivot.current_target = current_target

	target_changed.emit(current_target)

func _update_marker() -> void:
	if not _marker:
		return
	_marker.target = current_target
	_marker.attack_range = get_attack_range()
	_marker.accent = equipped_weapon.projectile_color if not equipped_weapon.is_melee else Palette.AMBER
	_marker.cooldown_ratio = 1.0 - clampf(fire_timer / maxf(_last_cooldown, 0.001), 0.0, 1.0)

# --- Waffe -----------------------------------------------------------------

func _get_attack_speed() -> float:
	if not _stats:
		return 1.0
	return float(_stats.get_weapon_modifiers(equipped_weapon)["attack_speed"])

func _get_hold_sprite() -> Sprite2D:
	if not sword:
		return null
	return sword.get_node_or_null("Sprite2D") as Sprite2D

## Setzt das Waffen-Sprite in der Hand aus der WeaponData-Resource.
func _apply_weapon_visuals() -> void:
	_visualized_weapon = equipped_weapon
	_last_cooldown = equipped_weapon.cooldown

	var hold_sprite := _get_hold_sprite()
	if not hold_sprite:
		return

	var has_texture: bool = equipped_weapon.hold_texture != null
	if has_texture:
		hold_sprite.texture = equipped_weapon.hold_texture
	hold_sprite.scale = _hold_sprite_base_scale * equipped_weapon.hold_scale
	hold_sprite.rotation = _hold_sprite_base_rotation + deg_to_rad(equipped_weapon.hold_rotation_degrees)
	hold_sprite.position = _hold_position()
	hold_sprite.visible = has_texture

	# Ohne Haltesprite wird ein Platzhalter gezeichnet - sonst wäre die Waffe
	# unsichtbar oder es bliebe die Klinge der vorherigen Waffe stehen.
	var placeholder := _ensure_placeholder(hold_sprite)
	if not placeholder:
		return
	placeholder.visible = not has_texture
	if placeholder.visible:
		placeholder.category = equipped_weapon.category
		placeholder.tint = equipped_weapon.projectile_color if not equipped_weapon.is_melee else Palette.BONE
		placeholder.position = _hold_position()
		placeholder.scale = _hold_sprite_base_scale * equipped_weapon.hold_scale * PLACEHOLDER_SCALE
		placeholder.queue_redraw()

## Die Grundposition der Szene schiebt das Sprite weit nach vorn - das passt
## zu einer Klinge, die aus der Faust ragt. Eine Schusswaffe gehört in die Hand.
func _hold_position() -> Vector2:
	return _hold_sprite_base_position if equipped_weapon.is_melee else Vector2.ZERO

func _ensure_placeholder(hold_sprite: Sprite2D) -> WeaponSymbol:
	if is_instance_valid(_hold_placeholder):
		return _hold_placeholder

	var host := hold_sprite.get_parent()
	if not host:
		return null

	_hold_placeholder = WeaponSymbol.new()
	# Das Symbol zeigt nach +X, die Szenen-Grundhaltung ist auf Klingen gedreht.
	_hold_placeholder.rotation = _hold_sprite_base_rotation - PI * 0.5
	_hold_placeholder.z_index = hold_sprite.z_index
	host.add_child(_hold_placeholder)
	return _hold_placeholder

	if sword and sword.has_method("configure"):
		# Geschmiedete Waffen stoßen Gegner spürbar weiter zurück.
		var stagger_mult := Progression.reinforce_stagger_mult(RunState.get_weapon_level(equipped_weapon.weapon_id))
		sword.configure(
			equipped_weapon.swing_duration,
			equipped_weapon.swing_angle_degrees,
			equipped_weapon.knockback * stagger_mult
		)

func _roll_damage() -> Dictionary:
	if _stats:
		return _stats.compute_damage(_stats.get_weapon_base_damage(equipped_weapon), equipped_weapon)
	# Ohne Statistik-Knoten wenigstens die Schmiedestufe berücksichtigen.
	var level := RunState.get_weapon_level(equipped_weapon.weapon_id)
	return {"damage": equipped_weapon.get_base_damage(level), "crit": false}

func fire_at(target: Node2D, damage: float, crit: bool) -> void:
	if not equipped_weapon.projectile_scene:
		push_warning("Waffe '%s' ist Fernkampf, hat aber keine projectile_scene" % equipped_weapon.weapon_name)
		return

	var scene_root := get_tree().current_scene
	if not scene_root:
		return

	var base_direction := global_position.direction_to(target.global_position)
	var count: int = maxi(equipped_weapon.projectiles_per_shot, 1)
	var spread: float = deg_to_rad(equipped_weapon.spread_degrees)

	for i in count:
		var offset: float = 0.0
		if count > 1:
			offset = lerpf(-spread * 0.5, spread * 0.5, float(i) / float(count - 1))
		elif spread > 0.0:
			offset = randf_range(-spread * 0.5, spread * 0.5)

		var shot_direction := base_direction.rotated(offset)
		var projectile = equipped_weapon.projectile_scene.instantiate()
		scene_root.add_child(projectile)
		projectile.global_position = global_position + shot_direction * 16.0
		if projectile.has_method("setup"):
			projectile.setup(
				shot_direction,
				equipped_weapon.projectile_speed,
				damage,
				equipped_weapon.pierce_count,
				equipped_weapon.projectile_color,
				crit
			)

	FX.muzzle_flash(
		global_position + base_direction * 22.0,
		base_direction,
		equipped_weapon.projectile_color,
		equipped_weapon.muzzle_flash_size
	)
	FX.shake(equipped_weapon.screen_shake)
	_recoil(base_direction)

func _recoil(direction: Vector2) -> void:
	if not weapon_pivot:
		return
	weapon_pivot.position = _pivot_base_position - direction * 5.0
	var tween := weapon_pivot.create_tween()
	tween.tween_property(weapon_pivot, "position", _pivot_base_position, 0.12).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
