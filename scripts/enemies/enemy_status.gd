extends RefCounted
class_name EnemyStatus

## Zustände eines Gegners durch Waffen-Upgrades: Brand, Frost, Gift, Blutung.
## Gehört zu genau einem Enemy und wird von dessen _process getickt.
## Schaden über Zeit wird gesammelt und alle 0,5 s als eine Zahl ausgezahlt,
## damit nicht jedes Frame eine Schadenszahl aufpoppt.

const TICK := 0.5

var burn_time: float = 0.0
var burn_dps: float = 0.0
var slow_time: float = 0.0
var slow_factor: float = 1.0
var freeze_time: float = 0.0
var frost_hits: int = 0
var poison_stacks: int = 0
var poison_time: float = 0.0
var poison_dps_per_stack: float = 3.0
var bleed: float = 0.0
## Brand-Affinität: beim Tod springt der Brand auf einen Nachbarn über.
var burn_spreads: bool = false

var _owner: Node2D
var _pending: float = 0.0
var _tick_timer: float = TICK

func _init(owner: Node2D) -> void:
	_owner = owner

## Tempo-Faktor für die Bewegung: eingefroren 0, verlangsamt < 1.
func speed_factor() -> float:
	if freeze_time > 0.0:
		return 0.0
	return slow_factor if slow_time > 0.0 else 1.0

func is_active() -> bool:
	return burn_time > 0.0 or slow_time > 0.0 or freeze_time > 0.0 or poison_time > 0.0

func apply_burn(dps: float, duration: float) -> void:
	burn_dps = maxf(burn_dps, dps)
	burn_time = maxf(burn_time, duration)

## `freeze_after` > 0: so viele Frosttreffer frieren für `freeze_duration` ein.
func apply_slow(factor: float, duration: float, freeze_after: int = 0, freeze_duration: float = 1.0) -> void:
	slow_factor = minf(slow_factor if slow_time > 0.0 else 1.0, factor)
	slow_time = maxf(slow_time, duration)
	if freeze_after <= 0:
		return
	frost_hits += 1
	if frost_hits >= freeze_after:
		frost_hits = 0
		freeze_time = freeze_duration
		FX.ring_burst(_owner.global_position, Palette.TEAL, 6.0, 40.0, 0.3, 4.0)

func apply_poison(max_stacks: int, dps_per_stack: float = 3.0) -> void:
	poison_stacks = mini(poison_stacks + 1, max_stacks)
	poison_dps_per_stack = dps_per_stack
	poison_time = 4.0

## Baut Blutung auf. Gibt true zurück, wenn die Leiste voll war und platzt.
func add_bleed(amount: float, threshold: float) -> bool:
	bleed += amount
	if bleed < threshold:
		return false
	bleed = 0.0
	return true

## Liefert den Schaden, der jetzt ausgezahlt werden soll (0 = nichts).
func tick(delta: float) -> float:
	if burn_time > 0.0:
		burn_time -= delta
		_pending += burn_dps * delta
	if poison_time > 0.0:
		poison_time -= delta
		_pending += poison_dps_per_stack * float(poison_stacks) * delta
		if poison_time <= 0.0:
			poison_stacks = 0
	slow_time = maxf(slow_time - delta, 0.0)
	freeze_time = maxf(freeze_time - delta, 0.0)

	_tick_timer -= delta
	if _tick_timer > 0.0:
		return 0.0
	_tick_timer = TICK
	var amount := _pending
	_pending = 0.0
	return amount

## Farbe für das Einfärben des Gegners, solange ein Zustand wirkt.
func tint() -> Color:
	if freeze_time > 0.0:
		return Color(0.6, 0.9, 1.3)
	if burn_time > 0.0:
		return Color(1.3, 0.75, 0.55)
	if poison_time > 0.0:
		return Color(0.75, 1.25, 0.6)
	if slow_time > 0.0:
		return Color(0.75, 0.9, 1.25)
	return Color.WHITE
