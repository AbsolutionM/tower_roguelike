extends Node
class_name PlayerAbility

## Charakter-abhängige Spezialfähigkeit (der dritte Button).
## Jeder Charakter bekommt eine eigene AbilityData-Resource.

signal cooldown_changed(remaining: float, total: float)
signal ability_used(ability: AbilityData)

@export var ability: AbilityData

var cooldown_timer: float = 0.0

var _body: Node2D
var _slow_timer: float = 0.0

func _ready() -> void:
	_body = get_parent() as Node2D
	PlayerInput.ability_pressed.connect(use)

func _process(delta: float) -> void:
	if cooldown_timer > 0.0:
		cooldown_timer = maxf(cooldown_timer - delta, 0.0)
		cooldown_changed.emit(cooldown_timer, get_cooldown())
		if cooldown_timer <= 0.0:
			_on_ready_again()

	if _slow_timer > 0.0:
		_slow_timer -= delta
		if _slow_timer <= 0.0:
			Enemy.time_scale = 1.0

func get_cooldown() -> float:
	if not ability:
		return 1.0
	var stats = _body.get_node_or_null("PlayerStats") if _body else null
	if stats:
		return ability.cooldown * stats.ability_cooldown_mult
	return ability.cooldown

func is_ready() -> bool:
	return ability != null and cooldown_timer <= 0.0

func use() -> void:
	if not is_ready() or not _body:
		return
	cooldown_timer = get_cooldown()
	ability_used.emit(ability)
	cooldown_changed.emit(cooldown_timer, get_cooldown())
	_execute()

func _on_ready_again() -> void:
	if _body:
		FX.ring_burst(_body.global_position, Color(1.0, 1.0, 1.0, 0.5), 20.0, 44.0, 0.25, 3.0)

func _execute() -> void:
	match ability.kind:
		AbilityData.Kind.SHOCKWAVE:
			_shockwave()
		AbilityData.Kind.BULLET_RING:
			_bullet_ring()
		AbilityData.Kind.BLINK:
			_blink()
		AbilityData.Kind.HEAL_PULSE:
			_heal_pulse()
		AbilityData.Kind.FAN_SHOT:
			_fan_shot()
		AbilityData.Kind.DASH_STRIKE:
			_dash_strike()
		AbilityData.Kind.SHIELD:
			_shield()
		AbilityData.Kind.TIME_SLOW:
			_time_slow()
		AbilityData.Kind.MAGNET_PULSE:
			_magnet_pulse()
		AbilityData.Kind.CHAIN_LIGHTNING:
			_chain_lightning()

# --- Hilfsfunktionen -------------------------------------------------------

func _aim_direction() -> Vector2:
	var target := _nearest_enemy(99999.0)
	if target:
		return _body.global_position.direction_to(target.global_position)
	var input_direction := PlayerInput.get_move_vector()
	if input_direction.length() > 0.05:
		return input_direction.normalized()
	if "facing" in _body:
		return _body.facing
	return Vector2.DOWN

func _nearest_enemy(max_range: float, exclude: Array = []) -> Node2D:
	var nearest: Node2D = null
	var nearest_distance: float = max_range
	for enemy in get_tree().get_nodes_in_group("enemies"):
		if not is_instance_valid(enemy) or enemy in exclude:
			continue
		var distance: float = _body.global_position.distance_to(enemy.global_position)
		if distance < nearest_distance:
			nearest_distance = distance
			nearest = enemy
	return nearest

func _damage_enemy(enemy: Node, amount: float, from_position: Vector2) -> void:
	if enemy.has_method("take_damage"):
		enemy.take_damage(amount, from_position, false)
		var stats = _body.get_node_or_null("PlayerStats")
		if stats:
			stats.report_damage(amount)

func _spawn_projectile(direction: Vector2, offset: float = 20.0) -> void:
	var scene_root := get_tree().current_scene
	if not scene_root or not ability.projectile_scene:
		return
	var projectile = ability.projectile_scene.instantiate()
	scene_root.add_child(projectile)
	projectile.global_position = _body.global_position + direction * offset
	if projectile.has_method("setup"):
		projectile.setup(direction, ability.projectile_speed, ability.damage, 0, ability.color, false)

