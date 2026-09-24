extends Control
class_name HeartBar

## Herzleiste wie in Isaac: erst die roten Container (voll, halb oder leer),
## dahinter die Seelenherzen. Sechs Herzen pro Reihe.

const HEARTS_PER_ROW := 6

## Größe eines Rasterpixels im Herz (das Herz ist 9 x 8 Pixel).
@export var heart_pixel: float = 3.0
@export var spacing: float = 34.0
@export var row_height: float = 30.0
@export var red_color: Color = Palette.BLOOD
@export var soul_color: Color = Palette.AZURE
@export var empty_color: Color = Palette.STONE_LIGHT

## Alles in halben Herzen.
var red: int = 0
var red_max: int = 0
var soul: int = 0

var _pulse: float = 0.0
var _time: float = 0.0

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func set_hearts(new_red: int, new_red_max: int, new_soul: int) -> void:
	# Kurz aufleuchten, wenn etwas verloren ging.
	if new_red + new_soul < red + soul:
		_pulse = 1.0
	red = new_red
	red_max = new_red_max
	soul = new_soul
	var slots: int = get_slot_count()
	var rows: int = maxi(int(ceil(float(slots) / float(HEARTS_PER_ROW))), 1)
	custom_minimum_size = Vector2(spacing * float(mini(maxi(slots, 1), HEARTS_PER_ROW)), row_height * float(rows))
	queue_redraw()

## Ganze Herzplätze: Container plus angefangene Seelenherzen.
func get_slot_count() -> int:
	return red_max / 2 + (soul + 1) / 2

func _process(delta: float) -> void:
	_time += delta
	if _pulse > 0.0:
		_pulse = maxf(_pulse - delta * 3.0, 0.0)
	# Bei einem einzigen übrigen Herz schlägt die Leiste wie ein Puls.
	if _pulse > 0.0 or red + soul <= 2:
		queue_redraw()

func _draw() -> void:
	var containers: int = red_max / 2
	var soul_slots: int = (soul + 1) / 2
	var low: bool = red + soul <= 2
	var beat: float = 1.0 + (0.12 * maxf(sin(_time * 7.0), 0.0) if low else 0.0) + _pulse * 0.15

	for i in containers + soul_slots:
		var column: int = i % HEARTS_PER_ROW
		var row: int = i / HEARTS_PER_ROW
		var center := Vector2(spacing * (float(column) + 0.5), row_height * (float(row) + 0.5))
		var pixel: float = heart_pixel * (beat if i == 0 else 1.0)

		if i < containers:
			var filled: int = clampi(red - i * 2, 0, 2)
			ItemSymbol.paint_heart(self, center, pixel, red_color, empty_color, filled)
		else:
			var soul_index: int = i - containers
			var filled_soul: int = clampi(soul - soul_index * 2, 0, 2)
			ItemSymbol.paint_heart(self, center, pixel, soul_color, Color.TRANSPARENT, filled_soul)
