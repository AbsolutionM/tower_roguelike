extends Node

## Fortschritt über Runs hinweg: Währungen, Upgrades, freigeschaltete Waffen,
## Beutel (Run-Inventar) und Lager (Gesamt-Inventar). Wird in user:// gespeichert.

signal gold_changed(amount: int)
signal essence_changed(essence_id: String, amount: int)
signal upgrade_purchased(upgrade_id: String, level: int)
signal weapon_reinforced(weapon_id: String, level: int)
signal character_leveled(character_id: String, level: int)
signal loadout_changed
signal run_inventory_changed
signal stash_changed
signal bag_full

const SAVE_PATH := "user://savegame.json"
const MAX_RUN_SLOTS := 12
## So viele Beutel-Slots gehen beim Tod verloren.
const SLOTS_LOST_ON_DEATH := 4
## So viele Accessoires darf ein Charakter gleichzeitig tragen.
const MAX_ACCESSORY_SLOTS := 2

var gold: int = 0
var essences: Dictionary = {}
var upgrade_levels: Dictionary = {}
## weapon_id -> Schmiedestufe (0..Progression.MAX_REINFORCE)
var weapon_levels: Dictionary = {}
## character_id -> Kraftstufe (1..Progression.MAX_POWER_LEVEL)
var character_levels: Dictionary = {}
var owned_weapon_ids: Array[String] = []
var equipped_weapon_ids: Dictionary = {}
var owned_accessory_ids: Array[String] = []
## character_id -> Array[String]
var equipped_accessory_ids: Dictionary = {}
var selected_character_id: String = ""
var selected_tower_id: String = ""

## Beutel des laufenden Runs: Liste aus { "item_id": String, "count": int }
var run_slots: Array = []
## Lager: item_id -> Anzahl
var stash: Dictionary = {}
## Ergebnis des letzten Runs, wird vom Abschluss-Bildschirm gelesen.
var last_run_summary: Dictionary = {}

func _ready() -> void:
	load_game()
	_grant_starting_weapons()

# --- Währungen -------------------------------------------------------------

func add_gold(amount: int) -> void:
	gold += amount
	GameManager.count_gold(amount)
	gold_changed.emit(gold)

func spend_gold(amount: int) -> bool:
	if gold < amount:
		return false
	gold -= amount
	gold_changed.emit(gold)
	return true

func add_essence(essence_id: String, amount: int = 1) -> void:
	if essence_id.is_empty():
		return
	essences[essence_id] = int(essences.get(essence_id, 0)) + amount
	essence_changed.emit(essence_id, essences[essence_id])

func get_essence(essence_id: String) -> int:
	return int(essences.get(essence_id, 0))

func get_total_essence() -> int:
	var total: int = 0
	for key in essences:
		total += int(essences[key])
	return total

# --- Beutel (Run-Inventar) -------------------------------------------------

func get_used_slots() -> int:
	return run_slots.size()

func is_bag_full() -> bool:
	return run_slots.size() >= MAX_RUN_SLOTS

## Legt ein Item in den Beutel. False = kein Platz mehr.
func add_run_item(item: ItemData, count: int = 1) -> bool:
	if not item or item.item_id.is_empty():
		return false

	var remaining := count

	for slot in run_slots:
		if slot["item_id"] != item.item_id:
			continue
		var space: int = item.max_stack - int(slot["count"])
		if space <= 0:
			continue
		var moved: int = mini(space, remaining)
		slot["count"] = int(slot["count"]) + moved
		remaining -= moved
		if remaining <= 0:
			run_inventory_changed.emit()
			return true

	while remaining > 0:
		if is_bag_full():
			run_inventory_changed.emit()
			bag_full.emit()
			return false
		var moved: int = mini(item.max_stack, remaining)
		run_slots.append({"item_id": item.item_id, "count": moved})
		remaining -= moved

	run_inventory_changed.emit()
	return true

