extends Enemy
class_name BossEnemy

## Boss mit drei Phasen. Bei 66% und 33% Leben wechselt er die Phase:
## kurz unverwundbar, Schockwelle, Adds, danach schneller und aggressiver.

signal phase_changed(phase: int)

const PHASE_THRESHOLDS := [0.66, 0.33]

var phase: int = 0
var special_timer: float = 0.0
var invulnerable: bool = false
var _special_toggle: bool = false
var _invuln_timer: float = 0.0

func _ready() -> void:
	super()
	add_to_group("bosses")
	special_timer = _special_interval()
	contact_timer = 1.2
	if sprite:
		FX.light_flash(global_position, Palette.BLOOD, 3.0, 2.4, 0.6)

func _special_interval() -> float:
	var base: float = enemy_data.special_interval if enemy_data else 3.4
	return maxf(base - phase * 0.6, 1.1)

func _process(delta: float) -> void:
	super(delta)
	if is_dying:
		return

	if invulnerable:
		_invuln_timer -= delta
		if _invuln_timer <= 0.0:
			invulnerable = false
		return

	special_timer -= delta
	if special_timer <= 0.0:
		special_timer = _special_interval()
		_do_special()

## Bosse werden kaum zurückgestoßen.
func apply_knockback(direction: Vector2, force: float) -> void:
	super(direction, force * 0.12)

func take_damage(amount: float, from_position: Vector2 = Vector2.ZERO, crit: bool = false) -> void:
	if invulnerable or is_dying:
		return
	super(amount, from_position, crit)
	if not is_dying:
		_check_phase()

func _check_phase() -> void:
	var ratio: float = current_health / maxf(max_health, 0.001)
	var target_phase: int = 0
	for i in PHASE_THRESHOLDS.size():
		if ratio <= float(PHASE_THRESHOLDS[i]):
			target_phase = i + 1
	if target_phase > phase:
		_enter_phase(target_phase)

func _enter_phase(new_phase: int) -> void:
	phase = new_phase
	phase_changed.emit(phase)

	invulnerable = true
	_invuln_timer = 1.0
	knockback_velocity = Vector2.ZERO

	FX.ring_burst(global_position, Palette.BLOOD, 20.0, 320.0, 0.7, 16.0)
	FX.ring_burst(global_position, Color(1.0, 1.0, 1.0, 0.8), 10.0, 220.0, 0.5, 8.0)
	FX.light_flash(global_position, Palette.BLOOD, 4.0, 3.0, 0.5)
	FX.screen_flash(Color(Palette.BLOOD, 0.35), 0.45)
	FX.shake(16.0)
	FX.hitstop(0.22, 0.1)
	FX.zoom_punch(0.07)

	if sprite:
		FX.flash(sprite, Color(9.0, 4.0, 4.0), 0.5)

	move_speed *= 1.22
	_summon_minions()

func _do_special() -> void:
	_special_toggle = not _special_toggle
	if phase >= 2:
		_projectile_spray()
		_summon_minions()
	elif _special_toggle:
		_projectile_spray()
	else:
		_summon_minions()

func _projectile_spray() -> void:
	if not enemy_data or not enemy_data.projectile_scene:
		return
	var scene_root := get_tree().current_scene
	if not scene_root:
		return

	var count: int = maxi(enemy_data.spray_projectiles, 3)
	var offset: float = randf() * TAU

	FX.ring_burst(global_position, Palette.ROSE, 12.0, 90.0, 0.3, 6.0)
	FX.shake(5.0)

	for i in count:
		var angle: float = offset + TAU * float(i) / float(count)
		var direction := Vector2(cos(angle), sin(angle))
		var projectile = enemy_data.projectile_scene.instantiate()
		projectile.hostile = true
		projectile.global_position = global_position + direction * 30.0
		scene_root.add_child.call_deferred(projectile)
		projectile.setup.call_deferred(
			direction,
			enemy_data.projectile_speed,
			enemy_data.projectile_damage,
			0,
			Palette.ROSE,
			false
		)

func _summon_minions() -> void:
	if not enemy_data or not enemy_data.minion_data:
		return
	FX.ring_burst(global_position, Palette.VIOLET, 14.0, 140.0, 0.4, 6.0)
	spawn_enemies_from_data(enemy_data.minion_data, enemy_data.minions_per_wave, 110.0)

func die() -> void:
	if is_dying:
		return
	FX.screen_flash(Color(Palette.AMBER, 0.5), 0.8)
	FX.hitstop(0.3, 0.08)
	FX.zoom_punch(0.09)
	for i in 4:
		FX.ring_burst(
			global_position,
			Color(1.0, 0.6 + 0.1 * i, 0.3),
			10.0,
			160.0 + 70.0 * i,
			0.5 + 0.12 * i,
			12.0
		)
	super()
