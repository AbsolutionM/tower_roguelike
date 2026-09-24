extends Control
class_name ItemSymbol

## Gezeichnetes Platzhalter-Icon für Items - im Menü wie auf dem Boden.
## Solange kein `ItemData.icon` gesetzt ist, war überall nur ein farbiges
## Quadrat zu sehen; das hier gibt jedem Materialtyp eine eigene Silhouette.
##
## Gezeichnet wird über `paint()`, damit dieselbe Form auch von Node2D-Knoten
## (dem Bodenpickup) benutzt werden kann.

enum Kind { GEL, SCRAP, SHARD, COIN, FLASK, ORE, CORE, ESSENCE, HEART, HALF_HEART, KEY }

var kind: Kind = Kind.GEL
var tint: Color = Palette.BONE
## Kantenlänge des Symbols in Pixeln.
var symbol_size: float = 40.0

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	custom_minimum_size = Vector2.ONE * symbol_size

func _draw() -> void:
	paint(self, size * 0.5, symbol_size, kind, tint)

## Zeichnet das Symbol auf ein beliebiges Canvas.
static func paint(canvas: CanvasItem, center: Vector2, box: float, symbol: Kind, color: Color) -> void:
	var unit: float = maxf(box / 10.0, 1.0)
	var edge: Color = Palette.edge(color)
	var shine: Color = Palette.highlight(color)

	match symbol:
		Kind.GEL:
			_gel(canvas, center, unit, color, edge, shine)
		Kind.SCRAP:
			_scrap(canvas, center, unit, color, edge, shine)
		Kind.SHARD:
			_shard(canvas, center, unit, color, edge, shine)
		Kind.COIN:
			_coin(canvas, center, unit, color, edge, shine)
		Kind.FLASK:
			_flask(canvas, center, unit, color, edge, shine)
		Kind.ORE:
			_ore(canvas, center, unit, color, edge, shine)
		Kind.CORE:
			_core(canvas, center, unit, color, edge, shine)
		Kind.ESSENCE:
			_essence(canvas, center, unit, color, edge, shine)
		Kind.HEART:
			paint_heart(canvas, center, unit, color, Color.TRANSPARENT, 2)
		Kind.HALF_HEART:
			paint_heart(canvas, center, unit, color, Color.TRANSPARENT, 1)
		Kind.KEY:
			_key(canvas, center, unit, color, edge, shine)

static func _box(canvas: CanvasItem, center: Vector2, offset: Vector2, size: Vector2,
		unit: float, fill: Color, edge: Color) -> void:
	var rect := Rect2(center + offset * unit - size * unit * 0.5, size * unit)
	canvas.draw_rect(rect.grow(unit * 0.35), edge)
	canvas.draw_rect(rect, fill)

## Weicher Klumpen: breite Basis, schmalere Kuppe.
static func _gel(canvas: CanvasItem, c: Vector2, u: float, fill: Color, edge: Color, shine: Color) -> void:
	_box(canvas, c, Vector2(0, 1.2), Vector2(7, 4), u, fill, edge)
	_box(canvas, c, Vector2(0, -1.4), Vector2(5, 3), u, fill, edge)
	_box(canvas, c, Vector2(-1.4, -1.8), Vector2(1.4, 1.2), u, shine, shine)

## Kantiges Blech mit Nietenloch.
static func _scrap(canvas: CanvasItem, c: Vector2, u: float, fill: Color, edge: Color, shine: Color) -> void:
	_box(canvas, c, Vector2(-0.6, 0.4), Vector2(7, 4.5), u, fill, edge)
	_box(canvas, c, Vector2(2.4, -1.8), Vector2(3, 2.6), u, fill, edge)
	_box(canvas, c, Vector2(-2.0, 0.2), Vector2(1.2, 1.2), u, edge, edge)
	_box(canvas, c, Vector2(0.8, 1.6), Vector2(2.6, 0.8), u, shine, shine)

