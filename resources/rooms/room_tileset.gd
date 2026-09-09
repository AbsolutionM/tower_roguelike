extends Resource
class_name RoomTileset

## Kacheln für einen Turm: Boden, Wandkante und Streudeko.
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

@export_group("Wand")
@export var wall_top: Texture2D
@export var wall_bottom: Texture2D
@export var wall_left: Texture2D
@export var wall_right: Texture2D
@export var corner_top_left: Texture2D
@export var corner_top_right: Texture2D
@export var corner_bottom_left: Texture2D
@export var corner_bottom_right: Texture2D

@export_group("Darstellung")
## Kantenlänge einer Kachel auf dem Bildschirm.
@export var tile_size: float = 64.0

func has_floor() -> bool:
	return not floor_tiles.is_empty()

func has_walls() -> bool:
	return wall_top != null and wall_left != null

## Bodenkachel für eine Rasterzelle. `rng` macht das Muster pro Raum stabil.
func pick_floor(rng: RandomNumberGenerator) -> Texture2D:
	if floor_tiles.is_empty():
		return null
	if not floor_accents.is_empty() and rng.randf() < accent_chance:
		return floor_accents[rng.randi() % floor_accents.size()]
	return floor_tiles[rng.randi() % floor_tiles.size()]

## Deko für eine Zelle, oder null.
func pick_decor(rng: RandomNumberGenerator) -> Texture2D:
	if decor_tiles.is_empty() or rng.randf() >= decor_chance:
		return null
	return decor_tiles[rng.randi() % decor_tiles.size()]

## Wandstück für eine Randzelle. `column`/`row` zählen vom Rand nach innen.
func pick_wall(on_left: bool, on_right: bool, on_top: bool, on_bottom: bool) -> Texture2D:
	if on_top and on_left:
		return corner_top_left
	if on_top and on_right:
		return corner_top_right
	if on_bottom and on_left:
		return corner_bottom_left
	if on_bottom and on_right:
		return corner_bottom_right
	if on_top:
		return wall_top
	if on_bottom:
		return wall_bottom
	if on_left:
		return wall_left
	if on_right:
		return wall_right
	return null
