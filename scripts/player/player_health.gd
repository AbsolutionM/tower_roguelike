extends Node
class_name PlayerHealth

signal health_changed(current: float, maximum: float)
signal damaged(amount: float)
signal healed(amount: float)
signal died

@export var invuln_time: float = 0.9
@export var death_restart_delay: float = 1.5
@export var blink_interval: float = 0.09

var max_health: float = 100.0
var current_health: float = 100.0
var invuln_timer: float = 0.0
var is_dead: bool = false

var _body: Node2D
var _sprite: CanvasItem
var _initialized: bool = false
var _blink_timer: float = 0.0

func _ready() -> void:
	_body = get_parent() as Node2D
	if _body:
		_sprite = _body.get_node_or_null("FirstBody")

func setup(maximum: float) -> void:
	max_health = maxf(maximum, 1.0)
	if not _initialized:
		current_health = max_health
		_initialized = true
	else:
		current_health = minf(current_health, max_health)
	health_changed.emit(current_health, max_health)

func _process(delta: float) -> void:
	_tick_regen(delta)

	if invuln_timer > 0.0:
		invuln_timer -= delta
		_blink_timer += delta
		if _sprite:
			_sprite.modulate.a = 0.35 if fmod(_blink_timer, blink_interval * 2.0) < blink_interval else 1.0
		if invuln_timer <= 0.0 and _sprite:
			_sprite.modulate.a = 1.0

func _get_stats() -> Node:
	return _body.get_node_or_null("PlayerStats") if _body else null

func _tick_regen(delta: float) -> void:
	if is_dead or current_health >= max_health:
		return
	var stats = _get_stats()
	if not stats or stats.health_regen <= 0.0:
		return
	current_health = minf(current_health + stats.health_regen * delta, max_health)
	health_changed.emit(current_health, max_health)

## Heilung ohne Effekte - für Lebensraub, der pro Treffer auslöst.
func heal_silent(amount: float) -> void:
	if is_dead or amount <= 0.0 or current_health >= max_health:
		return
	current_health = minf(current_health + amount, max_health)
	health_changed.emit(current_health, max_health)

func is_invulnerable() -> bool:
	return invuln_timer > 0.0 or is_dead

func set_invulnerable(duration: float) -> void:
	invuln_timer = maxf(invuln_timer, duration)

func take_damage(amount: float, from_position: Vector2 = Vector2.ZERO) -> void:
	if is_dead or amount <= 0.0 or is_invulnerable():
		return

	var origin_position: Vector2 = _body.global_position if _body else Vector2.ZERO
	var stats = _get_stats()

	if stats and randf() < clampf(stats.dodge_chance, 0.0, 1.0):
		invuln_timer = maxf(invuln_timer, 0.25)
		FX.floating_text(origin_position + Vector2(0.0, -46.0), "Ausgewichen", Palette.TEAL, 17, 40.0)
		FX.ring_burst(origin_position, Palette.TEAL, 8.0, 52.0, 0.25, 4.0)
		return

	var final_amount: float = amount
	if stats:
		final_amount = maxf(1.0, amount - stats.armor)
		_apply_thorns(stats)

	current_health = maxf(current_health - final_amount, 0.0)
	invuln_timer = invuln_time
	_blink_timer = 0.0

	health_changed.emit(current_health, max_health)
	damaged.emit(final_amount)

	FX.damage_number(origin_position + Vector2(0.0, -46.0), final_amount, false, FX.COLOR_HURT)
	FX.hit_spark(origin_position, FX.COLOR_HURT, 10)
	FX.shake(7.0)
	FX.hitstop(0.09, 0.05)
	Audio.play(Audio.ID_PLAYER_HURT)
	FX.screen_flash(Color(Palette.BLOOD, 0.28), 0.3)
	if _sprite:
		FX.flash(_sprite, Color(8.0, 1.5, 1.5), 0.14)

	if from_position != Vector2.ZERO and _body and _body.has_method("apply_knockback"):
		_body.apply_knockback(from_position.direction_to(origin_position), 260.0)

	if current_health <= 0.0:
		_die()

## Dornen: ein Teil des Schadens geht an nahe Gegner zurück.
func _apply_thorns(stats: Node) -> void:
	if stats.thorns <= 0.0 or not _body:
		return
	var origin: Vector2 = _body.global_position
	FX.ring_burst(origin, Palette.GOLD, 10.0, 110.0, 0.3, 5.0)
	for enemy in _body.get_tree().get_nodes_in_group("enemies"):
		if not is_instance_valid(enemy):
			continue
		if origin.distance_to(enemy.global_position) > 110.0:
			continue
		if enemy.has_method("take_damage"):
			enemy.take_damage(stats.thorns, origin, false)

func heal(amount: float) -> void:
	if is_dead or amount <= 0.0:
		return
	current_health = minf(current_health + amount, max_health)
	health_changed.emit(current_health, max_health)
	healed.emit(amount)
	var origin: Vector2 = _body.global_position if _body else Vector2.ZERO
	FX.floating_text(origin + Vector2(0.0, -46.0), "+" + str(int(round(amount))), FX.COLOR_HEAL, 20, 46.0)
	FX.ring_burst(origin, FX.COLOR_HEAL, 10.0, 70.0, 0.4, 5.0)

func _die() -> void:
	if is_dead:
		return
	is_dead = true
	died.emit()

	var origin: Vector2 = _body.global_position if _body else Vector2.ZERO
	FX.hitstop(0.35, 0.12)
	FX.shake(16.0)
	FX.ring_burst(origin, Palette.BLOOD, 10.0, 200.0, 0.6, 10.0)
	FX.hit_spark(origin, Palette.BLOOD, 18, Vector2.ZERO, TAU, 90.0)
	Audio.play(Audio.ID_PLAYER_DIE)
	FX.screen_flash(Color(Palette.BLOOD, 0.55), 0.6)

	if _sprite:
		_sprite.modulate.a = 1.0
		var tween := _sprite.create_tween()
		tween.set_parallel(true)
		tween.tween_property(_sprite, "modulate:a", 0.0, 0.8)
		tween.tween_property(_sprite, "rotation", 1.6, 0.8)

	await get_tree().create_timer(death_restart_delay).timeout
	if not is_inside_tree():
		return
	RunState.end_run(true)
	get_tree().change_scene_to_file("res://scenes/ui/run_end.tscn")
