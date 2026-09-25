extends Area2D
class_name Enemy

## Ein einziges Gegner-Script für alle Gegnertypen.
## Neuer Gegner = neue EnemyData-Resource (Werte, Verhalten, Loot, Optik).

signal died(enemy: Enemy)

const DEFAULT_PICKUP_SCENE := preload("res://scenes/props/item_pickup.tscn")

enum State { APPROACH, WINDUP, CHARGE }

## Global gebremste Zeit für Gegner (Zeitriss-Fähigkeit). 1.0 = normal.
static var time_scale: float = 1.0

## Halbe Höhe des Sprites, für das Position und Schatten in der Szene
## eingerichtet sind.
const SPRITE_LAYOUT_HALF_HEIGHT := 16.0

@export var enemy_data: EnemyData
@export var max_health: float = 30.0
@export var move_speed: float = 40.0
@export var health_bar_bg: ColorRect
@export var health_bar_fill: ColorRect
@export var sprite: Sprite2D
@export var squash_speed: float = 6.0
@export var squash_amount: float = 0.15
@export var trail_interval: float = 0.25
@export var trail_offset: float = 40.0
@export var trail_colors: Array[Color] = [
	Color(Palette.MOSS, 0.45),
	Color(Palette.edge(Palette.MOSS), 0.4),
	Color(Palette.LIME, 0.5)
]
@export var knockback_friction: float = 600.0
@export var outline_material: ShaderMaterial
@export var pickup_scene: PackedScene
@export var show_shadow: bool = true
@export var separation_radius: float = 48.0
@export var separation_strength: float = 70.0

var current_health: float
var player: Node2D
var player_health: Node
var bar_full_width: float = 0.0
var base_scale: Vector2 = Vector2.ONE
var sprite_base_position: Vector2 = Vector2.ZERO
var wobble_time: float = 0.0
var trail_timer: float = 0.0
var last_direction: Vector2 = Vector2.DOWN
var knockback_velocity: Vector2 = Vector2.ZERO

var state: State = State.APPROACH
var state_timer: float = 0.0
var attack_timer: float = 0.0
var contact_timer: float = 0.5
var spawn_timer: float = 0.32
var is_dying: bool = false
var charge_direction: Vector2 = Vector2.ZERO
var strafe_sign: float = 1.0

var _shadow: BlobShadow
## Brand, Frost, Gift, Blutung aus den Waffen-Upgrades.
var status: EnemyStatus
var _aura_timer: float = 0.0
var _base_material: Material
var _symbol: EnemySymbol
var _symbol_base_y: float = 0.0
var _squash_offset: float = 0.0
var _shadow_radius: float = 16.0

## Höhe über dem Boden - treibt Sprünge und Flug an.
var _height: float = 0.0
var _hop_timer: float = 0.0
var _hop_progress: float = -1.0
var _fly_time: float = 0.0

func _ready() -> void:
	add_to_group("enemies")
	add_to_group("damageable")
	status = EnemyStatus.new(self)

	apply_enemy_data()
	current_health = max_health

	player = get_tree().get_first_node_in_group("player")
	if player:
		player_health = player.get_node_or_null("PlayerHealth")

	strafe_sign = 1.0 if randf() < 0.5 else -1.0

	_fit_health_bar()
	if health_bar_bg:
		health_bar_bg.modulate.a = 0.0
	if sprite:
		base_scale = sprite.scale
		sprite_base_position = sprite.position
		_base_material = sprite.material

	_create_symbol()

	if show_shadow:
		_shadow_radius = enemy_data.shadow_radius if enemy_data else 16.0
		_shadow = BlobShadow.new()
		_shadow.radius = _shadow_radius
		_shadow.position = Vector2(0.0, 6.0)
		add_child(_shadow)

	_hop_timer = randf_range(0.1, 0.6)
	_fly_time = randf() * TAU

	_play_spawn_animation()

