extends Area2D
class_name Anvil

## Amboss im Turm: zwei Sekunden darauf stehen bleiben, mit Turmfunken
## bezahlen, ein Waffen-Upgrade aus drei wählen (Grobschliff).
## Stillstand im Kampf ist der Preis - darum der Timer.

@export var cost: int = 15
@export var hold_time: float = 2.0

var _player: Node2D = null
var _progress: float = 0.0
## Nach einem Kauf erst wieder, wenn der Held den Amboss verlassen hat.
var _used_while_inside: bool = false
var _time: float = 0.0
var _hint_cooldown: float = 0.0

func _ready() -> void:
	add_to_group("room_props")
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)
	var shadow := BlobShadow.new()
	shadow.radius = 22.0
	shadow.position = Vector2(0.0, 14.0)
	add_child(shadow)

func _on_body_entered(body: Node) -> void:
	if body.is_in_group("player"):
		_player = body

func _on_body_exited(body: Node) -> void:
	if body == _player:
		_player = null
		_progress = 0.0
		_used_while_inside = false

func _process(delta: float) -> void:
	_time += delta
	_hint_cooldown = maxf(_hint_cooldown - delta, 0.0)
	if _player and not _used_while_inside:
		if RunState.sparks < cost:
			_progress = 0.0
			if _hint_cooldown <= 0.0:
				_hint_cooldown = 1.5
				FX.floating_text(global_position + Vector2(0.0, -44.0), "%d Funken nötig" % cost, Palette.AMBER, 16, 30.0)
		else:
			_progress += delta
			if _progress >= hold_time:
				_forge()
	queue_redraw()

func _forge() -> void:
	_progress = 0.0
	_used_while_inside = true
	if not RunState.spend_sparks(cost):
		return
	FX.hit_spark(global_position + Vector2(0.0, -10.0), Palette.AMBER, 14, Vector2.UP, PI, 50.0)
	FX.shake(3.0)
	Audio.play(Audio.ID_FORGE)
	RunState.upgrade_offer_requested.emit(3, false, "Amboss · Grobschliff")

func _draw() -> void:
	var metal := Palette.STONE_LIGHT.lightened(0.15)
	var edge := Color(Palette.INK, 0.85)
	# Fuß, Körper, Horn.
	draw_rect(Rect2(-10.0, 2.0, 20.0, 12.0), metal.darkened(0.3))
	draw_rect(Rect2(-18.0, -8.0, 36.0, 11.0), metal)
	draw_rect(Rect2(18.0, -8.0, 8.0, 5.0), metal)
	draw_rect(Rect2(-18.0, -8.0, 36.0, 3.0), metal.lightened(0.3))
	draw_rect(Rect2(-18.0, -8.0, 36.0, 11.0), edge, false, 2.0)
	draw_rect(Rect2(-10.0, 2.0, 20.0, 12.0), edge, false, 2.0)
	# Glut über dem Amboss, solange man es sich leisten kann.
	var affordable: bool = RunState.sparks >= cost
	var glow: Color = Color(Palette.AMBER, 0.55 + sin(_time * 4.0) * 0.2) if affordable else Color(Palette.MIST, 0.4)
	draw_rect(Rect2(-3.0, -20.0 + sin(_time * 3.0) * 2.0, 6.0, 6.0), glow)
	if _progress > 0.0:
		var ratio: float = clampf(_progress / hold_time, 0.0, 1.0)
		draw_arc(Vector2(0.0, -2.0), 30.0, -PI * 0.5, -PI * 0.5 + TAU * ratio, 32, Palette.GOLD, 4.0)
