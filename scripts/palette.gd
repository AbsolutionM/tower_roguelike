extends RefCounted
class_name Palette

## Gemeinsame Farbwelt für das ganze Spiel.
## Alles - UI, Effekte, Gegner, Räume - zieht seine Farben von hier,
## damit nicht jedes Element seinen eigenen Farbton mitbringt.
##
## Aufbau: kühle, entsättigte Basis für Welt und Oberfläche,
## warme Goldtöne für alles, was der Spieler will (Beute, Fortschritt),
## und wenige klare Akzente für Gefahr, Magie und Natur.

# --- Basis (Welt, Flächen, Text) ---
const INK := Color("14121f")
const SHADOW := Color("1d1a2b")
const STONE := Color("2e2b40")
const STONE_LIGHT := Color("453f5c")
const MIST := Color("6b6484")
const BONE := Color("d8d2e0")

# --- Warm: Beute, Fortschritt, Spieler ---
const GOLD := Color("f2b134")
const AMBER := Color("ffd98a")
const EMBER := Color("e8663c")

# --- Kühl: Magie, Distanz, Technik ---
const TEAL := Color("3fd2c7")
const AZURE := Color("4a90d9")
const VIOLET := Color("8b6fd4")

# --- Natur: Schleim, Organisches ---
const MOSS := Color("6fbf5a")
const LIME := Color("a8e05f")

# --- Gefahr ---
const BLOOD := Color("d94f4f")
const ROSE := Color("ff8fa3")

## Seltenheitsfarben - aus derselben Palette statt frei gewählt.
const RARITY := [BONE, MOSS, AZURE, VIOLET, GOLD]

static func rarity(index: int) -> Color:
	return RARITY[clampi(index, 0, RARITY.size() - 1)]

## Leicht abgedunkelte Variante für Ränder und Schatten.
static func edge(color: Color) -> Color:
	return color.darkened(0.45)

## Aufgehellte Variante für Glanzlichter.
static func highlight(color: Color) -> Color:
	return color.lightened(0.35)
