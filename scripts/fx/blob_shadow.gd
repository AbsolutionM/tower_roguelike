extends Node2D
class_name BlobShadow

## Bodenschatten im Pixelraster. Wird per Code an Player/Gegner gehängt,
## damit Figuren nicht "schweben" aussehen.
## Ist im FXTheme eine shadow_texture gesetzt, wird die stattdessen benutzt.

@export var radius: float = 12.0
@export var squash: float = 0.42
@export var alpha: float = 0.3

func _ready() -> void:
	z_index = -20
	z_as_relative = false

func _draw() -> void:
	var tint := Color(0.0, 0.0, 0.0, alpha)

	var texture: Texture2D = FX.theme.shadow_texture
	if texture:
		var draw_size := Vector2(radius * 2.0, radius * 2.0 * squash)
		draw_texture_rect(texture, Rect2(-draw_size * 0.5, draw_size), false, Color(1.0, 1.0, 1.0, alpha))
		return

	PixelDraw.ellipse(self, Vector2.ZERO, radius, radius * squash, FX.pixel_size(), tint)

func configure(new_radius: float, new_alpha: float = -1.0) -> void:
	radius = new_radius
	if new_alpha >= 0.0:
		alpha = new_alpha
	queue_redraw()
