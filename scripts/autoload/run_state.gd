extends Node

## Fortschritt über Runs hinweg: Währungen, Upgrades, freigeschaltete Waffen,
## Beutel (Run-Inventar) und Lager (Gesamt-Inventar). Wird in user:// gespeichert.

signal gold_changed(amount: int)
signal essence_changed(essence_id: String, amount: int)
signal weapon_reinforced(weapon_id: String, level: int)
signal character_leveled(character_id: String, level: int)
signal loadout_changed
signal run_inventory_changed
signal stash_changed
signal bag_full
signal keys_changed(amount: int)
signal sparks_changed(amount: int)
signal shards_changed(amount: int)
signal run_upgrades_changed
## Jemand bietet Waffen-Upgrades an (Splitter, Amboss, Goldtruhe) - der HUD
## zeigt die Kartenwahl. `source` steht als Überschrift darüber.
signal upgrade_offer_requested(count: int, min_rare: bool, source: String)
signal weapon_evolved(weapon: WeaponData)
signal relics_changed
## Erfahrung im Lauf: aktuelle XP, XP bis zum nächsten Level, Level.
signal xp_changed(xp: int, needed: int, level: int)
## Level-up - der HUD zeigt die Power-up-Wahl.
signal level_up_offer_requested(level: int)
## Relikt-Wahl (Mini-Boss, Goldtruhe): `relic_count` Relikte und
## `upgrade_count` Waffen-Upgrades nebeneinander, eins davon wird genommen.
signal relic_offer_requested(relic_count: int, upgrade_count: int, source: String, min_rarity: int)

const SAVE_PATH := "user://savegame.json"
const MAX_RUN_SLOTS := 12
## Wer stirbt, verliert diesen Anteil der Beute aus dem Lauf (Beutel, Gold, Essenz).
const DEATH_LOOT_LOSS := 0.5
## So viele Accessoires darf ein Charakter gleichzeitig tragen.
const MAX_ACCESSORY_SLOTS := 2

var gold: int = 0
## Schlüssel gelten nur für den laufenden Run und werden nicht gespeichert.
var keys: int = 0
## Turmfunken: Währung nur für den Lauf (Amboss, später Händler, Glücksrad).
var sparks: int = 0
## Upgrade-Splitter: 5 Stück = 1 freies Waffen-Upgrade.
var shards: int = 0
const SHARDS_PER_UPGRADE := 5
## Waffen-Upgrades dieses Laufs: Karten-Schlüssel -> gesammelter Wert.
var run_upgrades: Dictionary = {}
var run_upgrade_count: int = 0
## Waffe im Lauf: startet auf Stufe I der Linie und evolviert bis zur
## höchsten in der Stadt gebauten Stufe (`run_weapon_cap`).
var run_weapon: WeaponData
var run_weapon_cap: WeaponData
## Erfahrung gilt nur im Turm und beginnt jeden Lauf wieder bei Level 1.
var run_xp: int = 0
var run_level: int = 1
## Power-ups aus Level-ups: ID -> Stapel.
var run_power_ups: Dictionary = {}
## Relikte dieses Laufs (IDs aus Relics.RELICS).
var run_relics: Array[String] = []
## Wiedergeburt greift nur einmal pro Lauf.
var rebirth_used: bool = false
## Etage, auf der der Turmherz-Splitter aufgehoben wurde.
var tower_heart_floor: int = 0
var essences: Dictionary = {}
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
## Türme, deren Hauptboss schon besiegt wurde - öffnen den jeweils nächsten.
var cleared_tower_ids: Array[String] = []
## Was im laufenden Lauf an Gold und Essenz dazukam - davon geht beim Tod
## die Hälfte verloren.
var run_gold: int = 0
var run_essences: Dictionary = {}

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
	if GameManager.run_active:
		run_gold += amount
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
	if GameManager.run_active:
		run_essences[essence_id] = int(run_essences.get(essence_id, 0)) + amount
	essence_changed.emit(essence_id, essences[essence_id])

func get_total_essence() -> int:
	var total: int = 0
	for key in essences:
		total += int(essences[key])
	return total

# --- Schlüssel -------------------------------------------------------------

## Setzt alles zurück, was nur einen Run lang lebt.
func start_run() -> void:
	keys = 0
	sparks = 0
	shards = 0
	run_upgrades.clear()
	run_upgrade_count = 0
	run_relics.clear()
	run_xp = 0
	run_level = 1
	run_power_ups.clear()
	xp_changed.emit(run_xp, xp_needed(run_level), run_level)
	rebirth_used = false
	tower_heart_floor = 0
	relics_changed.emit()
	sparks_changed.emit(sparks)
	shards_changed.emit(shards)
	run_gold = 0
	run_essences.clear()
	keys_changed.emit(keys)