func clear_run_inventory() -> void:
	run_slots.clear()
	run_inventory_changed.emit()

# --- Lager (Gesamt-Inventar) ----------------------------------------------

func add_to_stash(item_id: String, count: int) -> void:
	if item_id.is_empty() or count <= 0:
		return
	stash[item_id] = int(stash.get(item_id, 0)) + count
	stash_changed.emit()

func get_stash_count(item_id: String) -> int:
	return int(stash.get(item_id, 0))

## Lager als Liste aus { "item": ItemData, "count": int }, seltenste zuerst.
func get_stash_entries() -> Array:
	var entries: Array = []
	for item_id in stash:
		var item := Database.get_item(str(item_id))
		if item:
			entries.append({"item": item, "count": int(stash[item_id])})
	entries.sort_custom(func(a, b): return a["item"].rarity > b["item"].rarity)
	return entries

# --- Run-Abschluss ---------------------------------------------------------

## Beendet den Run. Bei Tod gehen zufällige Slots verloren, der Rest wandert
## ins Lager. Gibt { "lost": Array, "kept": Array, "died": bool } zurück.
func end_run(died: bool) -> Dictionary:
	GameManager.end_run()
	var slots := run_slots.duplicate(true)
	var lost: Array = []

	if died:
		slots.shuffle()
		var lose_count: int = mini(SLOTS_LOST_ON_DEATH, slots.size())
		for i in lose_count:
			lost.append(slots.pop_back())

	var kept: Array = []
	for slot in slots:
		add_to_stash(str(slot["item_id"]), int(slot["count"]))
		kept.append(slot)

	run_slots.clear()
	run_inventory_changed.emit()

	last_run_summary = {"lost": lost, "kept": kept, "died": died}
	save_game()
	return last_run_summary

# --- Upgrades --------------------------------------------------------------

func get_upgrade_level(upgrade_id: String) -> int:
	return int(upgrade_levels.get(upgrade_id, 0))

## `prefix` trennt den Fortschritt bei geteilten Bäumen (z.B. pro Waffe).
func can_purchase(upgrade: UpgradeData, prefix: String = "") -> bool:
	if not upgrade:
		return false
	var level := get_upgrade_level(prefix + upgrade.upgrade_id)
	if level >= upgrade.max_level:
		return false
	for required_id in upgrade.requires:
		if get_upgrade_level(prefix + required_id) <= 0:
			return false
	if gold < upgrade.get_gold_cost(level):
		return false
	if not upgrade.essence_id.is_empty() and get_essence(upgrade.essence_id) < upgrade.get_essence_cost(level):
		return false
	return true

func purchase(upgrade: UpgradeData, prefix: String = "") -> bool:
	if not can_purchase(upgrade, prefix):
		return false
	var key := prefix + upgrade.upgrade_id
	var level := get_upgrade_level(key)
	gold -= upgrade.get_gold_cost(level)
	if not upgrade.essence_id.is_empty():
		essences[upgrade.essence_id] = get_essence(upgrade.essence_id) - upgrade.get_essence_cost(level)
		essence_changed.emit(upgrade.essence_id, essences[upgrade.essence_id])
	upgrade_levels[key] = level + 1
	gold_changed.emit(gold)
	upgrade_purchased.emit(key, level + 1)
	save_game()
	return true

# --- Schmieden (Waffen) ----------------------------------------------------

func get_weapon_level(weapon_id: String) -> int:
	return clampi(int(weapon_levels.get(weapon_id, 0)), 0, Progression.MAX_REINFORCE)

## Gold + Material für den nächsten Schmiedeschritt.
## { "gold": int, "item": ItemData, "item_id": String, "need": int, "have": int, "max": bool }
func get_reinforce_cost(weapon: WeaponData) -> Dictionary:
	if not weapon:
		return {"max": true}
	var level := get_weapon_level(weapon.weapon_id)
	if level >= Progression.MAX_REINFORCE:
		return {"max": true}

	var material := Progression.reinforce_material(level)
	var item_id := str(material["item_id"])
	return {
		"max": false,
		"level": level,
		"gold": Progression.reinforce_gold_cost(level),
		"item": Database.get_item(item_id),
		"item_id": item_id,
		"need": int(material["count"]),
		"have": get_stash_count(item_id)
	}

