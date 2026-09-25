extends Node
class_name PlayerHealth

## Leben wie in Isaac: gezählt wird in halben Herzen.
##
##   Rote Herzen   - sitzen in Herzcontainern. Ein leerer Container bleibt
##                   stehen und kann wieder aufgefüllt werden.
##   Seelenherzen  - (blau) liegen hinter den Containern, fangen Treffer
##                   zuerst ab und sind weg, sobald sie verbraucht sind.
##
## Tot ist der Held, wenn weder rote noch blaue Hälften übrig sind.

signal hearts_changed(red: int, red_max: int, soul: int)
signal damaged(halves: int)
signal healed(halves: int)
signal died

## Obergrenze für Container plus Seelenherzen zusammen, in ganzen Herzen.
const MAX_HEARTS := 12
## So viel alter Schaden bzw. alte Heilung entspricht einem halben Herzen.
## Gegnerschaden, Lebensraub und Regeneration rechnen weiter in Punkten
## und werden hier in Herzhälften übersetzt.
const HALF_HEART_VALUE := 30.0
## Mehr als so viele Hälften nimmt ein einzelner Treffer nie.
const MAX_HALVES_PER_HIT := 4

@export var invuln_time: float = 0.9
@export var death_restart_delay: float = 1.5
@export var blink_interval: float = 0.09

## Alles in halben Herzen.
var red: int = 6
var red_max: int = 6
var soul: int = 0
## Kristallherz (Relikt Kristallpanzer): Schild über allen Herzen, max. 1 Herz.
var shield: int = 0
const MAX_SHIELD := 2
var invuln_timer: float = 0.0
var is_dead: bool = false

var _body: Node2D
var _sprite: CanvasItem
var _initialized: bool = false
var _blink_timer: float = 0.0
## Sammelt Lebensraub und Regeneration, bis ein halbes Herz voll ist.
var _heal_buffer: float = 0.0

func _ready() -> void:
	_body = get_parent() as Node2D
	if _body:
		_sprite = _body.get_node_or_null("RigView/Rig/FirstBody")

## `containers` und `soul_hearts` in ganzen Herzen. Beim ersten Aufruf startet
## der Held voll, danach werden nur die Container angepasst.
func setup(containers: int, soul_hearts: int = 0) -> void:
	red_max = clampi(containers, 0, MAX_HEARTS) * 2
	if not _initialized:
		red = red_max
		soul = clampi(soul_hearts * 2, 0, MAX_HEARTS * 2 - red_max)
		_initialized = true
		# Ohne ein einziges Herz wäre der Held sofort tot.
		if red + soul <= 0:
			soul = 2
	else:
		red = mini(red, red_max)
		soul = mini(soul, MAX_HEARTS * 2 - red_max)
	_emit()

func _process(delta: float) -> void:
	_tick_regen(delta)

	if invuln_timer > 0.0:
		invuln_timer -= delta
		_blink_timer += delta
		if _sprite:
			_sprite.modulate.a = 0.35 if fmod(_blink_timer, blink_interval * 2.0) < blink_interval else 1.0
		if invuln_timer <= 0.0 and _sprite:
			_sprite.modulate.a = 1.0

# --- Abfragen --------------------------------------------------------------

func get_containers() -> int:
	return red_max / 2

func is_red_full() -> bool:
	return red >= red_max

func can_add_soul() -> bool:
	return red_max + soul < MAX_HEARTS * 2

func can_add_container() -> bool:
	return red_max < MAX_HEARTS * 2

func is_invulnerable() -> bool:
	return invuln_timer > 0.0 or is_dead or DevMode.god_mode

func set_invulnerable(duration: float) -> void:
	invuln_timer = maxf(invuln_timer, duration)

## Schadensstufen: 1-30 = ½ Herz, 31-60 = 1, 61-90 = 1½, ab 91 = 2 (Deckel).
static func damage_to_halves(amount: float) -> int:
	return clampi(int(ceil(amount / HALF_HEART_VALUE - 0.001)), 1, MAX_HALVES_PER_HIT)

