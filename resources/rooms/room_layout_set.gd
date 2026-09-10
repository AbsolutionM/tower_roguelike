extends Resource
class_name RoomLayoutSet

## Sammlung fester Raum-Layouts im Isaac-Stil.
## Die Layouts stehen in einer Textdatei, durch Leerzeilen getrennt -
## so kann man sie in jedem Editor als Raster sehen und bearbeiten.
##
## Zeichen:
##   .  leer
##   #  Fels
##   e  Gegner (aus dem enemy_pool des Raums)
##   c  Truhe
##   o  Erz
## Zeilen, die mit // beginnen, sind Kommentare.

@export var set_name: String = "Layouts"
@export var columns: int = 9
@export_file("*.txt") var layout_file: String = ""

var _layouts: Array = []
var _loaded: bool = false

func _ensure_loaded() -> void:
	if _loaded:
		return
	_loaded = true

	if layout_file.is_empty() or not FileAccess.file_exists(layout_file):
		push_warning("RoomLayoutSet: Datei nicht gefunden: " + layout_file)
		return

	var file := FileAccess.open(layout_file, FileAccess.READ)
	if not file:
		return

	var current := PackedStringArray()
	while not file.eof_reached():
		var line := file.get_line()
		if line.begins_with("//"):
			continue
		var trimmed := line.strip_edges()
		if trimmed.is_empty():
			if current.size() > 0:
				_layouts.append(current)
				current = PackedStringArray()
			continue
		current.append(trimmed)
	file.close()

	if current.size() > 0:
		_layouts.append(current)

func get_random_layout() -> PackedStringArray:
	_ensure_loaded()
	if _layouts.is_empty():
		return PackedStringArray()
	return _layouts[randi() % _layouts.size()]
