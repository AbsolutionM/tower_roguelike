extends StaticBody2D
class_name Obstacle

## Blockierender Felsblock im Raum (Isaac-Stil): stoppt Spieler und Geschosse
## und zwingt dazu, um Ecken zu laufen statt stumpf geradeaus.

@export var block_radius: float = 26.0
@export var body_color: Color = Palette.STONE_LIGHT
@export var top_color: Color = Palette.MIST
## Optional: Textur statt der gezeichneten Blöcke.
@export var texture: Texture2D

var _shape: CollisionShape2D
var _chips: PackedVector2Array = PackedVector2Array()

func _ready() -> void:
	add_to_group("obstacles")
	z_index = 2
	z_as_relative = false

	_shape = CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = block_radius
	_shape.shape = circle
	add_child(_shape)

	# Ein paar unregelmäßige Kanten, damit nicht alle Blöcke gleich aussehen.
	for i in 4:
		var angle: float = randf() * TAU
		_chips.append(Vector2(cos(angle), sin(angle)) * block_radius * randf_range(0.45, 0.8))

	var shadow := BlobShadow.new()
	shadow.radius = block_radius * 0.9
	shadow.position = Vector2(0.0, block_radius * 0.5)
	add_child(shadow)

func get_radius() -> float:
	return block_radius

func _draw() -> void:
	if texture:
		var draw_size := Vector2.ONE * block_radius * 2.2
		draw_texture_rect(texture, Rect2(-draw_size * 0.5, draw_size), false)
		return

	var pixel: float = FX.pixel_size()
	PixelDraw.disc(self, Vector2(0.0, 0.0), block_radius, pixel, body_color)
	PixelDraw.disc(self, Vector2(0.0, -block_radius * 0.25), block_radius * 0.7, pixel, top_color)
	# Heller Rand statt dunklem - so hebt sich der Fels vom dunklen Boden ab.
	PixelDraw.ring(self, Vector2.ZERO, block_radius, pixel, Palette.highlight(body_color), 1)
	for chip in _chips:
		PixelDraw.stamp(self, chip, pixel, Palette.edge(body_color))
