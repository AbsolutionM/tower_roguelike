extends Area2D
class_name Chest

## Truhe als alternative Loot-Quelle. Ohne Sprite wird sie prozedural gezeichnet.

@export var drop_table: DropTable
@export var drop_items: Array[ItemData] = []
@export var drop_counts: Array[int] = []
@export var pickup_scene: PackedScene
@export var sprite: Sprite2D
@export var opened_texture: Texture2D
@export var chest_color: Color = Palette.GOLD.darkened(0.35)
@export var box_size: Vector2 = Vector2(34.0, 26.0)

var is_opened: bool = false

var _use_sprite: bool = false
var _time: float = 0.0
var _lid_lift: float = 0.0

func _ready() -> void:
	add_to_group("chests")
	body_entered.connect(_on_body_entered)

	if not sprite:
		sprite = get_node_or_null("Sprite2D")
	_use_sprite = sprite != null and sprite.texture != null
	if sprite and not _use_sprite:
		sprite.visible = false

	var shadow := BlobShadow.new()
	shadow.radius = box_size.x * 0.5
	shadow.position = Vector2(0.0, box_size.y * 0.5)
	add_child(shadow)

func _process(delta: float) -> void:
	_time += delta
	if not _use_sprite:
		queue_redraw()

func _draw() -> void:
	if _use_sprite:
		return

	var half := box_size * 0.5
	var bob: float = 0.0 if is_opened else sin(_time * 2.5) * 1.2
	var body_color: Color = chest_color.darkened(0.3) if is_opened else chest_color
	var lid_color: Color = body_color.lightened(0.15)

	var base_rect := Rect2(-half.x, -half.y * 0.1 + bob, box_size.x, half.y * 1.1)
	draw_rect(base_rect, body_color)
	draw_rect(base_rect, Color(Palette.INK, 0.6), false, 2.0)

	var lid_rect := Rect2(-half.x, -half.y + bob - _lid_lift, box_size.x, half.y * 0.85)
	draw_rect(lid_rect, lid_color)
	draw_rect(lid_rect, Color(Palette.INK, 0.6), false, 2.0)

	if not is_opened:
		draw_rect(Rect2(-5.0, -half.y * 0.25 + bob, 10.0, 11.0), Palette.GOLD)
		draw_rect(Rect2(-5.0, -half.y * 0.25 + bob, 10.0, 11.0), Color(Palette.edge(Palette.GOLD), 0.8), false, 1.5)

func _on_body_entered(body: Node) -> void:
	if is_opened:
		return
	if body.is_in_group("player"):
		open_chest()

func open_chest() -> void:
	is_opened = true

	if sprite and opened_texture:
		sprite.texture = opened_texture

	var tween := create_tween()
	tween.tween_property(self, "_lid_lift", 12.0, 0.16).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)

	FX.ring_burst(global_position, Palette.AMBER, 8.0, 74.0, 0.4, 6.0)
	FX.hit_spark(global_position, Palette.AMBER, 12, Vector2.UP, PI, 60.0)
	FX.shake(4.0)

	for drop in _roll_drops():
		_spawn_pickup(drop["item"], drop["count"])

func _roll_drops() -> Array:
	if drop_table:
		return drop_table.roll()

	var results: Array = []
	for i in drop_items.size():
		var item := drop_items[i]
		if not item:
			continue
		var count: int = drop_counts[i] if i < drop_counts.size() else 1
		results.append({"item": item, "count": count})
	return results

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
