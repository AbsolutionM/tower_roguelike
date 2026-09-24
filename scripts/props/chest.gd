extends Area2D
class_name Chest

## Truhen wie in Isaac. Ohne Sprite wird jede Art prozedural gezeichnet.
##
##   Holzkiste    - geht bei Berührung auf, kleine Beute.
##   Goldtruhe    - verschlossen, kostet einen Schlüssel, gute Beute.
##   Stachelkiste - geht auf, sticht aber ein halbes Herz ab. Bessere Beute.
##   Rote Truhe   - Glücksspiel: Seelenherzen und Essenz - oder ein Hinterhalt.

enum ChestType { WOOD, GOLD, SPIKED, RED }

const TYPE_NAMES := {
	ChestType.WOOD: "Holzkiste",
	ChestType.GOLD: "Goldtruhe",
	ChestType.SPIKED: "Stachelkiste",
	ChestType.RED: "Rote Truhe",
}

@export var chest_type: ChestType = ChestType.WOOD
## Würfelt die Art beim Erscheinen aus `type_weights` (Reihenfolge wie ChestType).
@export var randomize_type: bool = true
@export var type_weights: Array[float] = [58.0, 24.0, 10.0, 8.0]

@export_group("Beute")
## Holzkiste - und Rückfall für alle Arten ohne eigene Tabelle.
@export var drop_table: DropTable
@export var gold_drop_table: DropTable
@export var spiked_drop_table: DropTable
@export var red_drop_table: DropTable
@export var drop_items: Array[ItemData] = []
@export var drop_counts: Array[int] = []
@export var pickup_scene: PackedScene

@export_group("Rote Truhe")
## Chance, dass statt Beute Gegner herausspringen.
@export_range(0.0, 1.0) var red_ambush_chance: float = 0.35
@export var red_ambush_count: int = 2

@export_group("Stachelkiste")
## So viele halbe Herzen kostet das Öffnen.
@export var spike_damage_halves: int = 1

@export_group("Optik")
@export var sprite: Sprite2D
@export var opened_texture: Texture2D
@export var box_size: Vector2 = Vector2(34.0, 26.0)

var is_opened: bool = false

var _use_sprite: bool = false
var _time: float = 0.0
var _lid_lift: float = 0.0
var _jiggle: float = 0.0
## Verhindert, dass "Schlüssel nötig" jeden Frame erscheint.
var _locked_hint_cooldown: float = 0.0

func _ready() -> void:
	add_to_group("chests")
	body_entered.connect(_on_body_entered)

	if randomize_type:
		chest_type = _roll_type()

	if not sprite:
		sprite = get_node_or_null("Sprite2D")
	_use_sprite = sprite != null and sprite.texture != null
	if sprite and not _use_sprite:
		sprite.visible = false

	var shadow := BlobShadow.new()
	shadow.radius = box_size.x * 0.5
	shadow.position = Vector2(0.0, box_size.y * 0.5)
	add_child(shadow)

func _roll_type() -> ChestType:
	var total: float = 0.0
	for weight in type_weights:
		total += maxf(weight, 0.0)
	if total <= 0.0:
		return ChestType.WOOD
	var pick: float = randf() * total
	for i in type_weights.size():
		pick -= maxf(type_weights[i], 0.0)
		if pick <= 0.0:
			return i as ChestType
	return ChestType.WOOD

func get_type_name() -> String:
	return TYPE_NAMES.get(chest_type, "Truhe")

func _process(delta: float) -> void:
	_time += delta
	_locked_hint_cooldown = maxf(_locked_hint_cooldown - delta, 0.0)
	_jiggle = move_toward(_jiggle, 0.0, delta * 3.0)
	_retry_locked()
	if not _use_sprite:
		queue_redraw()

# --- Zeichnen --------------------------------------------------------------

func _body_color() -> Color:
	match chest_type:
		ChestType.GOLD:
			return Palette.GOLD
		ChestType.SPIKED:
			return Palette.STONE_LIGHT.lightened(0.1)
		ChestType.RED:
			return Palette.BLOOD.darkened(0.2)
	return Palette.EMBER.darkened(0.5)

