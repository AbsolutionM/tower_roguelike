extends Area2D
class_name Harvestable

## Abbaubares Objekt (Erz, Busch, ...). Wird von Waffen getroffen wie ein Gegner,
## zählt aber nicht als "enemies" und blockiert damit den Raumfortschritt nicht.

@export var hit_points: int = 3
@export var drop_item: ItemData
@export var drop_count_min: int = 1
@export var drop_count_max: int = 3
@export var pickup_scene: PackedScene
@export var sprite: Sprite2D
@export var rock_color: Color = Palette.STONE_LIGHT
@export var ore_color: Color = Palette.AZURE
@export var rock_radius: float = 10.8

var current_hits: int = 0

var _use_sprite: bool = false
var _shape: PackedVector2Array = PackedVector2Array()
var _ore_spots: PackedVector2Array = PackedVector2Array()
var _shake_offset: Vector2 = Vector2.ZERO

func _ready() -> void:
	add_to_group("damageable")
	add_to_group("harvestables")

	if not sprite:
		sprite = get_node_or_null("Sprite2D")
	_use_sprite = sprite != null and sprite.texture != null
	if sprite and not _use_sprite:
		sprite.visible = false

	_build_shape()

	var shadow := BlobShadow.new()
	shadow.radius = rock_radius * 0.9
	shadow.position = Vector2(0.0, rock_radius * 0.6)
	add_child(shadow)

func _build_shape() -> void:
	var segments := 9
	for i in segments:
		var angle: float = i * TAU / float(segments)
		var distance: float = rock_radius * randf_range(0.78, 1.12)
		_shape.append(Vector2(cos(angle) * distance, sin(angle) * distance * 0.85))
	for i in 3:
		var angle: float = randf() * TAU
		_ore_spots.append(Vector2(cos(angle), sin(angle)) * rock_radius * randf_range(0.15, 0.5))

func _process(_delta: float) -> void:
	if not _use_sprite and _shake_offset != Vector2.ZERO:
		queue_redraw()

func _draw() -> void:
	if _use_sprite:
		return
	var pixel: float = FX.pixel_size()
	PixelDraw.disc(self, _shake_offset, rock_radius, pixel, rock_color)
	PixelDraw.ring(self, _shake_offset, rock_radius, pixel, rock_color.darkened(0.35), 1)
	for spot in _ore_spots:
		PixelDraw.stamp(self, _shake_offset + spot, pixel * 1.6, ore_color)
		PixelDraw.stamp(self, _shake_offset + spot - Vector2(pixel, pixel) * 0.6, pixel * 0.8, Color(1.0, 1.0, 1.0, 0.75))

func take_damage(amount: float) -> void:
	current_hits += 1

	FX.hit_spark(global_position, ore_color, 7, Vector2.UP, PI, 26.0)
	FX.shake(1.5)

	if sprite and _use_sprite:
		FX.flash(sprite, Color(3.0, 3.0, 3.0), 0.1)
	else:
		_shake_offset = Vector2(randf_range(-3.0, 3.0), randf_range(-2.0, 2.0))
		var tween := create_tween()
		tween.tween_property(self, "_shake_offset", Vector2.ZERO, 0.14)
		tween.tween_callback(queue_redraw)
		queue_redraw()

	if current_hits >= hit_points:
		break_ore()

func break_ore() -> void:
	FX.impact(global_position, Vector2.ZERO, ore_color, 1.3)
	FX.dust_puff(global_position, Color(rock_color, 0.6), 6, 30.0)
	FX.shake(3.0)

	if drop_item and pickup_scene:
		var scene_root := get_tree().current_scene
		if scene_root:
			var amount := randi_range(drop_count_min, max(drop_count_min, drop_count_max))
			for i in amount:
				var pickup = pickup_scene.instantiate()
				pickup.item = drop_item
				pickup.count = 1
				pickup.global_position = global_position
				if pickup.has_method("pop_out"):
					pickup.pop_out()
				scene_root.add_child.call_deferred(pickup)

	queue_free()
