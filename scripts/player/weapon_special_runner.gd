extends RefCounted
class_name WeaponSpecialRunner

## Führt den Sonderschlag einer Waffe aus.
##
## Ausgelöst wird er vom WeaponController, sobald genug Treffer gelandet sind.
## Neuer Sonderschlag = neuer Eintrag in WeaponSpecial.Kind und ein Fall hier.

## `player` ist der Träger, `target` das aktuell anvisierte Ziel (darf leer sein).
static func execute(special: WeaponSpecial, weapon: WeaponData, player: Node2D,
		target: Node2D, base_damage: float) -> void:
	if not special or not is_instance_valid(player):
		return

	var origin: Vector2 = player.global_position
	var damage: float = base_damage * special.damage_mult

	FX.floating_text(origin + Vector2(0.0, -64.0), special.special_name, special.color, 20, 52.0)
	FX.light_flash(origin, special.color, 2.6, 1.6, 0.28)

	match special.kind:
		WeaponSpecial.Kind.SHOCKWAVE:
			_shockwave(special, player, origin, damage)
		WeaponSpecial.Kind.CLEAVE:
			_cleave(special, player, origin, damage)
		WeaponSpecial.Kind.BLEED_BURST:
			_bleed_burst(special, player, origin, damage)
		WeaponSpecial.Kind.PIERCE_SHOT:
			_pierce_shot(special, weapon, player, target, damage)
		WeaponSpecial.Kind.SPREAD_BURST:
			_spread_burst(special, weapon, player, target, damage)
		WeaponSpecial.Kind.VOLLEY:
			_volley(special, weapon, player, damage)
		WeaponSpecial.Kind.CHAIN_BOLT:
			_chain_bolt(special, player, origin, damage)
		WeaponSpecial.Kind.LIFE_STRIKE:
			_life_strike(special, player, origin, damage)
		WeaponSpecial.Kind.FROST_NOVA:
			_frost_nova(special, player, origin, damage)
		WeaponSpecial.Kind.METEOR:
			_meteor(special, player, target, origin, damage)

# --- Flächenwirkung --------------------------------------------------------

static func _shockwave(special: WeaponSpecial, player: Node2D, origin: Vector2, damage: float) -> void:
	FX.ring_burst(origin, special.color, 16.0, special.radius, 0.42, 10.0)
	FX.shake(9.0)
	FX.hitstop(0.07, 0.08)
	for enemy in _enemies_within(player, origin, special.radius):
		_damage(player, enemy, damage)
		if enemy.has_method("apply_knockback"):
			enemy.apply_knockback(origin.direction_to(enemy.global_position), special.knockback)

static func _cleave(special: WeaponSpecial, player: Node2D, origin: Vector2, damage: float) -> void:
	FX.ring_burst(origin, special.color, 10.0, special.radius, 0.3, 8.0)
	FX.hit_spark(origin, special.color, 22, Vector2.ZERO, TAU, special.radius * 0.6)
	FX.shake(7.0)
	FX.hitstop(0.08, 0.06)
	for enemy in _enemies_within(player, origin, special.radius):
		_damage(player, enemy, damage)

## Setzt alle Gegner in Reichweite sofort auf vollen Blutungsschaden.
static func _bleed_burst(special: WeaponSpecial, player: Node2D, origin: Vector2, damage: float) -> void:
	FX.ring_burst(origin, special.color, 8.0, special.radius, 0.34, 6.0)
	FX.shake(5.0)
	for enemy in _enemies_within(player, origin, special.radius):
		_damage(player, enemy, damage)
		FX.hit_spark(enemy.global_position, special.color, 8, Vector2.UP, PI, 50.0)

static func _frost_nova(special: WeaponSpecial, player: Node2D, origin: Vector2, damage: float) -> void:
	FX.ring_burst(origin, special.color, 14.0, special.radius, 0.5, 8.0)
	FX.shake(4.0)
	for enemy in _enemies_within(player, origin, special.radius):
		_damage(player, enemy, damage)
	# Alle Gegner gleichzeitig auszubremsen ist die Wirkung - sie läuft ab.
	Enemy.time_scale = 0.35
	var timer := player.get_tree().create_timer(special.duration)
	timer.timeout.connect(func() -> void: Enemy.time_scale = 1.0)

static func _life_strike(special: WeaponSpecial, player: Node2D, origin: Vector2, damage: float) -> void:
	FX.ring_burst(origin, special.color, 10.0, special.radius, 0.34, 6.0)
	var healed: float = 0.0
	for enemy in _enemies_within(player, origin, special.radius):
		_damage(player, enemy, damage)
		healed += damage * 0.35
	var health = player.get_node_or_null("PlayerHealth")
	if health and healed > 0.0 and health.has_method("heal_silent"):
		health.heal_silent(healed)
		FX.floating_text(origin + Vector2(0.0, -84.0), "+%.0f" % healed, Palette.MOSS, 18, 44.0)

