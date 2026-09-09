extends Resource
class_name GameDatabase

## Zentrale Inhaltsliste. Neue Charaktere/Waffen/Türme hier eintragen,
## dann tauchen sie automatisch in allen Menüs auf.

@export var characters: Array[CharacterData] = []
@export var weapons: Array[WeaponData] = []
@export var towers: Array[TowerData] = []
## Alles, was im Beutel oder Lager landen kann.
@export var items: Array[ItemData] = []
@export var accessories: Array[AccessoryData] = []
@export var recipes: Array[CraftingRecipe] = []
## Waffen, die der Spieler von Anfang an besitzt.
@export var starting_weapon_ids: Array[String] = []