# --- Fähigkeiten -----------------------------------------------------------

func _shockwave() -> void:
	var origin: Vector2 = _body.global_position
	FX.ring_burst(origin, ability.color, 16.0, ability.radius, 0.42, 12.0)
	FX.ring_burst(origin, Color(1.0, 1.0, 1.0, 0.8), 8.0, ability.radius * 0.7, 0.3, 6.0)
	FX.hit_spark(origin, ability.color, 16, Vector2.ZERO, TAU, ability.radius * 0.5)
	FX.light_flash(origin, ability.color, 3.0, ability.radius / 120.0, 0.3)
	FX.shake(9.0)
	FX.hitstop(0.08, 0.08)
	FX.zoom_punch(0.05)

	for enemy in get_tree().get_nodes_in_group("enemies"):
		if not is_instance_valid(enemy):
			continue
		if origin.distance_to(enemy.global_position) > ability.radius:
			continue
		_damage_enemy(enemy, ability.damage, origin)
		if enemy.has_method("apply_knockback"):
			enemy.apply_knockback(origin.direction_to(enemy.global_position), ability.knockback)

func _bullet_ring() -> void:
	FX.ring_burst(_body.global_position, ability.color, 10.0, 80.0, 0.3, 6.0)
	FX.shake(4.0)
	var count: int = maxi(ability.projectile_count, 1)
	for i in count:
		var angle: float = TAU * float(i) / float(count)
		_spawn_projectile(Vector2(cos(angle), sin(angle)))

func _fan_shot() -> void:
	var base_direction := _aim_direction()
	var count: int = maxi(ability.projectile_count, 1)
	var spread: float = deg_to_rad(ability.spread_degrees)

	FX.muzzle_flash(_body.global_position + base_direction * 24.0, base_direction, ability.color, 48.0)
	FX.shake(6.0)
	FX.zoom_punch(0.04)

	for i in count:
		var offset: float = 0.0
		if count > 1:
			offset = lerpf(-spread * 0.5, spread * 0.5, float(i) / float(count - 1))
		_spawn_projectile(base_direction.rotated(offset), 24.0)

func _blink() -> void:
	var direction := PlayerInput.get_move_vector()
	if direction.length() < 0.05 and "facing" in _body:
		direction = _body.facing
	if direction.length() < 0.05:
		direction = Vector2.DOWN

	var start: Vector2 = _body.global_position
	var target: Vector2 = start + direction.normalized() * ability.blink_distance

	var sprite := _body.get_node_or_null("FirstBody")
	if sprite:
		for i in 5:
			FX.afterimage(sprite, 0.4, Color(ability.color, 0.45))

	_body.global_position = target
	FX.ring_burst(start, ability.color, 8.0, 60.0, 0.3, 5.0)
	FX.ring_burst(target, ability.color, 8.0, 60.0, 0.3, 5.0)
	FX.dust_puff(start, Color(ability.color, 0.5), 6, 30.0)
	FX.shake(3.0)

	var health := _body.get_node_or_null("PlayerHealth")
	if health and health.has_method("set_invulnerable"):
		health.set_invulnerable(0.25)

func _dash_strike() -> void:
	var direction := _aim_direction()
	var start: Vector2 = _body.global_position
	var target: Vector2 = start + direction * ability.dash_distance

	var sprite := _body.get_node_or_null("FirstBody")
	if sprite:
		for i in 6:
			FX.afterimage(sprite, 0.45, Color(ability.color, 0.5))

	# Alles im Korridor zwischen Start und Ziel wird getroffen.
	var corridor: float = maxf(ability.radius, 60.0)
	for enemy in get_tree().get_nodes_in_group("enemies"):
		if not is_instance_valid(enemy):
			continue
		var to_enemy: Vector2 = enemy.global_position - start
		var along: float = to_enemy.dot(direction)
		if along < -20.0 or along > ability.dash_distance + 40.0:
			continue
		if absf(to_enemy.cross(direction)) > corridor:
			continue
		_damage_enemy(enemy, ability.damage, start)
		if enemy.has_method("apply_knockback"):
			enemy.apply_knockback(direction, ability.knockback)

	_body.global_position = target
	FX.hit_spark(start + direction * ability.dash_distance * 0.5, ability.color, 18, direction, PI * 0.4, 120.0)
	FX.ring_burst(target, ability.color, 10.0, 90.0, 0.32, 7.0)
	FX.light_flash(target, ability.color, 2.6, 1.4, 0.25)
	FX.shake(8.0)
	FX.hitstop(0.09, 0.07)

	var health := _body.get_node_or_null("PlayerHealth")
	if health and health.has_method("set_invulnerable"):
		health.set_invulnerable(0.35)