## Ohne eigene Textur bekommt der Gegner ein gezeichnetes Platzhalter-Symbol.
func _create_symbol() -> void:
	if not enemy_data or enemy_data.sprite_texture:
		return
	_symbol = EnemySymbol.new()
	_symbol.kind = enemy_data.symbol
	_symbol.tint = enemy_data.tint
	_symbol.symbol_size = enemy_data.symbol_size * enemy_data.sprite_scale
	_symbol_base_y = -_symbol.symbol_size * 0.55
	_symbol.position = Vector2(0.0, _symbol_base_y)
	add_child(_symbol)

func apply_enemy_data() -> void:
	if not enemy_data:
		return
	max_health = enemy_data.max_health * GameManager.get_health_scale()
	move_speed = enemy_data.move_speed * Weather.get_enemy_speed_mult()
	squash_amount = enemy_data.squash_amount
	squash_speed = enemy_data.squash_speed
	knockback_friction = enemy_data.knockback_friction
	if not enemy_data.trail_colors.is_empty():
		trail_colors = enemy_data.trail_colors
	if sprite:
		if enemy_data.sprite_texture:
			sprite.texture = enemy_data.sprite_texture
			sprite.visible = true
			# Die Szene ist für 32 Pixel hohe Sprites gebaut. Andere Höhen
			# werden an derselben Unterkante ausgerichtet, sonst schwebt ein
			# flacher Schleim über seinem Schatten und ein hoher steckt darin.
			var height: float = enemy_data.sprite_texture.get_size().y
			sprite.offset = Vector2(0.0, SPRITE_LAYOUT_HALF_HEIGHT - height * 0.5)
		else:
			# Platzhalter-Symbol übernimmt die Darstellung.
			sprite.visible = false
		sprite.modulate = enemy_data.tint
		if not is_equal_approx(enemy_data.sprite_scale, 1.0):
			sprite.scale *= enemy_data.sprite_scale