## Kristall: gestapelte Bänder, oben und unten schmal.
static func _shard(canvas: CanvasItem, c: Vector2, u: float, fill: Color, edge: Color, shine: Color) -> void:
	_box(canvas, c, Vector2(0, -3.2), Vector2(1.6, 2), u, fill, edge)
	_box(canvas, c, Vector2(0, -1.2), Vector2(3.6, 2.4), u, fill, edge)
	_box(canvas, c, Vector2(0, 1.4), Vector2(4.6, 3), u, fill, edge)
	_box(canvas, c, Vector2(0, 3.6), Vector2(2.6, 1.6), u, fill, edge)
	_box(canvas, c, Vector2(-1.0, 0.2), Vector2(0.9, 4), u, shine, shine)

static func _coin(canvas: CanvasItem, c: Vector2, u: float, fill: Color, edge: Color, shine: Color) -> void:
	PixelDraw.disc(canvas, c, u * 3.6, u, edge)
	PixelDraw.disc(canvas, c, u * 3.0, u, fill)
	PixelDraw.ring(canvas, c, u * 1.9, u, edge, 1)
	_box(canvas, c, Vector2(-1.3, -1.5), Vector2(1.1, 1.1), u, shine, shine)

## Flasche: Hals, Bauch, Glanzstreifen.
static func _flask(canvas: CanvasItem, c: Vector2, u: float, fill: Color, edge: Color, shine: Color) -> void:
	_box(canvas, c, Vector2(0, -3.4), Vector2(2, 1.4), u, Palette.STONE_LIGHT, edge)
	_box(canvas, c, Vector2(0, -2.0), Vector2(1.4, 1.6), u, edge, edge)
	_box(canvas, c, Vector2(0, 1.4), Vector2(5.4, 5), u, fill, edge)
	_box(canvas, c, Vector2(-1.5, 1.2), Vector2(0.9, 2.6), u, shine, shine)

## Brocken mit eingesprengten Adern.
static func _ore(canvas: CanvasItem, c: Vector2, u: float, fill: Color, edge: Color, shine: Color) -> void:
	_box(canvas, c, Vector2(0, 0.6), Vector2(7, 5), u, Palette.STONE_LIGHT, edge)
	_box(canvas, c, Vector2(-1.6, -0.6), Vector2(1.6, 1.6), u, fill, edge)
	_box(canvas, c, Vector2(1.4, 1.4), Vector2(1.4, 1.4), u, fill, edge)
	_box(canvas, c, Vector2(1.8, -1.4), Vector2(1.0, 1.0), u, shine, shine)

## Bosskern: Ring mit leuchtender Mitte.
static func _core(canvas: CanvasItem, c: Vector2, u: float, fill: Color, edge: Color, shine: Color) -> void:
	PixelDraw.disc(canvas, c, u * 4.0, u, edge)
	PixelDraw.disc(canvas, c, u * 3.4, u, Palette.STONE)
	PixelDraw.ring(canvas, c, u * 3.4, u, fill, 1)
	PixelDraw.disc(canvas, c, u * 1.6, u, fill)
	_box(canvas, c, Vector2(0, 0), Vector2(0.9, 0.9), u, shine, shine)

## Essenz: schwebender Tropfen mit Funken.
static func _essence(canvas: CanvasItem, c: Vector2, u: float, fill: Color, edge: Color, shine: Color) -> void:
	_box(canvas, c, Vector2(0, -3.0), Vector2(1.2, 1.6), u, fill, edge)
	_box(canvas, c, Vector2(0, -1.4), Vector2(2.6, 1.8), u, fill, edge)
	PixelDraw.disc(canvas, c + Vector2(0.0, u * 1.2), u * 3.0, u, fill)
	PixelDraw.ring(canvas, c + Vector2(0.0, u * 1.2), u * 3.0, u, edge, 1)
	_box(canvas, c, Vector2(-1.2, 0.6), Vector2(0.9, 0.9), u, shine, shine)
	_box(canvas, c, Vector2(3.2, -2.4), Vector2(0.8, 0.8), u, shine, shine)
	_box(canvas, c, Vector2(-3.4, 1.8), Vector2(0.7, 0.7), u, shine, shine)

