extends Resource
class_name RoomTileset

## Kacheln für einen Turm: Boden, Randkante, Streudeko und Lachen.
##
## Der RoomController zeichnet damit statt des Platzhalter-Schachbretts.
## Fehlt eine Kachel, fällt er für dieses Stück auf das gezeichnete Muster
## zurück - ein halb gefüllter Satz ist also kein Problem.

@export_group("Boden")
## Grundkacheln. Werden zufällig gemischt, damit der Boden nicht kachelt.
@export var floor_tiles: Array[Texture2D] = []
## Seltene Abwechslung (Gitter, Risse). Häufigkeit siehe `accent_chance`.
@export var floor_accents: Array[Texture2D] = []
@export_range(0.0, 0.5) var accent_chance: float = 0.07

@export_group("Deko")
## Liegt lose auf dem Boden - Pfützen, Blasen, Kleinkram.
@export var decor_tiles: Array[Texture2D] = []
@export_range(0.0, 0.5) var decor_chance: float = 0.05

@export_group("Rand")
## Mehrere Varianten pro Seite, damit die Kante nicht sichtbar kachelt.
@export var wall_top: Array[Texture2D] = []
@export var wall_bottom: Array[Texture2D] = []
@export var wall_left: Array[Texture2D] = []
@export var wall_right: Array[Texture2D] = []
@export var corner_top_left: Texture2D
@export var corner_top_right: Texture2D
@export var corner_bottom_left: Texture2D
@export var corner_bottom_right: Texture2D

@export_group("Lachen")
## Zusammenhängende Flächen aus Mitte, Rand, Außen- und Innenecken.
## Streifen von einer Kachel Breite gibt es nicht - der Raum räumt solche
## Zellen weg, bevor er zeichnet.
@export var pool_center: Array[Texture2D] = []
@export var pool_top: Texture2D
@export var pool_bottom: Texture2D
@export var pool_left: Texture2D
@export var pool_right: Texture2D
@export var pool_corner_top_left: Texture2D
@export var pool_corner_top_right: Texture2D
@export var pool_corner_bottom_left: Texture2D
@export var pool_corner_bottom_right: Texture2D
@export var pool_inner_top_left: Texture2D
@export var pool_inner_top_right: Texture2D
@export var pool_inner_bottom_left: Texture2D
@export var pool_inner_bottom_right: Texture2D
@export var pool_single: Texture2D
## Ungefähre Zahl der Lachen pro Raum.
@export_range(0, 12) var pool_count: int = 3

@export_group("Darstellung")
## Kantenlänge einer Kachel auf dem Bildschirm. Ein ganzes Vielfaches der
## Texturgröße, sonst verwischt die Pixelkunst.
@export var tile_size: float = 64.0

func has_floor() -> bool:
	return not floor_tiles.is_empty()

func has_walls() -> bool:
	return not wall_top.is_empty() and not wall_left.is_empty()

func has_pools() -> bool:
	return pool_count > 0 and not pool_center.is_empty() and pool_top != null

static func _any(options: Array[Texture2D], rng: RandomNumberGenerator) -> Texture2D:
	if options.is_empty():
		return null
	return options[rng.randi() % options.size()]

## Bodenkachel für eine Rasterzelle. `rng` macht das Muster pro Raum stabil.
func pick_floor(rng: RandomNumberGenerator) -> Texture2D:
	if floor_tiles.is_empty():
		return null
	if not floor_accents.is_empty() and rng.randf() < accent_chance:
		return _any(floor_accents, rng)
	return _any(floor_tiles, rng)

## Deko für eine Zelle, oder null.
func pick_decor(rng: RandomNumberGenerator) -> Texture2D:
	if decor_tiles.is_empty() or rng.randf() >= decor_chance:
		return null
	return _any(decor_tiles, rng)

## Randstück für eine Randzelle.
func pick_wall(on_left: bool, on_right: bool, on_top: bool, on_bottom: bool, rng: RandomNumberGenerator) -> Texture2D:
	if on_top and on_left:
		return corner_top_left
	if on_top and on_right:
		return corner_top_right
	if on_bottom and on_left:
		return corner_bottom_left
	if on_bottom and on_right:
		return corner_bottom_right
	if on_top:
		return _any(wall_top, rng)
	if on_bottom:
		return _any(wall_bottom, rng)
	if on_left:
		return _any(wall_left, rng)
	if on_right:
		return _any(wall_right, rng)
	return null

## Lachenkachel aus den Nachbarn: `sides` sind oben, unten, links, rechts,
## `diagonals` oben-links, oben-rechts, unten-links, unten-rechts - jeweils
## true, wenn der Nachbar auch in der Lache liegt. Null = keine passende
## Kachel (einzeilige Streifen), die Zelle gehört dann nicht in die Lache.
func pick_pool(sides: Array[bool], diagonals: Array[bool], rng: RandomNumberGenerator) -> Texture2D:
	var top: bool = sides[0]
	var bottom: bool = sides[1]
	var left: bool = sides[2]
	var right: bool = sides[3]
	var count: int = int(top) + int(bottom) + int(left) + int(right)

	match count:
		4:
			if not diagonals[0]:
				return pool_inner_top_left
			if not diagonals[1]:
				return pool_inner_top_right
			if not diagonals[2]:
				return pool_inner_bottom_left
			if not diagonals[3]:
				return pool_inner_bottom_right
			return _any(pool_center, rng)
		3:
			if not top:
				return pool_top
			if not bottom:
				return pool_bottom
			if not left:
				return pool_left
			return pool_right
		2:
			if bottom and right:
				return pool_corner_top_left
			if bottom and left:
				return pool_corner_top_right
			if top and right:
				return pool_corner_bottom_left
			if top and left:
				return pool_corner_bottom_right
		0:
			return pool_single
	return null