func _play_spawn_animation() -> void:
	FX.ring_burst(global_position, Color(Palette.VIOLET, 0.7), 4.0, 44.0, 0.3, 4.0)

	if _symbol:
		_symbol.scale = Vector2.ZERO
		var symbol_tween := _symbol.create_tween()
		symbol_tween.tween_property(_symbol, "scale", Vector2.ONE * 1.15, 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		symbol_tween.tween_property(_symbol, "scale", Vector2.ONE, 0.11)
		return

	if not sprite:
		return
	var target_scale := sprite.scale
	base_scale = target_scale
	sprite.scale = Vector2.ZERO
	var tween := sprite.create_tween()
	tween.tween_property(sprite, "scale", target_scale * 1.18, 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.tween_property(sprite, "scale", target_scale, 0.11)

func _process(delta: float) -> void:
	if is_dying:
		return

	spawn_timer = maxf(spawn_timer - delta, 0.0)
	attack_timer = maxf(attack_timer - delta, 0.0)
	contact_timer = maxf(contact_timer - delta, 0.0)

	var speed_factor := _tick_movement(delta) * status.speed_factor()
	_tick_status(delta)
	if is_dying:
		return
	var move_vector := (_behavior_velocity(delta) * speed_factor + _separation_velocity() + _obstacle_push()) * time_scale

	global_position += (move_vector + knockback_velocity) * delta
	knockback_velocity = knockback_velocity.move_toward(Vector2.ZERO, knockback_friction * delta)

	_check_contact_damage()
	_tick_heal_aura(delta)
	update_squash(delta)
	update_trail(delta)
	_apply_visual_height()

## Schaden über Zeit aus Brand und Gift, dazu die Einfärbung.
func _tick_status(delta: float) -> void:
	var amount := status.tick(delta)
	modulate = status.tint()
	if amount > 0.0:
		take_status_damage(amount, Palette.EMBER if status.burn_time > 0.0 else Palette.LIME)

## Relikte, die beim Tod eines Gegners greifen.
func _relic_kill_effects() -> void:
	if not GameManager.run_active:
		return
	if RunState.has_relic("bounty") and GameManager.room_kills == 1:
		_drop_item("res://resources/items/red_heart.tres", 1)
	if RunState.has_relic("midas_hand") and randf() < 0.05:
		_drop_item("res://resources/items/gold_coin.tres", 20)
		FX.floating_text(global_position + Vector2(0.0, -40.0), "Midas!", Palette.GOLD, 18, 36.0)
	if RunState.has_relic("time_thief") and enemy_data and enemy_data.drop_table and enemy_data.drop_table.resource_path.ends_with("dt_elite.tres"):
		GameManager.add_room_time(3.0)
		FX.floating_text(global_position + Vector2(0.0, -56.0), "+3 s", Palette.AZURE, 18, 36.0)
	if RunState.has_relic("chain_reaction") and randf() < 0.2:
		FX.ring_burst(global_position, Palette.EMBER, 10.0, 80.0, 0.3, 6.0)
		for other in get_tree().get_nodes_in_group("enemies"):
			if other != self and is_instance_valid(other) and global_position.distance_to(other.global_position) <= 80.0:
				other.take_damage(40.0, global_position, false)

func _drop_item(path: String, count: int) -> void:
	var scene_root := get_tree().current_scene
	if not pickup_scene or not scene_root:
		return
	var pickup = pickup_scene.instantiate()
	pickup.item = load(path)
	pickup.count = count
	pickup.global_position = global_position
	if pickup.has_method("pop_out"):
		pickup.pop_out()
	scene_root.add_child.call_deferred(pickup)

## Brand-Affinität: ein brennender Gegner steckt beim Tod einen Nachbarn an.
func _spread_burn() -> void:
	if not status or status.burn_time <= 0.0 or not status.burn_spreads:
		return
	for other in get_tree().get_nodes_in_group("enemies"):
		if other != self and is_instance_valid(other) and global_position.distance_to(other.global_position) <= 80.0:
			other.status.apply_burn(status.burn_dps, 3.0)
			other.status.burn_spreads = true
			FX.ring_burst(other.global_position, Palette.EMBER, 4.0, 30.0, 0.25, 3.0)
			return

## Schaden ohne Treffereffekte - für Brand, Gift und Blutung.
func take_status_damage(amount: float, color: Color = Palette.EMBER) -> void:
	if is_dying or amount <= 0.0:
		return
	current_health -= amount
	update_health_bar()
	FX.damage_number(global_position + Vector2(0.0, -30.0), amount, false, color)
	if current_health <= 0.0:
		die()

## Aktualisiert die Höhe über dem Boden und liefert den Tempofaktor.
func _tick_movement(delta: float) -> float:
	if not enemy_data:
		return 1.0

	match enemy_data.movement:
		EnemyData.Movement.HOP:
			return _tick_hop(delta)
		EnemyData.Movement.FLY:
			_fly_time += delta
			_height = enemy_data.fly_height + sin(_fly_time * 2.4) * enemy_data.fly_bob
			return 1.0
		_:
			_height = 0.0
			return 1.0

## Schleime stehen still und springen dann in einem Bogen nach vorn.
func _tick_hop(delta: float) -> float:
	var duration: float = maxf(enemy_data.hop_duration, 0.05)

	if _hop_progress >= 0.0:
		_hop_progress += delta / duration
		if _hop_progress >= 1.0:
			_hop_progress = -1.0
			_height = 0.0
			FX.dust_puff(global_position + Vector2(0.0, 6.0), Color(Palette.MIST, 0.45), 4, 18.0)
			return 0.0
		_height = sin(_hop_progress * PI) * enemy_data.hop_height
		return enemy_data.hop_speed_mult

	_height = 0.0
	_hop_timer -= delta
	if _hop_timer <= 0.0:
		_hop_timer = enemy_data.hop_interval
		_hop_progress = 0.0
		return enemy_data.hop_speed_mult
	return 0.0

func _apply_visual_height() -> void:
	if _symbol:
		_symbol.position.y = _symbol_base_y - _height
	elif sprite:
		sprite.position.y = sprite_base_position.y + _squash_offset - _height

	# Der Schatten schrumpft, je höher der Gegner schwebt.
	if _shadow and enemy_data and enemy_data.movement != EnemyData.Movement.GROUND:
		var t: float = clampf(_height / 90.0, 0.0, 1.0)
		_shadow.configure(_shadow_radius * (1.0 - 0.4 * t), 0.28 * (1.0 - 0.5 * t))

func _visual() -> Node2D:
	return _symbol if _symbol else sprite

## Ruhe-Skalierung der aktuellen Darstellung (Symbol oder Sprite).
func _visual_rest_scale() -> Vector2:
	return Vector2.ONE if _symbol else base_scale

## Heiler-Gegner pulsen und heilen alles in ihrer Nähe.
func _tick_heal_aura(delta: float) -> void:
	if not enemy_data or enemy_data.heal_aura_rate <= 0.0:
		return
	_aura_timer -= delta
	if _aura_timer > 0.0:
		return
	_aura_timer = 0.6

	FX.ring_burst(global_position, Color(Palette.LIME, 0.6), 12.0, enemy_data.heal_aura_radius, 0.55, 3.0)
	for other in get_tree().get_nodes_in_group("enemies"):
		if other == self or not is_instance_valid(other):
			continue
		if global_position.distance_to(other.global_position) > enemy_data.heal_aura_radius:
			continue
		if other.has_method("receive_heal"):
			other.receive_heal(enemy_data.heal_aura_rate * 0.6)

func receive_heal(amount: float) -> void:
	if is_dying or current_health >= max_health:
		return
	current_health = minf(current_health + amount, max_health)
	update_health_bar()
	FX.floating_text(global_position + Vector2(0.0, -30.0), "+%d" % int(round(amount)), FX.COLOR_HEAL, 14, 26.0)

## Die Gegner-Szene stammt vom RoomController - so kann ein Gegner Kopien spawnen.
func get_enemy_scene() -> PackedScene:
	var controller = get_tree().get_first_node_in_group("room_controller")
	if controller and "enemy_scene" in controller:
		return controller.enemy_scene
	return null

## Spawnt Gegner aus einer EnemyData-Resource rund um diese Position.
func spawn_enemies_from_data(data: EnemyData, amount: int, spread: float = 60.0) -> void:
	if not data or amount <= 0:
		return
	var scene := get_enemy_scene()
	var scene_root := get_tree().current_scene
	if not scene or not scene_root:
		return

	for i in amount:
		var spawned = scene.instantiate()
		spawned.enemy_data = data
		var angle: float = TAU * float(i) / float(amount) + randf() * 0.5
		spawned.global_position = global_position + Vector2(cos(angle), sin(angle)) * spread
		scene_root.add_child.call_deferred(spawned)

func _behavior_velocity(delta: float) -> Vector2:
	if not player or not is_instance_valid(player):
		return Vector2.ZERO

	var to_player := global_position.direction_to(player.global_position)
	var distance := global_position.distance_to(player.global_position)
	_face(to_player)

	var behavior: int = enemy_data.behavior if enemy_data else EnemyData.Behavior.CHASE

	match behavior:
		EnemyData.Behavior.CHARGER:
			return _charger_velocity(delta, to_player, distance)
		EnemyData.Behavior.SHOOTER:
			return _shooter_velocity(to_player, distance)
		EnemyData.Behavior.ORBITER:
			return _orbiter_velocity(to_player, distance)
		_:
			return to_player * move_speed

## Drückt Bodengegner aus Felsen heraus - Flieger schweben darüber hinweg.
func _obstacle_push() -> Vector2:
	if enemy_data and enemy_data.movement == EnemyData.Movement.FLY:
		return Vector2.ZERO

	var push := Vector2.ZERO
	for obstacle in get_tree().get_nodes_in_group("obstacles"):
		if not is_instance_valid(obstacle):
			continue
		var offset: Vector2 = global_position - obstacle.global_position
		var distance: float = offset.length()
		var radius: float = obstacle.get_radius() + 20.0
		if distance > radius or distance < 0.01:
			continue
		push += (offset / distance) * (1.0 - distance / radius)

	return push * 200.0

## Hält Gegner auf Abstand zueinander, damit sie sich nicht stapeln.
func _separation_velocity() -> Vector2:
	if separation_strength <= 0.0:
		return Vector2.ZERO

	var push := Vector2.ZERO
	for other in get_tree().get_nodes_in_group("enemies"):
		if other == self or not is_instance_valid(other):
			continue
		var offset: Vector2 = global_position - other.global_position
		var distance: float = offset.length()
		if distance > separation_radius or distance < 0.01:
			continue
		push += (offset / distance) * (1.0 - distance / separation_radius)

	return push * separation_strength

func _face(direction: Vector2) -> void:
	if absf(direction.x) > 0.1:
		last_direction = direction
		if sprite:
			sprite.flip_h = direction.x < 0.0

func _charger_velocity(delta: float, to_player: Vector2, distance: float) -> Vector2:
	var trigger: float = enemy_data.charge_trigger_range if enemy_data else 260.0
	var windup: float = enemy_data.charge_windup if enemy_data else 0.55
	var charge_speed: float = enemy_data.charge_speed if enemy_data else 430.0

	match state:
		State.APPROACH:
			if distance < trigger and attack_timer <= 0.0 and not GameManager.is_overview():
				state = State.WINDUP
				state_timer = windup
				FX.ring_burst(global_position, Palette.EMBER, 6.0, 46.0, windup, 4.0)
			return to_player * move_speed

		State.WINDUP:
			state_timer -= delta
			charge_direction = to_player
			if state_timer <= 0.0:
				state = State.CHARGE
				state_timer = 0.42
				FX.dust_puff(global_position + Vector2(0.0, 8.0), Color(Palette.AMBER, 0.5), 5, 26.0)
			return -to_player * move_speed * 0.35

		State.CHARGE:
			state_timer -= delta
			if sprite:
				FX.afterimage(sprite, 0.22, Color(Palette.EMBER, 0.4))
			if state_timer <= 0.0:
				state = State.APPROACH
				attack_timer = enemy_data.attack_cooldown if enemy_data else 1.2
			return charge_direction * charge_speed

	return Vector2.ZERO

func _shooter_velocity(to_player: Vector2, distance: float) -> Vector2:
	var keep: float = enemy_data.keep_distance if enemy_data else 190.0
	var shoot_range: float = enemy_data.shoot_range if enemy_data else 340.0

	if attack_timer <= 0.0 and distance <= shoot_range and spawn_timer <= 0.0 and not GameManager.is_overview():
		_shoot(to_player)

	if distance > keep * 1.15:
		return to_player * move_speed
	if distance < keep * 0.75:
		return -to_player * move_speed
	return to_player.orthogonal() * move_speed * 0.7 * strafe_sign

func _orbiter_velocity(to_player: Vector2, distance: float) -> Vector2:
	var keep: float = enemy_data.keep_distance if enemy_data else 150.0
	var radial := to_player * clampf((distance - keep) / 60.0, -1.0, 1.0)
	var tangential := to_player.orthogonal() * strafe_sign
	return (radial + tangential).normalized() * move_speed

func _shoot(direction: Vector2) -> void:
	if not enemy_data or not enemy_data.projectile_scene:
		return
	var scene_root := get_tree().current_scene
	if not scene_root:
		return

	attack_timer = enemy_data.attack_cooldown

	var projectile = enemy_data.projectile_scene.instantiate()
	scene_root.add_child(projectile)
	projectile.global_position = global_position + direction * 16.0
	if "hostile" in projectile:
		projectile.hostile = true
	if projectile.has_method("setup"):
		projectile.setup(
			direction,
			enemy_data.projectile_speed,
			enemy_data.projectile_damage * GameManager.get_damage_scale(),
			0,
			Palette.BLOOD,
			false
		)

	FX.muzzle_flash(global_position + direction * 18.0, direction, Palette.ROSE, 22.0)

func _check_contact_damage() -> void:
	# Im Überblick zu Beginn des Raums greift noch niemand an.
	if contact_timer > 0.0 or spawn_timer > 0.0 or GameManager.is_overview():
		return
	if not player or not is_instance_valid(player) or not player_health:
		return

	var range_value: float = enemy_data.contact_range if enemy_data else 38.0
	if global_position.distance_to(player.global_position) > range_value:
		return

	var damage: float = (enemy_data.contact_damage if enemy_data else 8.0) * GameManager.get_damage_scale()
	contact_timer = 0.65
	if player_health.has_method("take_damage"):
		player_health.take_damage(damage, global_position)

func apply_knockback(direction: Vector2, force: float) -> void:
	knockback_velocity = direction.normalized() * force

func update_squash(delta: float) -> void:
	if not sprite or not sprite.texture or spawn_timer > 0.0:
		return

	wobble_time += delta * squash_speed
	var squash: float = (sin(wobble_time) + 1.0) * 0.5 * squash_amount

	var new_scale_x: float = base_scale.x * (1.0 + squash)
	var new_scale_y: float = base_scale.y * (1.0 - squash)
	sprite.scale = Vector2(new_scale_x, new_scale_y)

	var texture_height := float(sprite.texture.get_height())
	# Die endgültige Position setzt _apply_visual_height, damit Sprünge dazukommen.
	_squash_offset = (base_scale.y - new_scale_y) * texture_height / 2.0

func update_trail(delta: float) -> void:
	if trail_colors.is_empty():
		return
	trail_timer -= delta
	if trail_timer > 0.0:
		return
	trail_timer = trail_interval
	FX.dust_puff(
		global_position - last_direction * trail_offset,
		trail_colors[randi() % trail_colors.size()],
		3,
		12.0
	)

func take_damage(amount: float, from_position: Vector2 = Vector2.ZERO, crit: bool = false) -> void:
	if is_dying:
		return

	if DevMode.one_hit_kill:
		amount = maxf(amount, current_health)
	current_health -= amount
	update_health_bar()

	var top := global_position + Vector2(0.0, -34.0)
	FX.damage_number(top, amount, crit)

	var impact_direction: Vector2 = Vector2.ZERO
	if from_position != Vector2.ZERO:
		impact_direction = from_position.direction_to(global_position)
	FX.impact(global_position, impact_direction, FX.COLOR_CRIT if crit else FX.COLOR_DAMAGE, 1.4 if crit else 1.0)

	var visual := _visual()
	if visual and DevMode.fx("hit_flash"):
		FX.flash(visual, Color(8.0, 8.0, 8.0), 0.12)
		var rest := _visual_rest_scale()
		var tween := visual.create_tween()
		tween.tween_property(visual, "scale", rest * Vector2(1.3, 0.72), 0.05)
		tween.tween_property(visual, "scale", rest, 0.12).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)

	if crit:
		FX.hitstop(0.07, 0.06)
		FX.shake(5.0)

	if current_health <= 0.0:
		die()

## Der Balken stand mit fester Breite in der Szene und war bei kleinen Gegnern
## breiter als der Gegner selbst - er las sich dann wie ein Strich im Raum.
## Jetzt richtet er sich nach der sichtbaren Größe.
func _fit_health_bar() -> void:
	if not health_bar_bg or not health_bar_fill:
		return

	var width: float = clampf(get_visual_radius() * 1.7, 22.0, 90.0)
	var height: float = 5.0
	var below: float = get_visual_radius() * 0.75 + 4.0

	health_bar_bg.size = Vector2(width, height)
	health_bar_bg.position = Vector2(-width * 0.5, below)
	health_bar_bg.color = Color(Palette.INK, 0.85)

	health_bar_fill.position = Vector2(1.0, 1.0)
	health_bar_fill.size = Vector2(width - 2.0, height - 2.0)
	health_bar_fill.color = Palette.BLOOD
	bar_full_width = health_bar_fill.size.x

func update_health_bar() -> void:
	if not health_bar_fill or bar_full_width <= 0.0:
		return

	if health_bar_bg:
		health_bar_bg.modulate.a = 1.0

	var percent: float = clampf(current_health / maxf(max_health, 0.001), 0.0, 1.0)
	var tween := health_bar_fill.create_tween()
	tween.tween_property(health_bar_fill, "size:x", bar_full_width * percent, 0.12).set_ease(Tween.EASE_OUT)

func die() -> void:
	GameManager.count_enemy_killed()
	Audio.play(Audio.ID_ENEMY_DIE)
	if is_dying:
		return
	is_dying = true

	remove_from_group("enemies")
	remove_from_group("damageable")
	_spread_burn()
	set_deferred("monitoring", false)
	died.emit(self)

	FX.impact(global_position, Vector2.ZERO, trail_colors[0] if not trail_colors.is_empty() else FX.COLOR_DAMAGE, 1.6)
	FX.ring_burst(global_position, Color(1.0, 1.0, 1.0, 0.8), 6.0, 66.0, 0.3, 5.0)
	FX.shake(4.0)
	FX.hitstop(0.05, 0.08)

	_spawn_loot()
	_relic_kill_effects()

	if enemy_data:
		if enemy_data.explode_on_death:
			_explode()
		if enemy_data.split_data and enemy_data.split_count > 0:
			spawn_enemies_from_data(enemy_data.split_data, enemy_data.split_count, 46.0)

	if health_bar_bg:
		health_bar_bg.visible = false
	if _shadow:
		_shadow.visible = false

	var visual := _visual()
	if visual:
		var tween := visual.create_tween()
		tween.set_parallel(true)
		tween.tween_property(visual, "scale", _visual_rest_scale() * Vector2(1.5, 0.2), 0.22).set_ease(Tween.EASE_OUT)
		tween.tween_property(visual, "modulate:a", 0.0, 0.22)
		await tween.finished
	else:
		await get_tree().create_timer(0.2).timeout

	queue_free()

func _spawn_loot() -> void:
	if not enemy_data:
		return

	var scene_root := get_tree().current_scene
	if not scene_root:
		return

	var scene: PackedScene = pickup_scene if pickup_scene else DEFAULT_PICKUP_SCENE
	if not scene:
		return

	var luck: float = 0.0
	if player:
		var stats = player.get_node_or_null("PlayerStats")
		if stats:
			luck = stats.luck

	var drops: Array = []
	if enemy_data.drop_table:
		drops = enemy_data.drop_table.roll(luck)

	for drop in drops:
		var pickup = scene.instantiate()
		pickup.item = drop["item"]
		pickup.count = drop["count"]
		pickup.global_position = global_position
		if pickup.has_method("pop_out"):
			pickup.pop_out()
		# Deferred, weil der Tod aus einem Physik-Callback kommen kann.
		scene_root.add_child.call_deferred(pickup)

## Bomber: Explosion beim Tod, trifft nur den Spieler.
func _explode() -> void:
	var radius: float = enemy_data.explosion_radius
	FX.ring_burst(global_position, Palette.EMBER, 14.0, radius, 0.45, 11.0)
	FX.hit_spark(global_position, Palette.GOLD, 20, Vector2.ZERO, TAU, radius * 0.55)
	FX.light_flash(global_position, Palette.EMBER, 3.2, radius / 110.0, 0.32)
	FX.shake(10.0)
	FX.hitstop(0.07, 0.1)

	if not player or not is_instance_valid(player):
		return
	if global_position.distance_to(player.global_position) > radius:
		return
	var health = player.get_node_or_null("PlayerHealth")
	if health and health.has_method("take_damage"):
		health.take_damage(enemy_data.explosion_damage, global_position)

## Radius für die Ziel-Markierung, aus der Sprite-Größe abgeleitet.
func get_visual_radius() -> float:
	if _symbol:
		return _symbol.symbol_size + 8.0
	if sprite and sprite.texture:
		var texture_size: Vector2 = sprite.texture.get_size() * base_scale.abs()
		return maxf(texture_size.x, texture_size.y) * 0.5 + 6.0
	return 26.0

## Wird vom WeaponController gesetzt. Ohne eigenes outline_material bleibt das
## Material der Szene erhalten - vorher wurde es hier fälschlich gelöscht.
func set_targeted(is_target: bool) -> void:
	if not sprite:
		return
	if is_target and outline_material:
		sprite.material = outline_material
	else:
		sprite.material = _base_material
