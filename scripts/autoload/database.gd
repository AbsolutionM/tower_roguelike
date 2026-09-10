extends Node

## Lädt die Inhaltsdatenbank und liefert Nachschlage-Funktionen.

const DATABASE_PATH := "res://resources/database/game_database.tres"

var data: GameDatabase

func _ready() -> void:
	data = load(DATABASE_PATH) as GameDatabase
	if not data:
		push_error("GameDatabase konnte nicht geladen werden: " + DATABASE_PATH)

func get_characters() -> Array[CharacterData]:
	if data:
		return data.characters
	var empty: Array[CharacterData] = []
	return empty

func get_weapons() -> Array[WeaponData]:
	if data:
		return data.weapons
	var empty: Array[WeaponData] = []
	return empty

func get_towers() -> Array[TowerData]:
	if data:
		return data.towers
	var empty: Array[TowerData] = []
	return empty

func get_items() -> Array[ItemData]:
	if data:
		return data.items
	var empty: Array[ItemData] = []
	return empty

func get_item(item_id: String) -> ItemData:
	for item in get_items():
		if item and item.item_id == item_id:
			return item
	return null

func get_accessories() -> Array[AccessoryData]:
	if data:
		return data.accessories
	var empty: Array[AccessoryData] = []
	return empty

func get_accessory(accessory_id: String) -> AccessoryData:
	for accessory in get_accessories():
		if accessory and accessory.accessory_id == accessory_id:
			return accessory
	return null

func get_recipes() -> Array[CraftingRecipe]:
	if data:
		return data.recipes
	var empty: Array[CraftingRecipe] = []
	return empty

func get_starting_weapon_ids() -> Array[String]:
	if data:
		return data.starting_weapon_ids
	var empty: Array[String] = []
	return empty

func get_character(character_id: String) -> CharacterData:
	for character in get_characters():
		if character and character.character_id == character_id:
			return character
	return null

func get_weapon(weapon_id: String) -> WeaponData:
	for weapon in get_weapons():
		if weapon and weapon.weapon_id == weapon_id:
			return weapon
	return null

func get_tower(tower_id: String) -> TowerData:
	for tower in get_towers():
		if tower and tower.tower_id == tower_id:
			return tower
	return null