func _get_stats() -> Node:
	return _body.get_node_or_null("PlayerStats") if _body else null

func _emit() -> void:
	hearts_changed.emit(red, red_max, soul)

# --- Heilen ----------------------------------------------------------------

func _tick_regen(delta: float) -> void:
	if is_dead or is_red_full():
		return
	var stats = _get_stats()
	if not stats or stats.health_regen <= 0.0:
		return
	heal_silent(stats.health_regen * delta)

## Heilung ohne Effekte - für Lebensraub und Regeneration. Kleine Beträge
## sammeln sich, bis ein halbes Herz zusammen ist.
func heal_silent(amount: float) -> void:
	if is_dead or amount <= 0.0 or is_red_full():
		_heal_buffer = 0.0
		return
	_heal_buffer += amount
	var halves: int = int(_heal_buffer / HALF_HEART_VALUE)
	if halves <= 0:
		return
	_heal_buffer -= float(halves) * HALF_HEART_VALUE
	red = mini(red + halves, red_max)
	_emit()

## Heilung aus Fähigkeiten, in alten Lebenspunkten - mindestens ein halbes Herz.
func heal(amount: float) -> void:
	if amount <= 0.0:
		return
	heal_hearts(maxi(int(round(amount / HALF_HEART_VALUE)), 1))

## Füllt rote Container auf. Gibt zurück, wie viele Hälften tatsächlich
## ankamen - ein voller Held nimmt kein rotes Herz auf.
func heal_hearts(halves: int) -> int:
	if is_dead or halves <= 0:
		return 0
	var gained: int = mini(halves, red_max - red)
	if gained <= 0:
		return 0
	red += gained
	_emit()
	healed.emit(gained)
	var origin: Vector2 = _body.global_position if _body else Vector2.ZERO
	FX.floating_text(origin + Vector2(0.0, -46.0), _halves_text(gained), FX.COLOR_HEAL, 20, 46.0)
	FX.ring_burst(origin, FX.COLOR_HEAL, 10.0, 70.0, 0.4, 5.0)
	return gained

## Seelenherzen kommen oben drauf, solange Platz ist.
func add_soul_hearts(halves: int) -> int:
	if is_dead or halves <= 0:
		return 0
	var gained: int = mini(halves, MAX_HEARTS * 2 - red_max - soul)
	if gained <= 0:
		return 0
	soul += gained
	_emit()
	var origin: Vector2 = _body.global_position if _body else Vector2.ZERO
	FX.floating_text(origin + Vector2(0.0, -46.0), _halves_text(gained), Palette.AZURE, 20, 46.0)
	FX.ring_burst(origin, Palette.AZURE, 10.0, 70.0, 0.4, 5.0)
	return gained

## Kristallherz auffüllen (pro Raum ½ nach).
func add_shield(halves: int) -> void:
	if is_dead or halves <= 0:
		return
	shield = mini(shield + halves, MAX_SHIELD)
	_emit()

## Container weg (Glaskanone). Bleibt nichts übrig, rettet ein Seelenherz.
func remove_container(count: int = 1) -> void:
	red_max = maxi(red_max - count * 2, 0)
	red = mini(red, red_max)
	if red + soul <= 0:
		soul = 2
	_emit()

## Ein neuer Container kommt gefüllt dazu (wie in Isaac).
func add_container(count: int = 1) -> void:
	if is_dead or count <= 0:
		return
	var added: int = mini(count * 2, MAX_HEARTS * 2 - red_max)
	if added <= 0:
		return
	red_max += added
	red += added
	# Container verdrängen Seelenherzen, wenn das Limit erreicht ist.
	soul = mini(soul, MAX_HEARTS * 2 - red_max)
	_emit()

static func _halves_text(halves: int) -> String:
	if halves % 2 == 0:
		return "+%d Herz" % (halves / 2) if halves == 2 else "+%d Herzen" % (halves / 2)
	if halves == 1:
		return "+½ Herz"
	return "+%d½ Herzen" % (halves / 2)