func add_keys(amount: int) -> void:
	if amount <= 0:
		return
	keys += amount
	keys_changed.emit(keys)

func add_sparks(amount: int) -> void:
	if amount <= 0:
		return
	sparks += amount
	sparks_changed.emit(sparks)

func spend_sparks(amount: int) -> bool:
	if sparks < amount:
		return false
	sparks -= amount
	sparks_changed.emit(sparks)
	return true

## Fünf Splitter werden sofort zu einer Upgrade-Wahl.
func add_shards(amount: int) -> void:
	if amount <= 0:
		return
	shards += amount
	while shards >= SHARDS_PER_UPGRADE:
		shards -= SHARDS_PER_UPGRADE
		upgrade_offer_requested.emit(3, false, "Upgrade-Splitter")
	shards_changed.emit(shards)

# --- Erfahrung und Power-ups ----------------------------------------------

## XP bis zum nächsten Level: 20, 32, 44, ... - ein voller Lauf reicht für
## etwa 12-15 Level.
static func xp_needed(level: int) -> int:
	return 20 + 12 * (level - 1)

func add_xp(amount: int) -> void:
	if amount <= 0 or not GameManager.run_active:
		return
	run_xp += amount
	while run_xp >= xp_needed(run_level):
		run_xp -= xp_needed(run_level)
		run_level += 1
		level_up_offer_requested.emit(run_level)
	xp_changed.emit(run_xp, xp_needed(run_level), run_level)

## Nimmt ein Power-up. Herzen wirken sofort, Werte über PlayerStats.
func add_power_up(power_id: String) -> void:
	var power := PowerUps.find(power_id)
	if power.is_empty():
		return
	run_power_ups[power_id] = int(run_power_ups.get(power_id, 0)) + 1
	var player := get_tree().get_first_node_in_group("player")
	var health: PlayerHealth = player.get_node_or_null("PlayerHealth") if player else null
	if health:
		if int(power.get("containers", 0)) > 0:
			health.add_container(int(power["containers"]))
		if int(power.get("soul", 0)) > 0:
			health.add_soul_hearts(int(power["soul"]) * 2)
		if int(power.get("heal", 0)) > 0:
			health.heal_hearts(int(power["heal"]))
	loadout_changed.emit()

# --- Relikte ---------------------------------------------------------------

func has_relic(relic_id: String) -> bool:
	return GameManager.run_active and run_relics.has(relic_id)

## Nimmt ein Relikt. Herzen und Schlüssel wirken sofort, Werte über
## PlayerStats (loadout_changed löst die Neuberechnung aus).
func add_relic(relic_id: String) -> void:
	var relic := Relics.find(relic_id)
	if relic.is_empty() or run_relics.has(relic_id):
		return
	run_relics.append(relic_id)
	var player := get_tree().get_first_node_in_group("player")
	var health: PlayerHealth = player.get_node_or_null("PlayerHealth") if player else null
	if health:
		var containers: int = int(relic.get("containers", 0))
		if containers > 0:
			health.add_container(containers)
		elif containers < 0:
			health.remove_container(-containers)
		if int(relic.get("soul", 0)) > 0:
			health.add_soul_hearts(int(relic["soul"]) * 2)
		if relic_id == "crystal_armor":
			health.add_shield(2)
	if relic_id == "key_ring":
		add_keys(3)
	if relic_id == "tower_heart":
		tower_heart_floor = GameManager.current_floor
	relics_changed.emit()
	loadout_changed.emit()

## Laufbeginn: die Stadtwaffe gibt die Obergrenze, gestartet wird auf Stufe I.
func begin_weapon_run(town_weapon: WeaponData) -> WeaponData:
	run_weapon_cap = town_weapon
	run_weapon = WeaponUpgrades.line_root(town_weapon) if town_weapon else null
	return run_weapon

## Die Waffe, die gerade zählt: im Turm die Laufwaffe, in der Stadt die ausgerüstete.
func get_active_weapon() -> WeaponData:
	if GameManager.run_active and run_weapon:
		return run_weapon
	return get_equipped_weapon()

## False = kein Schlüssel da.
func spend_key() -> bool:
	if keys <= 0:
		return false
	keys -= 1
	keys_changed.emit(keys)
	return true

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