func _shield() -> void:
	var health := _body.get_node_or_null("PlayerHealth")
	if health and health.has_method("set_invulnerable"):
		health.set_invulnerable(ability.duration)

	FX.ring_burst(_body.global_position, ability.color, 20.0, 110.0, 0.5, 9.0)
	FX.light_flash(_body.global_position, ability.color, 2.8, 1.8, 0.4)
	FX.floating_text(_body.global_position + Vector2(0.0, -54.0), "Schild", ability.color, 20, 40.0)
	FX.shake(4.0)

	# Der Schild stößt Gegner beim Aktivieren weg.
	for enemy in get_tree().get_nodes_in_group("enemies"):
		if not is_instance_valid(enemy):
			continue
		if _body.global_position.distance_to(enemy.global_position) > ability.radius:
			continue
		if enemy.has_method("apply_knockback"):
			enemy.apply_knockback(_body.global_position.direction_to(enemy.global_position), ability.knockback)

func _time_slow() -> void:
	Enemy.time_scale = clampf(ability.slow_factor, 0.05, 1.0)
	_slow_timer = ability.duration

	FX.ring_burst(_body.global_position, ability.color, 24.0, 700.0, 0.8, 14.0)
	FX.screen_flash(Color(ability.color, 0.22), 0.5)
	FX.light_flash(_body.global_position, ability.color, 2.4, 2.6, 0.5)
	FX.floating_text(_body.global_position + Vector2(0.0, -54.0), "Zeitriss", ability.color, 20, 40.0)
	FX.shake(5.0)

func _magnet_pulse() -> void:
	var origin: Vector2 = _body.global_position
	FX.ring_burst(origin, ability.color, 30.0, 620.0, 0.6, 10.0)
	FX.light_flash(origin, ability.color, 2.2, 2.2, 0.4)
	FX.shake(3.0)

	var collected: int = 0
	for pickup in get_tree().get_nodes_in_group("pickups"):
		if not is_instance_valid(pickup) or not pickup.has_method("collect"):
			continue
		pickup.collect()
		collected += 1

	if collected > 0:
		FX.floating_text(origin + Vector2(0.0, -54.0), "%d eingesammelt" % collected, ability.color, 18, 44.0)

	var health := _body.get_node_or_null("PlayerHealth")
	if health and health.has_method("heal") and ability.heal_amount > 0.0:
		health.heal(ability.heal_amount)

func _chain_lightning() -> void:
	var current_position: Vector2 = _body.global_position
	var hit: Array = []

	for i in maxi(ability.chain_jumps, 1):
		var target: Node2D = null
		var nearest_distance: float = ability.chain_range
		for enemy in get_tree().get_nodes_in_group("enemies"):
			if not is_instance_valid(enemy) or enemy in hit:
				continue
			var distance: float = current_position.distance_to(enemy.global_position)
			if distance < nearest_distance:
				nearest_distance = distance
				target = enemy

		if not target:
			break

		FX.lightning(current_position, target.global_position, ability.color)
		FX.light_flash(target.global_position, ability.color, 2.0, 0.7, 0.18)
		# Jeder Sprung trifft etwas schwächer.
		_damage_enemy(target, ability.damage * pow(0.85, i), current_position)

		hit.append(target)
		current_position = target.global_position

	if hit.is_empty():
		FX.ring_burst(_body.global_position, ability.color, 10.0, 90.0, 0.3, 5.0)
		return

	FX.shake(6.0)
	FX.hitstop(0.07, 0.08)

func _heal_pulse() -> void:
	var health := _body.get_node_or_null("PlayerHealth")
	if health and health.has_method("heal"):
		health.heal(ability.heal_amount)
	FX.ring_burst(_body.global_position, FX.COLOR_HEAL, 12.0, ability.radius, 0.45, 8.0)