## Herz als Pixelraster, 9 x 8 Pixel. Die linke Hälfte sind die Spalten 0-4.
const HEART_ROWS := [
	".XX...XX.",
	"XXXX.XXXX",
	"XXXXXXXXX",
	"XXXXXXXXX",
	".XXXXXXX.",
	"..XXXXX..",
	"...XXX...",
	"....X....",
]

## Zeichnet ein Herz mit Rand. `filled_halves`: 2 = voll, 1 = linke Hälfte,
## 0 = leer. Der ungefüllte Teil bekommt `empty` (transparent = weglassen).
## Wird vom Bodenpickup und von der Herzleiste im HUD benutzt.
static func paint_heart(canvas: CanvasItem, center: Vector2, pixel: float, fill: Color,
		empty: Color, filled_halves: int) -> void:
	var rows: int = HEART_ROWS.size()
	var columns: int = str(HEART_ROWS[0]).length()
	var origin := center - Vector2(columns, rows) * pixel * 0.5
	var outline: Color = Palette.INK
	var shine: Color = Palette.highlight(fill)

	# Rand: jedes Rasterfeld, das an ein Herzfeld grenzt, selbst aber keins ist.
	for y in range(-1, rows + 1):
		for x in range(-1, columns + 1):
			if _heart_cell(x, y):
				continue
			var touches := false
			for offset in [Vector2i(-1, 0), Vector2i(1, 0), Vector2i(0, -1), Vector2i(0, 1)]:
				if _heart_cell(x + offset.x, y + offset.y):
					touches = true
					break
			if touches:
				canvas.draw_rect(Rect2(origin + Vector2(x, y) * pixel, Vector2.ONE * pixel), outline)

	for y in rows:
		for x in columns:
			if not _heart_cell(x, y):
				continue
			var is_filled: bool = filled_halves >= 2 or (filled_halves == 1 and x <= 4)
			var color: Color = fill if is_filled else empty
			if color.a <= 0.0:
				continue
			canvas.draw_rect(Rect2(origin + Vector2(x, y) * pixel, Vector2.ONE * pixel), color)

	# Glanzpunkt oben links, nur auf gefüllten Herzen.
	if filled_halves > 0:
		canvas.draw_rect(Rect2(origin + Vector2(1, 1) * pixel, Vector2.ONE * pixel), shine)
		canvas.draw_rect(Rect2(origin + Vector2(2, 1) * pixel, Vector2.ONE * pixel), shine)
		canvas.draw_rect(Rect2(origin + Vector2(1, 2) * pixel, Vector2.ONE * pixel), shine)

static func _heart_cell(x: int, y: int) -> bool:
	if y < 0 or y >= HEART_ROWS.size():
		return false
	var row: String = HEART_ROWS[y]
	if x < 0 or x >= row.length():
		return false
	return row[x] == "X"

## Schlüssel: Ring als Griff, Schaft nach rechts, zwei Bartzähne.
static func _key(canvas: CanvasItem, c: Vector2, u: float, fill: Color, edge: Color, shine: Color) -> void:
	_box(canvas, c, Vector2(1.4, 0), Vector2(5.6, 1.4), u, fill, edge)
	_box(canvas, c, Vector2(3.4, 1.4), Vector2(1.0, 1.6), u, fill, edge)
	_box(canvas, c, Vector2(1.8, 1.2), Vector2(1.0, 1.2), u, fill, edge)
	PixelDraw.disc(canvas, c + Vector2(-2.6, 0.0) * u, u * 2.6, u, edge)
	PixelDraw.disc(canvas, c + Vector2(-2.6, 0.0) * u, u * 2.0, u, fill)
	PixelDraw.disc(canvas, c + Vector2(-2.6, 0.0) * u, u * 0.9, u, edge)
	_box(canvas, c, Vector2(-3.4, -1.0), Vector2(0.8, 0.8), u, shine, shine)