## Blitz, der von Gegner zu Gegner springt und dabei schwächer wird.
static func _chain_bolt(special: WeaponSpecial, player: Node2D, origin: Vector2, damage: float) -> void:
	var remaining := _enemies_within(player, origin, special.radius)
	var current := origin
	var jumps: int = maxi(special.count, 1)

	for i in jumps:
		var next: Node2D = _nearest(remaining, current)
		if not next:
			break
		remaining.erase(next)
		FX.lightning(current, next.global_position, special.color, 8, 16.0)
		_damage(player, next, damage * pow(0.85, i))
		current = next.global_position
	FX.shake(5.0)

static func _meteor(special: WeaponSpecial, player: Node2D, target: Node2D,
		origin: Vector2, damage: float) -> void:
	var impact: Vector2 = target.global_position if is_instance_valid(target) else origin
	FX.lightning(impact + Vector2(0.0, -260.0), impact, special.color, 6, 22.0)
	FX.ring_burst(impact, special.color, 18.0, special.radius, 0.45, 12.0)
	FX.light_flash(impact, special.color, 3.4, 2.0, 0.35)
	FX.shake(11.0)
	FX.hitstop(0.09, 0.05)
	for enemy in _enemies_within(player, impact, special.radius):
		_damage(player, enemy, damage)
		if enemy.has_method("apply_knockback"):
			enemy.apply_knockback(impact.direction_to(enemy.global_position), special.knockback)

# --- Geschosse -------------------------------------------------------------

static func _pierce_shot(special: WeaponSpecial, weapon: WeaponData, player: Node2D,
		target: Node2D, damage: float) -> void:
	var direction := _aim(player, target)
	FX.muzzle_flash(player.global_position + direction * 22.0, direction, special.color, 60.0)
	FX.shake(6.0)
	_spawn(weapon, player, direction, damage, special.color, 40, 1.5)

static func _spread_burst(special: WeaponSpecial, weapon: WeaponData, player: Node2D,
		target: Node2D, damage: float) -> void:
	var direction := _aim(player, target)
	var count: int = maxi(special.count, 2)
	var spread: float = deg_to_rad(70.0)
	FX.muzzle_flash(player.global_position + direction * 20.0, direction, special.color, 52.0)
	FX.shake(6.0)
	for i in count:
		var offset: float = lerpf(-spread * 0.5, spread * 0.5, float(i) / float(count - 1))
		_spawn(weapon, player, direction.rotated(offset), damage, special.color, 1, 1.0)

static func _volley(special: WeaponSpecial, weapon: WeaponData, player: Node2D, damage: float) -> void:
	var count: int = maxi(special.count, 3)
	FX.ring_burst(player.global_position, special.color, 10.0, 70.0, 0.3, 6.0)
	FX.shake(5.0)
	for i in count:
		var angle: float = TAU * float(i) / float(count)
		_spawn(weapon, player, Vector2.RIGHT.rotated(angle), damage, special.color, 1, 1.0)

# --- Hilfen ----------------------------------------------------------------

static func _spawn(weapon: WeaponData, player: Node2D, direction: Vector2, damage: float,
		tint: Color, pierce: int, scale_up: float) -> void:
	if not weapon or not weapon.projectile_scene:
		return
	var host := player.get_tree().current_scene
	if not host:
		return

	var projectile = weapon.projectile_scene.instantiate()
	host.add_child(projectile)
	projectile.global_position = player.global_position + direction * 18.0
	if projectile.has_method("setup"):
		projectile.setup(direction, maxf(weapon.projectile_speed, 300.0), damage, pierce, tint, false)
	if not is_equal_approx(scale_up, 1.0) and projectile is Node2D:
		projectile.scale = Vector2.ONE * scale_up

## Richtung zum Ziel, sonst nach vorn.
static func _aim(player: Node2D, target: Node2D) -> Vector2:
	if is_instance_valid(target):
		return player.global_position.direction_to(target.global_position)
	if "facing" in player:
		return (player.facing as Vector2).normalized()
	return Vector2.RIGHT

static func _enemies_within(player: Node2D, origin: Vector2, radius: float) -> Array:
	var result: Array = []
	for enemy in player.get_tree().get_nodes_in_group("enemies"):
		if is_instance_valid(enemy) and origin.distance_to(enemy.global_position) <= radius:
			result.append(enemy)
	return result

static func _nearest(candidates: Array, from: Vector2) -> Node2D:
	var best: Node2D = null
	var best_distance: float = INF
	for enemy in candidates:
		if not is_instance_valid(enemy):
			continue
		var distance := from.distance_to(enemy.global_position)
		if distance < best_distance:
			best_distance = distance
			best = enemy
	return best

static func _damage(player: Node2D, enemy: Node, amount: float) -> void:
	if not enemy.has_method("take_damage"):
		return
	enemy.take_damage(amount, player.global_position, false)
	var stats = player.get_node_or_null("PlayerStats")
	if stats:
		stats.report_damage(amount)