func _band_color() -> Color:
	match chest_type:
		ChestType.GOLD:
			return Palette.AMBER
		ChestType.SPIKED:
			return Palette.MIST
		ChestType.RED:
			return Palette.GOLD.darkened(0.2)
	return Palette.EMBER.darkened(0.7)

func _draw() -> void:
	if _use_sprite:
		return

	var half := box_size * 0.5
	var bob: float = 0.0 if is_opened else sin(_time * 2.5) * 1.2
	var shake: float = sin(_time * 60.0) * 2.0 * _jiggle
	var offset := Vector2(shake, bob)
	var body_color: Color = _body_color().darkened(0.3) if is_opened else _body_color()
	var lid_color: Color = body_color.lightened(0.15)
	var band: Color = _band_color()
	var outline := Color(Palette.INK, 0.8)

	var base_rect := Rect2(Vector2(-half.x, -half.y * 0.1) + offset, Vector2(box_size.x, half.y * 1.1))
	draw_rect(base_rect, body_color)
	# Senkrechte Beschläge links und rechts.
	draw_rect(Rect2(base_rect.position + Vector2(4.0, 0.0), Vector2(4.0, base_rect.size.y)), band)
	draw_rect(Rect2(base_rect.position + Vector2(box_size.x - 8.0, 0.0), Vector2(4.0, base_rect.size.y)), band)
	draw_rect(base_rect, outline, false, 2.0)

	var lid_rect := Rect2(Vector2(-half.x, -half.y - _lid_lift) + offset, Vector2(box_size.x, half.y * 0.85))
	draw_rect(lid_rect, lid_color)
	draw_rect(Rect2(lid_rect.position + Vector2(4.0, 0.0), Vector2(4.0, lid_rect.size.y)), band.lightened(0.1))
	draw_rect(Rect2(lid_rect.position + Vector2(box_size.x - 8.0, 0.0), Vector2(4.0, lid_rect.size.y)), band.lightened(0.1))
	draw_rect(lid_rect, outline, false, 2.0)

	if chest_type == ChestType.SPIKED and not is_opened:
		_draw_spikes(lid_rect, base_rect)

	if is_opened:
		return

	var lock_rect := Rect2(Vector2(-5.0, -half.y * 0.25) + offset, Vector2(10.0, 11.0))
	match chest_type:
		ChestType.GOLD:
			# Schloss mit Schlüsselloch - hier braucht es einen Schlüssel.
			var plate := lock_rect.grow(2.0)
			draw_rect(plate, Palette.BONE)
			draw_rect(plate, outline, false, 1.5)
			draw_rect(Rect2(plate.get_center() + Vector2(-1.5, -3.0), Vector2(3.0, 3.0)), Palette.INK)
			draw_rect(Rect2(plate.get_center() + Vector2(-0.75, 0.0), Vector2(1.5, 4.0)), Palette.INK)
		ChestType.RED:
			draw_rect(lock_rect, Palette.GOLD)
			draw_rect(Rect2(lock_rect.get_center() - Vector2(2.0, 2.0), Vector2(4.0, 4.0)), Palette.INK)
			draw_rect(lock_rect, Color(Palette.edge(Palette.GOLD), 0.8), false, 1.5)
		_:
			draw_rect(lock_rect, Palette.GOLD)
			draw_rect(lock_rect, Color(Palette.edge(Palette.GOLD), 0.8), false, 1.5)

## Stachelreihe auf dem Deckel und an den Seiten.
func _draw_spikes(lid_rect: Rect2, base_rect: Rect2) -> void:
	var spike := Palette.BONE
	var x := lid_rect.position.x + 3.0
	while x < lid_rect.end.x - 4.0:
		draw_colored_polygon(PackedVector2Array([
			Vector2(x, lid_rect.position.y),
			Vector2(x + 5.0, lid_rect.position.y),
			Vector2(x + 2.5, lid_rect.position.y - 6.0),
		]), spike)
		x += 7.0
	for side in [-1.0, 1.0]:
		var edge_x: float = base_rect.position.x if side < 0.0 else base_rect.end.x
		var y := base_rect.position.y + 3.0
		while y < base_rect.end.y - 4.0:
			draw_colored_polygon(PackedVector2Array([
				Vector2(edge_x, y),
				Vector2(edge_x, y + 5.0),
				Vector2(edge_x + side * 5.0, y + 2.5),
			]), spike)
			y += 7.0

