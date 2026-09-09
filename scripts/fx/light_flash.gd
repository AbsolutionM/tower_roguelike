extends PointLight2D
class_name LightFlash

## Kurzer Lichtblitz (Mündungsfeuer, Treffer, Fähigkeiten).
## Räumt sich selbst auf.

const LIGHT_TEXTURE := preload("res://resources/materials/light_gradient.tres")

var duration: float = 0.18
var peak_energy: float = 2.0
var start_scale: float = 1.0
var end_scale: float = 1.6

var _elapsed: float = 0.0

func _ready() -> void:
	texture = LIGHT_TEXTURE
	blend_mode = Light2D.BLEND_MODE_ADD
	energy = peak_energy
	texture_scale = start_scale

func _process(delta: float) -> void:
	_elapsed += delta
	var progress: float = clampf(_elapsed / maxf(duration, 0.0001), 0.0, 1.0)
	energy = peak_energy * (1.0 - progress)
	texture_scale = lerpf(start_scale, end_scale, progress)
	if progress >= 1.0:
		queue_free()
