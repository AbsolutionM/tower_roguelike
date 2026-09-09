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

func _block(rect: Rect2, fill: Color, edge: Color) -> void:
	draw_rect(rect.grow(0.5), edge)
	draw_rect(rect, fill)