func can_reinforce(weapon: WeaponData) -> bool:
	if not weapon or not is_weapon_owned(weapon.weapon_id):
		return false
	var cost := get_reinforce_cost(weapon)
	if bool(cost.get("max", true)):
		return false
	return gold >= int(cost["gold"]) and int(cost["have"]) >= int(cost["need"])

func reinforce_weapon(weapon: WeaponData) -> bool:
	if not can_reinforce(weapon):
		return false
	var cost := get_reinforce_cost(weapon)
	gold -= int(cost["gold"])
	remove_from_stash(str(cost["item_id"]), int(cost["need"]))

	var level := get_weapon_level(weapon.weapon_id) + 1
	weapon_levels[weapon.weapon_id] = level

	gold_changed.emit(gold)
	Audio.play(Audio.ID_FORGE)
	weapon_reinforced.emit(weapon.weapon_id, level)
	loadout_changed.emit()
	save_game()
	return true

# --- Kraftstufen (Helden) --------------------------------------------------

func get_character_level(character_id: String) -> int:
	return clampi(
		int(character_levels.get(character_id, Progression.MIN_POWER_LEVEL)),
		Progression.MIN_POWER_LEVEL,
		Progression.MAX_POWER_LEVEL
	)

## { "gold": int, "essence": int, "have_essence": int, "max": bool }
func get_power_cost(character: CharacterData) -> Dictionary:
	if not character:
		return {"max": true}
	var level := get_character_level(character.character_id)
	if level >= Progression.MAX_POWER_LEVEL:
		return {"max": true}
	return {
		"max": false,
		"level": level,
		"gold": Progression.power_gold_cost(level),
		"essence": Progression.power_essence_cost(level),
		"have_essence": get_total_essence()
	}

func can_level_character(character: CharacterData) -> bool:
	if not character:
		return false
	var cost := get_power_cost(character)
	if bool(cost.get("max", true)):
		return false
	return gold >= int(cost["gold"]) and get_total_essence() >= int(cost["essence"])

func level_up_character(character: CharacterData) -> bool:
	if not can_level_character(character):
		return false
	var cost := get_power_cost(character)
	gold -= int(cost["gold"])
	_spend_essence(int(cost["essence"]))

	var level := get_character_level(character.character_id) + 1
	character_levels[character.character_id] = level

	gold_changed.emit(gold)
	Audio.play(Audio.ID_LEVEL_UP)
	character_leveled.emit(character.character_id, level)
	loadout_changed.emit()
	save_game()
	return true

## Essenz ist ein gemeinsamer Topf - abgezogen wird von der größten Sorte zuerst,
## damit seltene Essenzen für Spezielles übrig bleiben.
func _spend_essence(amount: int) -> void:
	var remaining := amount
	var keys: Array = essences.keys()
	keys.sort_custom(func(a, b): return int(essences[a]) > int(essences[b]))
	for key in keys:
		if remaining <= 0:
			break
		var available := int(essences[key])
		var taken: int = mini(available, remaining)
		essences[key] = available - taken
		remaining -= taken
		essence_changed.emit(str(key), essences[key])

# --- Waffen & Auswahl ------------------------------------------------------

func _grant_starting_weapons() -> void:
	for weapon_id in Database.get_starting_weapon_ids():
		unlock_weapon(weapon_id)

func is_weapon_owned(weapon_id: String) -> bool:
	return owned_weapon_ids.has(weapon_id)

func unlock_weapon(weapon_id: String) -> void:
	if weapon_id.is_empty() or owned_weapon_ids.has(weapon_id):
		return
	owned_weapon_ids.append(weapon_id)
	loadout_changed.emit()

