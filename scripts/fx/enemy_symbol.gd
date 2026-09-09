extends Node2D
class_name EnemySymbol

## Gezeichnetes Platzhalter-Symbol für Gegner ohne eigene Textur.
## Sobald in der EnemyData eine sprite_texture liegt, wird das hier nicht benutzt.

enum Kind { BLOB, BAT, SKULL, EYE, SPIDER, CRYSTAL, GHOST }

var kind: Kind = Kind.BLOB
var tint: Color = Palette.MOSS
var symbol_size: float = 26.0

var _time: float = 0.0

func _ready() -> void:
	z_as_relative = false

func _process(delta: float) -> void:
	_time += delta
	queue_redraw()

func _dark() -> Color:
	return Color(Palette.INK, 0.9)

func _draw() -> void:
	var pixel: float = FX.pixel_size()
	match kind:
		Kind.BLOB:
			_draw_blob(pixel)
		Kind.BAT:
			_draw_bat(pixel)
		Kind.SKULL:
			_draw_skull(pixel)
		Kind.EYE:
			_draw_eye(pixel)
		Kind.SPIDER:
			_draw_spider(pixel)
		Kind.CRYSTAL:
			_draw_crystal(pixel)
		Kind.GHOST:
			_draw_ghost(pixel)

## Kuppel mit flachem Boden - Grundform für Schleim und Geist.
func _dome(pixel: float, radius: float, squash: float, color: Color) -> void:
	var blocks: int = int(ceil(radius / pixel))
	for y in range(-blocks, blocks + 1):
		for x in range(-blocks, blocks + 1):
			var offset := Vector2(float(x), float(y)) * pixel
			if offset.y > 0.0:
				continue
			if Vector2(offset.x / radius, offset.y / (radius * squash)).length() > 1.0:
				continue
			PixelDraw.stamp(self, offset, pixel, color)
	draw_rect(Rect2(-radius, -pixel, radius * 2.0, pixel), color)

func _eyes(pixel: float, spread: float, height: float) -> void:
	PixelDraw.stamp(self, Vector2(-spread, height), pixel, _dark())
	PixelDraw.stamp(self, Vector2(spread, height), pixel, _dark())

func _draw_blob(pixel: float) -> void:
	var squish: float = 1.0 + sin(_time * 3.0) * 0.06
	_dome(pixel, symbol_size, 0.85 / squish, tint)
	PixelDraw.stamp(self, Vector2(-symbol_size * 0.3, -symbol_size * 0.55), pixel, Color(1.0, 1.0, 1.0, 0.5))
	_eyes(pixel, symbol_size * 0.32, -symbol_size * 0.3)

func _draw_bat(pixel: float) -> void:
	var flap: float = sin(_time * 11.0) * symbol_size * 0.28
	var body: float = symbol_size * 0.42
	PixelDraw.disc(self, Vector2.ZERO, body, pixel, tint)

	# Flügel als gestufte Dreiecke, die auf und ab schlagen
	var steps: int = 4
	for i in steps:
		var t: float = float(i) / float(steps)
		var reach: float = body + symbol_size * 0.95 * t
		var y: float = -flap * t
		var thickness: float = pixel * (2.0 - t)
		draw_rect(Rect2(-reach, y - thickness * 0.5, reach - body * 0.6, thickness), tint)
		draw_rect(Rect2(body * 0.6, y - thickness * 0.5, reach - body * 0.6, thickness), tint)

	# Ohren
	PixelDraw.stamp(self, Vector2(-body * 0.5, -body - pixel), pixel, tint)
	PixelDraw.stamp(self, Vector2(body * 0.5, -body - pixel), pixel, tint)
	_eyes(pixel, body * 0.4, -body * 0.1)

func _draw_skull(pixel: float) -> void:
	PixelDraw.disc(self, Vector2(0.0, -symbol_size * 0.15), symbol_size * 0.7, pixel, tint)
	draw_rect(Rect2(-symbol_size * 0.35, symbol_size * 0.3, symbol_size * 0.7, symbol_size * 0.3), tint)
	PixelDraw.disc(self, Vector2(-symbol_size * 0.3, -symbol_size * 0.2), pixel * 1.6, pixel, _dark())
	PixelDraw.disc(self, Vector2(symbol_size * 0.3, -symbol_size * 0.2), pixel * 1.6, pixel, _dark())
	for i in 3:
		draw_rect(Rect2(-symbol_size * 0.22 + float(i) * symbol_size * 0.2, symbol_size * 0.3, pixel, symbol_size * 0.3), _dark())

func _draw_eye(pixel: float) -> void:
	PixelDraw.disc(self, Vector2.ZERO, symbol_size * 0.8, pixel, Color(0.95, 0.95, 1.0))
	PixelDraw.ring(self, Vector2.ZERO, symbol_size * 0.8, pixel, tint, 2)
	var look := Vector2(sin(_time * 1.7), cos(_time * 1.3)) * symbol_size * 0.22
	PixelDraw.disc(self, look, symbol_size * 0.34, pixel, tint)
	PixelDraw.disc(self, look, symbol_size * 0.16, pixel, _dark())

func _draw_spider(pixel: float) -> void:
	var body: float = symbol_size * 0.45
	var wiggle: float = sin(_time * 8.0) * pixel
	for i in 3:
		var y: float = -body * 0.4 + float(i) * body * 0.5
		var reach: float = body + symbol_size * 0.75
		draw_rect(Rect2(-reach, y + wiggle, reach - body * 0.5, pixel), tint)
		draw_rect(Rect2(body * 0.5, y - wiggle, reach - body * 0.5, pixel), tint)
	PixelDraw.disc(self, Vector2(0.0, body * 0.2), body, pixel, tint)
	PixelDraw.disc(self, Vector2(0.0, -body * 0.7), body * 0.5, pixel, tint)
	_eyes(pixel, body * 0.28, -body * 0.75)

func _draw_crystal(pixel: float) -> void:
	var height: float = symbol_size * 1.1
	var width: float = symbol_size * 0.7
	var rows: int = maxi(int(height * 2.0 / pixel), 4)
	for i in rows:
		var t: float = float(i) / float(rows)
		var y: float = -height + height * 2.0 * t
		var half: float = width * (1.0 - absf(t - 0.42) / 0.58)
		if half <= 0.0:
			continue
		var shade: Color = tint.lightened(0.25) if t < 0.42 else tint
		draw_rect(Rect2(-half, y, half * 2.0, pixel), shade)
	PixelDraw.stamp(self, Vector2(-width * 0.25, -height * 0.35), pixel, Color(1.0, 1.0, 1.0, 0.65))

func _draw_ghost(pixel: float) -> void:
	var drift: float = sin(_time * 2.2) * pixel
	_dome(pixel, symbol_size * 0.85, 1.0, Color(tint, 0.85))
	# Wellenförmiger Abschluss unten
	var width: float = symbol_size * 0.85
	var columns: int = int(width * 2.0 / pixel)
	for i in columns:
		var x: float = -width + float(i) * pixel
		var wave: float = sin(float(i) * 0.9 + _time * 5.0) * pixel
		draw_rect(Rect2(x, -pixel, pixel, pixel * 2.5 + wave), Color(tint, 0.85))
	_eyes(pixel, symbol_size * 0.3, -symbol_size * 0.35 + drift)
