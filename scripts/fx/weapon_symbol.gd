extends Node2D
class_name WeaponSymbol

## Gezeichneter Platzhalter für Waffen ohne eigenes Haltesprite.
## Damit ist keine Waffe unsichtbar, solange die Texturen noch fehlen -
## dieselbe Idee wie bei den Gegner-Symbolen.
##
## Gezeichnet wird immer nach +X. Der WeaponPivot dreht das Ganze zum Ziel.

var category: WeaponData.Category = WeaponData.Category.SHORTSWORD
var tint: Color = Palette.BONE

## Bewusst kein `z_as_relative = false`: der Platzhalter soll genau dort liegen,
## wo auch ein echtes Haltesprite liegt - relativ zur Hand, vor dem Körper.
func _draw() -> void:
	match category:
		WeaponData.Category.SHORTSWORD:
			_blade(11.0, 2.0)
		WeaponData.Category.BROADSWORD:
			_blade(15.0, 3.0)
		WeaponData.Category.KATANA:
			_blade(16.0, 1.5)
		WeaponData.Category.REVOLVER:
			_gun(8.0, 2.0, 3.5)
		WeaponData.Category.PISTOL:
			_gun(9.0, 1.5, 3.0)
		WeaponData.Category.SMG:
			_gun(12.0, 1.5, 4.0)
		WeaponData.Category.SHOTGUN:
			_gun(16.0, 2.5, 4.5)
		WeaponData.Category.BOW:
			_bow(13.0)
		WeaponData.Category.STAFF:
			_staff(17.0)
		WeaponData.Category.WHIP:
			_whip(16.0)
		WeaponData.Category.THROWN:
			_disc(7.0)
		WeaponData.Category.SHIELD:
			_shield(7.0)

## Griff, Parierstange, Klinge - alles in ganzen Pixelblöcken.
func _blade(length: float, half_width: float) -> void:
	var edge: Color = Palette.edge(tint)
	_block(Rect2(-4.0, -1.0, 4.0, 2.0), Palette.STONE, edge)
	_block(Rect2(-0.5, -half_width - 1.5, 1.5, half_width * 2.0 + 3.0), Palette.GOLD, edge)
	_block(Rect2(1.0, -half_width, length, half_width * 2.0), tint, edge)
	# Glanzkante oben auf der Klinge.
	draw_rect(Rect2(1.0, -half_width, length, 0.6), Palette.highlight(tint))

## Griff, Verschluss, Lauf - je nach Waffe länger oder dicker.
## Der Korpus bleibt stahlgrau, `tint` markiert nur Lauf und Mündung -
## sonst wird eine dunkel getönte Waffe vor dunklem Boden zum braunen Brett.
func _gun(barrel: float, barrel_half: float, body_half: float) -> void:
	var steel: Color = Palette.STONE_LIGHT.lightened(0.25)
	var edge: Color = Palette.INK
	_block(Rect2(-3.0, 0.0, 3.0, 5.0), Palette.edge(Palette.EMBER), edge)
	_block(Rect2(-3.5, -body_half, 5.5, body_half * 2.0), steel, edge)
	_block(Rect2(2.0, -barrel_half, barrel, barrel_half * 2.0), steel, edge)
	# Laufkante und Mündung in der Waffenfarbe - daran erkennt man den Typ.
	draw_rect(Rect2(2.0, -barrel_half, barrel, 0.7), tint)
	draw_rect(Rect2(barrel + 1.0, -barrel_half - 0.4, 1.2, barrel_half * 2.0 + 0.8), tint)

## Bogen als Halbkreis quer zur Schussrichtung, Sehne als gerade Linie.
func _bow(radius: float) -> void:
	var edge: Color = Palette.edge(tint)
	draw_arc(Vector2(2.0, 0.0), radius, -PI * 0.5, PI * 0.5, 14, edge, 3.0)
	draw_arc(Vector2(2.0, 0.0), radius, -PI * 0.5, PI * 0.5, 14, tint, 1.6)
	draw_line(Vector2(2.0, -radius), Vector2(2.0, radius), Palette.BONE, 0.8)
	_block(Rect2(0.0, -1.5, 4.0, 3.0), Palette.STONE, edge)

## Langer dünner Schaft mit Knauf an der Spitze.
func _staff(length: float) -> void:
	var edge: Color = Palette.edge(Palette.STONE)
	_block(Rect2(-5.0, -0.8, length, 1.6), Palette.STONE, edge)
	draw_circle(Vector2(length - 5.0, 0.0), 3.2, Palette.edge(tint))
	draw_circle(Vector2(length - 5.0, 0.0), 2.4, tint)
	draw_circle(Vector2(length - 5.8, -0.8), 0.9, Palette.highlight(tint))

## Griff plus eine Schnur, die nach vorn hin dünner wird und leicht wellt.
func _whip(length: float) -> void:
	var edge: Color = Palette.edge(tint)
	_block(Rect2(-4.0, -1.2, 5.0, 2.4), Palette.STONE, Palette.INK)
	var points := PackedVector2Array()
	for i in 9:
		var t: float = float(i) / 8.0
		points.append(Vector2(1.0 + t * length, sin(t * PI * 2.0) * 1.8 * (1.0 - t * 0.5)))
	draw_polyline(points, edge, 2.6)
	draw_polyline(points, tint, 1.2)

## Wurfscheibe: Raute mit hellem Kern.
func _disc(radius: float) -> void:
	var edge: Color = Palette.edge(tint)
	var shape := PackedVector2Array([
		Vector2(radius, 0.0), Vector2(0.0, radius), Vector2(-radius, 0.0), Vector2(0.0, -radius)
	])
	draw_colored_polygon(shape, edge)
	var inner := PackedVector2Array()
	for point in shape:
		inner.append(point * 0.75)
	draw_colored_polygon(inner, tint)
	draw_circle(Vector2.ZERO, radius * 0.25, Palette.highlight(tint))

## Schild: Tafel mit Rand und Buckel.
func _shield(half: float) -> void:
	var edge: Color = Palette.edge(tint)
	_block(Rect2(-half * 0.6, -half, half * 1.2, half * 2.0), tint, edge)
	draw_rect(Rect2(-half * 0.6, -half, half * 1.2, 1.0), Palette.highlight(tint))
	draw_circle(Vector2.ZERO, half * 0.3, edge)

func _block(rect: Rect2, fill: Color, edge: Color) -> void:
	draw_rect(rect.grow(0.5), edge)
	draw_rect(rect, fill)