func get_owned_weapons() -> Array[WeaponData]:
	var result: Array[WeaponData] = []
	for weapon_id in owned_weapon_ids:
		var weapon := Database.get_weapon(weapon_id)
		if weapon:
			result.append(weapon)
	return result

func set_selected_character(character_id: String) -> void:
	selected_character_id = character_id
	loadout_changed.emit()
	save_game()

func get_selected_character() -> CharacterData:
	var character := Database.get_character(selected_character_id)
	if character:
		return character
	var all := Database.get_characters()
	return all[0] if not all.is_empty() else null

func set_equipped_weapon(character_id: String, weapon_id: String) -> void:
	equipped_weapon_ids[character_id] = weapon_id
	loadout_changed.emit()
	save_game()

func get_equipped_weapon_id(character_id: String) -> String:
	if equipped_weapon_ids.has(character_id):
		var equipped := str(equipped_weapon_ids[character_id])
		if is_weapon_owned(equipped):
			return equipped

	# Startwaffe nur, wenn sie auch freigeschaltet ist - sonst irgendeine eigene.
	var character := Database.get_character(character_id)
	if character and character.starting_weapon and is_weapon_owned(character.starting_weapon.weapon_id):
		return character.starting_weapon.weapon_id
	return owned_weapon_ids[0] if not owned_weapon_ids.is_empty() else ""

# --- Accessoires -----------------------------------------------------------

func is_accessory_owned(accessory_id: String) -> bool:
	return owned_accessory_ids.has(accessory_id)

func unlock_accessory(accessory_id: String) -> void:
	if accessory_id.is_empty() or owned_accessory_ids.has(accessory_id):
		return
	owned_accessory_ids.append(accessory_id)
	loadout_changed.emit()

func get_owned_accessories() -> Array[AccessoryData]:
	var result: Array[AccessoryData] = []
	for accessory_id in owned_accessory_ids:
		var accessory := Database.get_accessory(accessory_id)
		if accessory:
			result.append(accessory)
	return result

func get_equipped_accessory_ids(character_id: String) -> Array:
	if not equipped_accessory_ids.has(character_id):
		return []
	return equipped_accessory_ids[character_id]

func is_accessory_equipped(character_id: String, accessory_id: String) -> bool:
	return get_equipped_accessory_ids(character_id).has(accessory_id)

func get_equipped_accessories(character_id: String) -> Array[AccessoryData]:
	var result: Array[AccessoryData] = []
	for accessory_id in get_equipped_accessory_ids(character_id):
		var accessory := Database.get_accessory(str(accessory_id))
		if accessory:
			result.append(accessory)
	return result

## An- und Ablegen. Ist kein Slot frei, fliegt das älteste Accessoire raus.
func toggle_accessory(character_id: String, accessory_id: String) -> void:
	var equipped: Array = get_equipped_accessory_ids(character_id).duplicate()
	if equipped.has(accessory_id):
		equipped.erase(accessory_id)
	else:
		equipped.append(accessory_id)
		while equipped.size() > MAX_ACCESSORY_SLOTS:
			equipped.pop_front()
	equipped_accessory_ids[character_id] = equipped
	loadout_changed.emit()
	save_game()

# --- Shop, Verkauf und Crafting -------------------------------------------

func buy_weapon(weapon: WeaponData) -> bool:
	if not weapon or weapon.shop_price <= 0 or is_weapon_owned(weapon.weapon_id):
		return false
	if not spend_gold(weapon.shop_price):
		return false
	unlock_weapon(weapon.weapon_id)
	Audio.play(Audio.ID_PURCHASE)
	save_game()
	return true

func buy_accessory(accessory: AccessoryData) -> bool:
	if not accessory or accessory.shop_price <= 0 or is_accessory_owned(accessory.accessory_id):
		return false
	if not spend_gold(accessory.shop_price):
		return false
	unlock_accessory(accessory.accessory_id)
	save_game()
	return true

