extends Node2D
class_name ShapeFX

## Prozedurale Effekt-Formen (Ringe, Funken, Staub, Mündungsfeuer).
## Wird im Pixelraster gezeichnet, damit es zum Pixel-Art-Look passt.
## Texturen kommen optional aus dem FXTheme.

enum Mode { RING, SPARKS, PUFF, CONE }

var mode: Mode = Mode.RING
var color: Color = Color.WHITE
var duration: float = 0.3
var start_radius: float = 8.0
var end_radius: float = 80.0
var start_width: float = 6.0
var end_width: float = 1.0
var direction: Vector2 = Vector2.RIGHT
var spread: float = TAU
var count: int = 8
var additive: bool = true

var _elapsed: float = 0.0
var _dirs: PackedVector2Array = PackedVector2Array()
var _speeds: PackedFloat32Array = PackedFloat32Array()
var _sizes: PackedFloat32Array = PackedFloat32Array()

func _ready() -> void:
	z_index = 150
	z_as_relative = false

	if additive:
		var mat := CanvasItemMaterial.new()
		mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		material = mat

	var base_angle: float = direction.angle() if direction.length() > 0.01 else 0.0
	for i in count:
		var angle: float = base_angle + randf_range(-spread * 0.5, spread * 0.5)
		_dirs.append(Vector2(cos(angle), sin(angle)))
		_speeds.append(randf_range(0.65, 1.0))
		_sizes.append(randf_range(0.6, 1.25))

func _process(delta: float) -> void:
	_elapsed += delta
	if _elapsed >= duration:
		queue_free()
		return
	queue_redraw()

func _ease_out(t: float) -> float:
	return 1.0 - pow(1.0 - t, 3.0)

func _pixel() -> float:
	return FX.pixel_size()

func _draw() -> void:
	var progress: float = clampf(_elapsed / maxf(duration, 0.0001), 0.0, 1.0)
	var fade: float = 1.0 - progress
	var pixel: float = _pixel()
	var tint := Color(color, color.a * fade)

	match mode:
		Mode.RING:
			var radius: float = lerpf(start_radius, end_radius, _ease_out(progress))
			var thickness: int = maxi(int(lerpf(start_width, end_width, progress) / pixel), 1)
			PixelDraw.ring(self, Vector2.ZERO, radius, pixel, tint, thickness, FX.theme.ring_texture)

		Mode.SPARKS:
			for i in count:
				var travel: float = lerpf(0.0, end_radius * _speeds[i], _ease_out(progress))
				var tail: float = maxf(travel - end_radius * 0.4 * _sizes[i], 0.0)
				PixelDraw.line(self, _dirs[i] * tail, _dirs[i] * travel, pixel, tint, FX.theme.spark_texture)

		Mode.PUFF:
			for i in count:
				var offset: Vector2 = _dirs[i] * lerpf(0.0, end_radius, _ease_out(progress)) * _speeds[i]
				var radius: float = lerpf(start_radius, start_radius * 2.0, progress) * _sizes[i]
				PixelDraw.disc(self, offset, radius, pixel, Color(color, color.a * fade * 0.55), FX.theme.puff_texture)

		Mode.CONE:
			var length: float = end_radius * (0.55 + 0.45 * sin(progress * PI))
			var half: float = start_width * fade
			var perpendicular: Vector2 = direction.orthogonal()
			# Mündungsfeuer als schmaler werdende Pixelbalken.
			var steps: int = maxi(int(length / pixel), 2)
			for i in steps:
				var t: float = float(i) / float(steps)
				var width: float = half * (1.0 - t)
				var center: Vector2 = direction * (length * t)
				PixelDraw.line(
					self,
					center - perpendicular * width,
					center + perpendicular * width,
					pixel,
					tint,
					FX.theme.muzzle_texture
				)
			PixelDraw.disc(self, Vector2.ZERO, half * 0.9, pixel, Color(1.0, 1.0, 1.0, fade))
