extends Resource
class_name FXTheme

## Zentrale Stelle für Effekt-Texturen. Alle Slots sind optional:
## solange sie leer sind, werden die Effekte als Pixelblöcke gezeichnet.
## Legst du hier Texturen rein, benutzen sie automatisch alle Effekte im Spiel.

## Kantenlänge eines Effekt-Pixels in Weltkoordinaten.
@export var pixel_size: float = 4.0

@export_group("Texturen")
@export var spark_texture: Texture2D
@export var ring_texture: Texture2D
@export var puff_texture: Texture2D
@export var muzzle_texture: Texture2D
@export var shadow_texture: Texture2D