func remove_from_stash(item_id: String, count: int) -> bool:
	if get_stash_count(item_id) < count:
		return false
	var remaining: int = get_stash_count(item_id) - count
	if remaining > 0:
		stash[item_id] = remaining
	else:
		stash.erase(item_id)
	stash_changed.emit()
	return true

## Verkauft Material aus dem Lager und gibt das erhaltene Gold zurück.
func sell_stash_item(item: ItemData, count: int = 1) -> int:
	if not item or count <= 0:
		return 0
	if not remove_from_stash(item.item_id, count):
		return 0
	var earned: int = maxi(item.value, 1) * count
	add_gold(earned)
	save_game()
	return earned

func craft(recipe: CraftingRecipe) -> bool:
	if not recipe or not recipe.can_craft():
		return false
	for entry in recipe.get_required():
		remove_from_stash(str(entry["item_id"]), int(entry["count"]))
	gold -= recipe.gold_cost
	gold_changed.emit(gold)
	unlock_weapon(recipe.result_weapon.weapon_id)
	save_game()
	return true

func get_equipped_weapon() -> WeaponData:
	var character := get_selected_character()
	if not character:
		return null
	var weapon := Database.get_weapon(get_equipped_weapon_id(character.character_id))
	return weapon if weapon else character.starting_weapon

func get_selected_tower() -> TowerData:
	var tower := Database.get_tower(selected_tower_id)
	if tower:
		return tower
	var all := Database.get_towers()
	return all[0] if not all.is_empty() else null

func set_selected_tower(tower_id: String) -> void:
	selected_tower_id = tower_id
	save_game()

# --- Speichern -------------------------------------------------------------

func save_game() -> void:
	var payload := {
		"gold": gold,
		"essences": essences,
		"upgrade_levels": upgrade_levels,
		"weapon_levels": weapon_levels,
		"character_levels": character_levels,
		"owned_weapon_ids": owned_weapon_ids,
		"equipped_weapon_ids": equipped_weapon_ids,
		"selected_character_id": selected_character_id,
		"selected_tower_id": selected_tower_id,
		"run_slots": run_slots,
		"stash": stash,
		"owned_accessory_ids": owned_accessory_ids,
		"equipped_accessory_ids": equipped_accessory_ids
	}
	var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if not file:
		return
	file.store_string(JSON.stringify(payload))
	file.close()

func load_game() -> void:
	if not FileAccess.file_exists(SAVE_PATH):
		return
	var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if not file:
		return
	var parsed = JSON.parse_string(file.get_as_text())
	file.close()
	if typeof(parsed) != TYPE_DICTIONARY:
		return

	gold = int(parsed.get("gold", 0))
	essences = parsed.get("essences", {})
	upgrade_levels = parsed.get("upgrade_levels", {})
	weapon_levels = parsed.get("weapon_levels", {})
	character_levels = parsed.get("character_levels", {})
	equipped_weapon_ids = parsed.get("equipped_weapon_ids", {})
	selected_character_id = str(parsed.get("selected_character_id", ""))
	selected_tower_id = str(parsed.get("selected_tower_id", ""))
	stash = parsed.get("stash", {})

	equipped_accessory_ids = parsed.get("equipped_accessory_ids", {})

	owned_weapon_ids.clear()
	for weapon_id in parsed.get("owned_weapon_ids", []):
		owned_weapon_ids.append(str(weapon_id))

	owned_accessory_ids.clear()
	for accessory_id in parsed.get("owned_accessory_ids", []):
		owned_accessory_ids.append(str(accessory_id))

	run_slots.clear()
	for slot in parsed.get("run_slots", []):
		if typeof(slot) == TYPE_DICTIONARY and slot.has("item_id"):
			run_slots.append({"item_id": str(slot["item_id"]), "count": int(slot.get("count", 1))})
