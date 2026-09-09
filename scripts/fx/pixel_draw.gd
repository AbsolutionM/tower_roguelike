extends RefCounted
class_name PixelDraw

## Zeichenhilfen im Pixelraster - damit Effekte zum Pixel-Art-Look passen
## statt weiche Vektorkreise zu sein.
## Ist `texture` gesetzt, wird statt eines Quadrats die Textur gestempelt.

## Größe der tatsächlich bemalten Fläche einer Textur.
## Viele Sprites haben breiten leeren Rand - die Texturgröße sagt wenig aus.
static func used_size(texture: Texture2D) -> Vector2:
	var used := _used_rect(texture)
	return Vector2(used.size) if used.size.x > 0 else texture.get_size()

## Versatz, der die bemalte Fläche auf den Knotenursprung zentriert.
## Ohne den sitzen Sprites schief, deren Motiv nicht mittig in der Textur liegt.
static func center_offset(texture: Texture2D) -> Vector2:
	var used := _used_rect(texture)
	if used.size.x <= 0 or used.size.y <= 0:
		return Vector2.ZERO
	var full: Vector2 = texture.get_size()
	return (full * 0.5 - Vector2(used.position) - Vector2(used.size) * 0.5).round()

static func _used_rect(texture: Texture2D) -> Rect2i:
	if not texture:
		return Rect2i()
	var image := texture.get_image()
	if not image:
		return Rect2i()
	return image.get_used_rect()

static func snap(point: Vector2, pixel: float) -> Vector2:
	return Vector2(roundf(point.x / pixel) * pixel, roundf(point.y / pixel) * pixel)

static func stamp(canvas: CanvasItem, center: Vector2, pixel: float, color: Color, texture: Texture2D = null) -> void:
	var snapped := snap(center, pixel)
	if texture:
		var texture_size: Vector2 = texture.get_size()
		var scale_factor: float = pixel * 2.0 / maxf(texture_size.x, 1.0)
		var draw_size: Vector2 = texture_size * scale_factor
		canvas.draw_texture_rect(texture, Rect2(snapped - draw_size * 0.5, draw_size), false, color)
		return
	canvas.draw_rect(Rect2(snapped - Vector2(pixel, pixel) * 0.5, Vector2(pixel, pixel)), color)

## Gerasterter Ring. `thickness` zählt in Pixelblöcken nach innen.
static func ring(canvas: CanvasItem, center: Vector2, radius: float, pixel: float, color: Color, thickness: int = 1, texture: Texture2D = null) -> void:
	if radius <= 0.0:
		return
	var steps: int = maxi(int(TAU * radius / maxf(pixel, 1.0)), 10)
	var drawn := {}
	for i in steps:
		var angle: float = TAU * float(i) / float(steps)
		var direction := Vector2(cos(angle), sin(angle))
		for t in maxi(thickness, 1):
			var point := center + direction * maxf(radius - float(t) * pixel, 0.0)
			var key := snap(point, pixel)
			if drawn.has(key):
				continue
			drawn[key] = true
			stamp(canvas, key, pixel, color, texture)

## Gefüllte, gerasterte Scheibe.
static func disc(canvas: CanvasItem, center: Vector2, radius: float, pixel: float, color: Color, texture: Texture2D = null) -> void:
	if radius <= 0.0:
		return
	var blocks: int = int(ceil(radius / maxf(pixel, 1.0)))
	for y in range(-blocks, blocks + 1):
		for x in range(-blocks, blocks + 1):
			var offset := Vector2(float(x), float(y)) * pixel
			if offset.length() > radius:
				continue
			stamp(canvas, center + offset, pixel, color, texture)

## Gerasterte Linie - für Funken, Blitze und Regen.
static func line(canvas: CanvasItem, from: Vector2, to: Vector2, pixel: float, color: Color, texture: Texture2D = null) -> void:
	var distance := from.distance_to(to)
	var steps: int = maxi(int(distance / maxf(pixel, 1.0)), 1)
	var drawn := {}
	for i in steps + 1:
		var point := from.lerp(to, float(i) / float(steps))
		var key := snap(point, pixel)
		if drawn.has(key):
			continue
		drawn[key] = true
		stamp(canvas, key, pixel, color, texture)

## Gerasterter Kreisbogen - z.B. für Cooldown-Anzeigen.
static func arc(canvas: CanvasItem, center: Vector2, radius: float, start_angle: float, end_angle: float, pixel: float, color: Color, thickness: int = 1) -> void:
	if radius <= 0.0 or end_angle <= start_angle:
		return
	var span: float = end_angle - start_angle
	var steps: int = maxi(int(span * radius / maxf(pixel, 1.0)), 4)
	var drawn := {}
	for i in steps + 1:
		var angle: float = start_angle + span * float(i) / float(steps)
		var direction := Vector2(cos(angle), sin(angle))
		for t in maxi(thickness, 1):
			var point := center + direction * maxf(radius - float(t) * pixel, 0.0)
			var key := snap(point, pixel)
			if drawn.has(key):
				continue
			drawn[key] = true
			stamp(canvas, key, pixel, color)

## Rechteckiger Pixelrahmen - für UI-Kästen mit harten Kanten.
static func frame(canvas: CanvasItem, rect: Rect2, pixel: float, color: Color, thickness: int = 1) -> void:
	var inset: float = float(maxi(thickness, 1)) * pixel
	canvas.draw_rect(Rect2(rect.position, Vector2(rect.size.x, inset)), color)
	canvas.draw_rect(Rect2(Vector2(rect.position.x, rect.end.y - inset), Vector2(rect.size.x, inset)), color)
	canvas.draw_rect(Rect2(rect.position, Vector2(inset, rect.size.y)), color)
	canvas.draw_rect(Rect2(Vector2(rect.end.x - inset, rect.position.y), Vector2(inset, rect.size.y)), color)

## Breite auf ganze Pixelblöcke abrunden - damit Balken in Stufen wachsen.
static func quantize(value: float, pixel: float) -> float:
	return floorf(value / maxf(pixel, 1.0)) * pixel

## Gerasterte Ellipse, gefüllt - für Schatten.
static func ellipse(canvas: CanvasItem, center: Vector2, radius_x: float, radius_y: float, pixel: float, color: Color) -> void:
	if radius_x <= 0.0 or radius_y <= 0.0:
		return
	var blocks_x: int = int(ceil(radius_x / maxf(pixel, 1.0)))
	var blocks_y: int = int(ceil(radius_y / maxf(pixel, 1.0)))
	for y in range(-blocks_y, blocks_y + 1):
		for x in range(-blocks_x, blocks_x + 1):
			var offset := Vector2(float(x), float(y)) * pixel
			var normalized := Vector2(offset.x / radius_x, offset.y / radius_y)
			if normalized.length() > 1.0:
				continue
			stamp(canvas, center + offset, pixel, color)
