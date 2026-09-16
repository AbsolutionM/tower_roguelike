extends SubViewport
class_name RigView

## Zeichnet Figur, Hände und Waffe in nativer Pixelauflösung und gibt das
## Bild an ein Sprite, das es dreifach vergrößert in die Welt stellt.
##
## Warum: Pixelkunst, die erst dreifach vergrößert und dann gedreht wird,
## bekommt schräge Kanten mit Ein-Pixel-Stufen und einen Umriss, der
## ebenfalls in Bildschirmpixeln zittert. Hier wird bei einem Pixel je
## Texturpixel gezeichnet, gedreht und umrandet - alles, was danach kommt,
## ist reine Vergrößerung. Jeder Pixel der Figur, der Hände, der Waffe und
## des Umrisses ist damit gleich groß, und der Umriss läuft um die
## gemeinsame Silhouette.
##
## Das Rig darin ist in Spielerkoordinaten aufgebaut (Sprites dreifach
## skaliert); die Leinwandtransformation teilt wieder durch drei.

## Bildschirmpixel je Texturpixel der Figur.
const PIXEL := 3.0
## Kantenlänge der Ansicht in Texturpixeln. Muss die längste Waffe samt
## Ausholen fassen: Faust bei ~7, Klinge bis 46, dazu ein Pixel Umriss.
const VIEW_TEXELS := 160

## Das Sprite in der Welt, das dieses Bild zeigt.
@export var display: Sprite2D

func _ready() -> void:
	size = Vector2i(VIEW_TEXELS, VIEW_TEXELS)
	transparent_bg = true
	disable_3d = true
	render_target_update_mode = SubViewport.UPDATE_ALWAYS
	canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	# Alles rastet auf ganze Texturpixel - eine Hand auf 6,8 Pixeln gibt es nicht.
	snap_2d_transforms_to_pixel = true
	# Spielerursprung in die Mitte, Spielerpixel durch drei.
	canvas_transform = Transform2D(
		Vector2(1.0 / PIXEL, 0.0), Vector2(0.0, 1.0 / PIXEL),
		Vector2(VIEW_TEXELS * 0.5, VIEW_TEXELS * 0.5))
	if display:
		display.texture = get_texture()
		display.scale = Vector2.ONE * PIXEL

## Weltkoordinaten eines Knotens aus dieser Ansicht: die Ansicht hängt am
## Spieler, ihr Rig steht im Spielerursprung.
func to_world(local: Transform2D) -> Transform2D:
	var carrier := get_parent() as Node2D
	return carrier.global_transform * local if carrier else local
