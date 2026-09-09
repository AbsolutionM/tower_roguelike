extends Control
class_name TowerArtwork

## Prozedurales Turmbild für den Start-Tab.
## Sobald TowerData.image gesetzt ist, wird stattdessen die Textur gezeigt.

var tower: TowerData

var _time: float = 0.0

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func _process(delta: float) -> void:
	_time += delta
	queue_redraw()

func _draw() -> void:
	if not tower:
		return

	var view := size
	if tower.image:
		var texture_size: Vector2 = tower.image.get_size()
		var scale_factor: float = minf(view.x / maxf(texture_size.x, 1.0), view.y / maxf(texture_size.y, 1.0))
		var draw_size: Vector2 = texture_size * scale_factor
		draw_texture_rect(tower.image, Rect2((view - draw_size) * 0.5, draw_size), false)
		return

	var accent: Color = tower.accent_color
	var sky_top: Color = Palette.INK
	var sky_bottom: Color = Color(accent, 0.12)

	# Himmel
	draw_rect(Rect2(Vector2.ZERO, view), sky_top)
	draw_rect(Rect2(Vector2(0.0, view.y * 0.45), Vector2(view.x, view.y * 0.55)), sky_bottom)

	var pixel: float = UIKit.PIXEL

	# Mond als Pixelscheibe mit ausgestanzter Sichel
	PixelDraw.disc(self, Vector2(view.x * 0.76, view.y * 0.18), view.x * 0.075, pixel, Color(Palette.AMBER, 0.85))
	PixelDraw.disc(self, Vector2(view.x * 0.79, view.y * 0.16), view.x * 0.062, pixel, sky_top)

	var center_x: float = view.x * 0.5
	var ground_y: float = view.y * 0.9
	var floors: int = clampi(tower.floors, 3, 9)
	var floor_height: float = (ground_y - view.y * 0.18) / float(floors)

	# Etagen von unten nach oben, jede etwas schmaler.
	for i in floors:
		var t: float = float(i) / float(floors)
		var half_width: float = lerpf(view.x * 0.27, view.x * 0.15, t)
		var top: float = ground_y - floor_height * float(i + 1)
		var rect := Rect2(center_x - half_width, top, half_width * 2.0, floor_height + 1.0)

		draw_rect(rect, Palette.STONE.lerp(accent, t * 0.18))
		draw_rect(rect, Color(Palette.INK, 0.8), false, 2.0)

		# Fenster, die leicht pulsieren
		var windows: int = 3 if half_width > view.x * 0.2 else 2
		for w in windows:
			var wx: float = center_x + lerpf(-half_width * 0.55, half_width * 0.55, float(w) / maxf(float(windows - 1), 1.0))
			var glow: float = 0.55 + 0.45 * sin(_time * 1.6 + float(i) * 1.3 + float(w))
			var window_rect := Rect2(wx - floor_height * 0.11, top + floor_height * 0.3, floor_height * 0.22, floor_height * 0.34)
			draw_rect(window_rect, Color(accent, 0.35 + 0.4 * glow))

	# Dach als gestapelte Pixelstufen statt glattem Dreieck
	var roof_y: float = ground_y - floor_height * float(floors)
	var roof_half: float = view.x * 0.19
	var roof_height: float = view.y * 0.09
	var roof_steps: int = maxi(int(roof_height / pixel), 3)
	for i in roof_steps:
		var t: float = float(i) / float(roof_steps)
		var step_half: float = roof_half * (1.0 - t)
		var step_y: float = roof_y - roof_height * t
		draw_rect(Rect2(center_x - step_half, step_y - pixel, step_half * 2.0, pixel), Color(accent, 0.85))

	# Mast und Fahne
	var flag_top := Vector2(center_x, roof_y - roof_height)
	var mast_height: float = view.y * 0.05
	draw_rect(Rect2(flag_top.x - pixel * 0.5, flag_top.y - mast_height, pixel, mast_height), Palette.BONE)

	var wave: float = sin(_time * 3.0) * view.x * 0.012
	var flag_height: float = maxf(view.y * 0.008, pixel)
	for i in 4:
		var t: float = float(i) / 4.0
		var flag_width: float = maxf(view.x * 0.075 * (1.0 - t * 0.3) + wave, pixel)
		draw_rect(
			Rect2(flag_top.x, flag_top.y - mast_height + float(i) * flag_height, flag_width, flag_height),
			accent
		)

	# Boden
	draw_rect(Rect2(Vector2(0.0, ground_y), Vector2(view.x, view.y - ground_y)), Palette.SHADOW)
	draw_rect(Rect2(Vector2(0.0, ground_y), Vector2(view.x, pixel * 0.5)), Color(accent, 0.4))
