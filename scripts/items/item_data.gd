extends Resource
class_name ItemData

## HEART, SOUL_HEART und KEY wirken sofort beim Aufsammeln und landen nie
## im Beutel. `value` ist dann die Menge (halbe Herzen bzw. Schlüssel).
enum ItemType { MATERIAL, CURRENCY, ESSENCE, CONSUMABLE, HEART, SOUL_HEART, KEY }
enum Rarity { COMMON, UNCOMMON, RARE, EPIC, LEGENDARY }

const RARITY_NAMES := {
	Rarity.COMMON: "Gewöhnlich",
	Rarity.UNCOMMON: "Ungewöhnlich",
	Rarity.RARE: "Selten",
	Rarity.EPIC: "Episch",
	Rarity.LEGENDARY: "Legendär"
}

const RARITY_COLORS := {
	Rarity.COMMON: Palette.BONE,
	Rarity.UNCOMMON: Palette.MOSS,
	Rarity.RARE: Palette.AZURE,
	Rarity.EPIC: Palette.VIOLET,
	Rarity.LEGENDARY: Palette.GOLD
}

## Eindeutige ID - wird im Lager und im Spielstand gespeichert.
@export var item_id: String = ""
@export var item_name: String = "Item"
@export var icon: Texture2D
@export var max_stack: int = 99
@export_multiline var description: String = ""

@export_group("Verhalten")
@export var item_type: ItemType = ItemType.MATERIAL
@export var rarity: Rarity = Rarity.COMMON
@export var value: int = 1
@export var essence_id: String = ""

@export_group("Optik")
## Gezeichnete Form, solange kein `icon` gesetzt ist.
@export var symbol: ItemSymbol.Kind = ItemSymbol.Kind.GEL
## Wird für den prozeduralen Look benutzt, solange kein Icon gesetzt ist.
@export var color: Color = Palette.GOLD
@export var pickup_scale: float = 1.0

func get_rarity_name() -> String:
	return RARITY_NAMES.get(rarity, "Gewöhnlich")

func get_rarity_color() -> Color:
	return RARITY_COLORS.get(rarity, Color.WHITE)