## Beendet den Run. Bei Tod geht die Hälfte jedes Stapels im Beutel verloren,
## dazu die Hälfte des im Lauf verdienten Golds und der Essenz. Der Rest
## wandert ins Lager. Gibt { "lost", "kept", "died", "gold_lost", "victory" } zurück.
func end_run(died: bool, victory: bool = false) -> Dictionary:
	GameManager.end_run()
	var lost: Array = []
	var kept: Array = []
	var gold_lost: int = 0

	for slot in run_slots:
		var count: int = int(slot["count"])
		var lose: int = int(floor(float(count) * DEATH_LOOT_LOSS)) if died else 0
		if lose > 0:
			lost.append({"item_id": slot["item_id"], "count": lose})
		if count - lose > 0:
			add_to_stash(str(slot["item_id"]), count - lose)
			kept.append({"item_id": slot["item_id"], "count": count - lose})

	if died:
		gold_lost = mini(int(floor(float(run_gold) * DEATH_LOOT_LOSS)), gold)
		gold -= gold_lost
		gold_changed.emit(gold)
		for essence_id in run_essences:
			var lose: int = mini(int(floor(float(run_essences[essence_id]) * DEATH_LOOT_LOSS)), int(essences.get(essence_id, 0)))
			essences[essence_id] = int(essences.get(essence_id, 0)) - lose
			essence_changed.emit(str(essence_id), essences[essence_id])

	run_slots.clear()
	run_gold = 0
	run_essences.clear()
	run_inventory_changed.emit()

	last_run_summary = {"lost": lost, "kept": kept, "died": died, "gold_lost": gold_lost, "victory": victory}
	save_game()
	return last_run_summary

# --- Türme -----------------------------------------------------------------

func mark_tower_cleared(tower_id: String) -> void:
	if tower_id.is_empty() or cleared_tower_ids.has(tower_id):
		return
	cleared_tower_ids.append(tower_id)
	save_game()

## Der erste Turm ist immer offen, jeder weitere erst nach dem Sieg im vorigen.
func is_tower_unlocked(tower: TowerData) -> bool:
	if not tower:
		return false
	var towers := Database.get_towers()
	var index := towers.find(tower)
	if index <= 0 or tower.unlocked:
		return true
	var previous: TowerData = towers[index - 1]
	return previous != null and cleared_tower_ids.has(previous.tower_id)

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

# --- Waffenstufen (Linie aufwerten) ---------------------------------------

## Was der Schritt zur nächsten Stufe kostet, oder leer am Ende der Linie.
## { "gold": int, "materials": [{ "item", "item_id", "need", "have" }] }
func get_tier_cost(weapon: WeaponData) -> Dictionary:
	if not weapon or not weapon.next_tier:
		return {}
	var materials: Array = []
	for entry in weapon.get_tier_materials():
		var item_id := str(entry["item_id"])
		materials.append({
			"item": Database.get_item(item_id), "item_id": item_id,
			"need": int(entry["count"]), "have": get_stash_count(item_id)
		})
	return {"gold": weapon.tier_gold, "materials": materials}

func can_advance_tier(weapon: WeaponData) -> bool:
	if not weapon or not weapon.next_tier or not is_weapon_owned(weapon.weapon_id):
		return false
	var cost := get_tier_cost(weapon)
	if gold < int(cost["gold"]):
		return false
	for material in cost["materials"]:
		if int(material["have"]) < int(material["need"]):
			return false
	return true

## Tauscht die Waffe gegen ihre nächste Stufe. Die Schmiedestufe wandert mit,
## und wer die alte trug, trägt danach die neue.
func advance_weapon_tier(weapon: WeaponData) -> bool:
	if not can_advance_tier(weapon):
		return false
	var cost := get_tier_cost(weapon)
	gold -= int(cost["gold"])
	for material in cost["materials"]:
		remove_from_stash(str(material["item_id"]), int(material["need"]))

	var next: WeaponData = weapon.next_tier
	owned_weapon_ids.erase(weapon.weapon_id)
	if not owned_weapon_ids.has(next.weapon_id):
		owned_weapon_ids.append(next.weapon_id)
	weapon_levels[next.weapon_id] = get_weapon_level(weapon.weapon_id)
	weapon_levels.erase(weapon.weapon_id)
	for character_id in equipped_weapon_ids.keys():
		if str(equipped_weapon_ids[character_id]) == weapon.weapon_id:
			equipped_weapon_ids[character_id] = next.weapon_id

	gold_changed.emit(gold)
	Audio.play(Audio.ID_FORGE)
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
		"weapon_levels": weapon_levels,
		"character_levels": character_levels,
		"owned_weapon_ids": owned_weapon_ids,
		"equipped_weapon_ids": equipped_weapon_ids,
		"selected_character_id": selected_character_id,
		"selected_tower_id": selected_tower_id,
		"cleared_tower_ids": cleared_tower_ids,
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
	weapon_levels = parsed.get("weapon_levels", {})
	character_levels = parsed.get("character_levels", {})
	equipped_weapon_ids = parsed.get("equipped_weapon_ids", {})
	selected_character_id = str(parsed.get("selected_character_id", ""))
	selected_tower_id = str(parsed.get("selected_tower_id", ""))
	cleared_tower_ids.clear()
	for tower_id in parsed.get("cleared_tower_ids", []):
		cleared_tower_ids.append(str(tower_id))
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