# --- Öffnen ----------------------------------------------------------------

func _on_body_entered(body: Node) -> void:
	if is_opened or not body.is_in_group("player"):
		return

	match chest_type:
		ChestType.GOLD:
			if not RunState.spend_key():
				_show_locked()
				return
			FX.floating_text(global_position + Vector2(0.0, -40.0), "-1 Schlüssel", Palette.BONE, 16, 30.0)
		ChestType.SPIKED:
			var health = body.get_node_or_null("PlayerHealth")
			if health and health.has_method("take_hearts_damage"):
				health.take_hearts_damage(spike_damage_halves, global_position)
	open_chest()

## Wer auf der Goldtruhe steht und dabei einen Schlüssel aufsammelt, soll
## nicht erst weg- und wieder hinlaufen müssen.
func _retry_locked() -> void:
	if is_opened or chest_type != ChestType.GOLD or RunState.keys <= 0:
		return
	for body in get_overlapping_bodies():
		if body.is_in_group("player"):
			_on_body_entered(body)
			return

func _show_locked() -> void:
	_jiggle = 1.0
	if _locked_hint_cooldown > 0.0:
		return
	_locked_hint_cooldown = 1.2
	FX.floating_text(global_position + Vector2(0.0, -40.0), "Schlüssel nötig", Palette.BONE, 16, 30.0)

func open_chest() -> void:
	if is_opened:
		return
	is_opened = true

	if sprite and opened_texture:
		sprite.texture = opened_texture

	var tween := create_tween()
	tween.tween_property(self, "_lid_lift", 12.0, 0.16).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)

	var burst: Color = _body_color().lightened(0.3)
	FX.ring_burst(global_position, burst, 8.0, 74.0, 0.4, 6.0)
	FX.hit_spark(global_position, burst, 12, Vector2.UP, PI, 60.0)
	FX.shake(4.0)

	if chest_type == ChestType.RED and randf() < red_ambush_chance and _spring_ambush():
		return

	for drop in _roll_drops():
		_spawn_pickup(drop["item"], drop["count"])

## Rote Truhe: Gegner springen heraus. False = im Raum gibt es keine
## Gegnerart dafür (z.B. Bossraum), dann gibt es doch Beute.
func _spring_ambush() -> bool:
	var room_controller := get_tree().get_first_node_in_group("room_controller")
	if not room_controller or not room_controller.has_method("spawn_ambush"):
		return false
	if room_controller.spawn_ambush(global_position, red_ambush_count) <= 0:
		return false
	FX.floating_text(global_position + Vector2(0.0, -46.0), "Hinterhalt!", Palette.BLOOD, 20, 40.0)
	FX.screen_flash(Color(Palette.BLOOD, 0.25), 0.35)
	FX.shake(8.0)
	return true

func _table_for_type() -> DropTable:
	var table: DropTable = null
	match chest_type:
		ChestType.GOLD:
			table = gold_drop_table
		ChestType.SPIKED:
			table = spiked_drop_table
		ChestType.RED:
			table = red_drop_table
	return table if table else drop_table

func _roll_drops() -> Array:
	var table := _table_for_type()
	if table:
		return table.roll(_player_luck())

	var results: Array = []
	for i in drop_items.size():
		var item := drop_items[i]
		if not item:
			continue
		var count: int = drop_counts[i] if i < drop_counts.size() else 1
		results.append({"item": item, "count": count})
	return results

func _player_luck() -> float:
	var player := get_tree().get_first_node_in_group("player")
	if not player:
		return 0.0
	var stats = player.get_node_or_null("PlayerStats")
	return stats.luck if stats else 0.0

func _spawn_pickup(item: ItemData, count: int) -> void:
	if not item or not pickup_scene:
		return
	var scene_root := get_tree().current_scene
	if not scene_root:
		return

	var pickup = pickup_scene.instantiate()
	pickup.item = item
	pickup.count = count
	pickup.global_position = global_position
	if pickup.has_method("pop_out"):
		pickup.pop_out()
	scene_root.add_child.call_deferred(pickup)