# --- Schaden ---------------------------------------------------------------

## Schaden in alten Punkten - Rüstung zieht ab, der Rest wird in Herzen umgerechnet.
func take_damage(amount: float, from_position: Vector2 = Vector2.ZERO) -> void:
	if is_dead or amount <= 0.0 or is_invulnerable():
		return
	var stats = _get_stats()
	if _try_dodge(stats):
		return
	var final_amount: float = amount
	if stats:
		final_amount = maxf(1.0, amount - stats.armor)
		_apply_thorns(stats)
	_apply_hit(damage_to_halves(final_amount), from_position)

## Schaden direkt in halben Herzen - für Fallen wie Stachelkisten.
func take_hearts_damage(halves: int, from_position: Vector2 = Vector2.ZERO) -> void:
	if is_dead or halves <= 0 or is_invulnerable():
		return
	_apply_hit(halves, from_position)

func _try_dodge(stats: Node) -> bool:
	if not stats or randf() >= clampf(stats.dodge_chance, 0.0, 1.0):
		return false
	var origin_position: Vector2 = _body.global_position if _body else Vector2.ZERO
	invuln_timer = maxf(invuln_timer, 0.25)
	FX.floating_text(origin_position + Vector2(0.0, -46.0), "Ausgewichen", Palette.TEAL, 17, 40.0)
	FX.ring_burst(origin_position, Palette.TEAL, 8.0, 52.0, 0.25, 4.0)
	return true

## Seelenherzen fangen zuerst ab, danach leeren sich die roten Container.
func _apply_hit(halves: int, from_position: Vector2) -> void:
	var origin_position: Vector2 = _body.global_position if _body else Vector2.ZERO

	# Reihenfolge: Kristallherz, dann Seelenherzen, dann Rot.
	var from_shield: int = mini(halves, shield)
	shield -= from_shield
	var rest: int = halves - from_shield
	var from_soul: int = mini(rest, soul)
	soul -= from_soul
	red = maxi(red - (rest - from_soul), 0)
	if RunState.has_relic("gold_greed") and RunState.gold > 0:
		RunState.add_gold(-mini(3, RunState.gold))

	invuln_timer = invuln_time
	_blink_timer = 0.0

	_emit()
	damaged.emit(halves)

	var hurt_color: Color = Palette.TEAL if from_shield == halves else (Palette.AZURE if from_shield + from_soul == halves else FX.COLOR_HURT)
	FX.floating_text(origin_position + Vector2(0.0, -46.0), "-" + _halves_text(halves).substr(1), hurt_color, 20, 40.0)
	FX.hit_spark(origin_position, hurt_color, 10)
	FX.shake(7.0)
	FX.hitstop(0.09, 0.05)
	Audio.play(Audio.ID_PLAYER_HURT)
	FX.screen_flash(Color(Palette.BLOOD, 0.28), 0.3)
	if _sprite:
		FX.flash(_sprite, Color(8.0, 1.5, 1.5), 0.14)

	if from_position != Vector2.ZERO and _body and _body.has_method("apply_knockback"):
		_body.apply_knockback(from_position.direction_to(origin_position), 260.0)

	if red + soul <= 0:
		if RunState.has_relic("rebirth") and not RunState.rebirth_used:
			_rebirth()
			return
		_die()

## Wiedergeburt: einmal pro Lauf mit zwei roten Herzen wieder aufstehen.
func _rebirth() -> void:
	RunState.rebirth_used = true
	red_max = maxi(red_max, 4)
	red = 4
	invuln_timer = 2.0
	_emit()
	var origin: Vector2 = _body.global_position if _body else Vector2.ZERO
	FX.floating_text(origin + Vector2(0.0, -80.0), "Wiedergeburt!", Palette.GOLD, 26, 60.0)
	FX.ring_burst(origin, Palette.GOLD, 10.0, 220.0, 0.6, 10.0)
	FX.screen_flash(Color(1.0, 0.9, 0.6, 0.5), 0.5)

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
