extends RefCounted
class_name WeaponUpgrades

## Pool der Waffen-Upgrades im Lauf. Ein Pool für alle Waffen, kleine Schritte.
## Karten kommen als Wahl (1 aus 3); die seltene Variante gibt den doppelten
## Wert. Werte mit Deckel stoppen dort - Schärfe und Takt am Maximum der
## aktuellen Waffenstufe. Ist der Deckel erreicht, verschwindet die Karte.
##
## Die Affinität der Waffe macht passende Karten stärker (siehe value_for).
## Gesammelt wird in RunState.run_upgrades, gelesen von PlayerStats.

const A := WeaponData.Affinity

## `cap`: Zahl = fester Deckel, "damage"/"speed" = Maximum der Waffenstufe.
## `flat`: Wert ist eine Anzahl statt eines Anteils.
const CARDS := [
	{"key": "sharpness", "name": "Schärfe", "text": "+%s Schaden", "value": 0.06, "cap": "damage", "affinity": A.NONE},
	{"key": "tempo", "name": "Takt", "text": "+%s Angriffstempo", "value": 0.05, "cap": "speed", "affinity": A.NONE},
	{"key": "precision", "name": "Präzision", "text": "+%s Krit-Chance", "value": 0.03, "cap": 0.40, "affinity": A.CRIT},
	{"key": "crit_power", "name": "Kritwucht", "text": "+%s Krit-Schaden", "value": 0.10, "cap": 1.0, "affinity": A.CRIT},
	{"key": "impact", "name": "Wucht", "text": "+%s Rückstoß", "value": 0.10, "cap": 0.60, "affinity": A.IMPACT},
	{"key": "reach", "name": "Reichweite", "text": "+%s Reichweite", "value": 0.05, "cap": 0.30, "affinity": A.NONE},
	{"key": "charge", "name": "Ladung", "text": "Sonderschlag %s Treffer früher", "value": 1.0, "cap": 5.0, "flat": true, "affinity": A.SPECIAL},
	{"key": "thirst", "name": "Durst", "text": "+%s Lebensraub", "value": 0.01, "cap": 0.06, "affinity": A.NONE},
	{"key": "burn", "name": "Glut", "text": "+%s Chance auf Brand", "value": 0.08, "cap": 0.50, "affinity": A.BURN},
	{"key": "frost", "name": "Frost", "text": "+%s Chance auf Verlangsamung", "value": 0.08, "cap": 0.50, "affinity": A.FROST},
	{"key": "poison", "name": "Gift", "text": "+%s Chance auf Gift-Stack", "value": 0.10, "cap": 0.60, "affinity": A.POISON},
	{"key": "shock", "name": "Blitz", "text": "+%s Chance auf Kettenblitz", "value": 0.06, "cap": 0.36, "affinity": A.SHOCK},
	{"key": "bleed", "name": "Blutung", "text": "+%s Blutungsaufbau", "value": 6.0, "cap": 36.0, "flat": true, "affinity": A.BLEED},
]

## Grundchance auf die seltene Karte, dazu Glück.
const RARE_CHANCE := 0.15
const UPGRADES_PER_EVOLUTION := 3

static func find_card(key: String) -> Dictionary:
	for card in CARDS:
		if card["key"] == key:
			return card
	return {}

## Deckel dieser Karte für diese Waffe.
static func cap_for(card: Dictionary, weapon: WeaponData) -> float:
	var cap = card["cap"]
	if cap is String:
		if not weapon:
			return 0.0
		if cap == "damage":
			return weapon.get_damage_max() / maxf(weapon.damage, 0.001) - 1.0
		return weapon.cooldown / maxf(weapon.get_cooldown_min(), 0.001) - 1.0
	return float(cap)

## Gesammelter Wert, schon am Deckel der aktuellen Waffenstufe abgeschnitten.
static func effective(key: String, weapon: WeaponData) -> float:
	var card := find_card(key)
	if card.is_empty():
		return 0.0
	return minf(float(RunState.run_upgrades.get(key, 0.0)), cap_for(card, weapon))

static func is_capped(card: Dictionary, weapon: WeaponData) -> bool:
	return float(RunState.run_upgrades.get(card["key"], 0.0)) >= cap_for(card, weapon) - 0.0001

## Wert einer Karte auf dieser Waffe. Krit-Affinität: Präzision und Kritwucht
## 50 % stärker. Sonderschlag-Affinität: Ladung zählt doppelt. Wucht-Affinität:
## Wucht 50 % stärker.
static func value_for(card: Dictionary, rare: bool, weapon: WeaponData) -> float:
	var value: float = float(card["value"]) * (2.0 if rare else 1.0)
	if weapon and card["affinity"] != A.NONE and weapon.affinity == card["affinity"]:
		match weapon.affinity:
			A.CRIT, A.IMPACT:
				value *= 1.5
			A.SPECIAL:
				value *= 2.0
	return value

## Passt die Karte zur Affinität der Waffe? Dann wird sie im Menü markiert.
static func matches_affinity(card: Dictionary, weapon: WeaponData) -> bool:
	return weapon != null and card["affinity"] != A.NONE and weapon.affinity == card["affinity"]

static func format_value(card: Dictionary, value: float) -> String:
	if card.get("flat", false):
		return "%d" % int(round(value))
	return "%d %%" % int(round(value * 100.0))

static func describe(card: Dictionary, value: float) -> String:
	return str(card["text"]) % format_value(card, value)

## `count` Karten ohne Doppelte, nur solche, deren Deckel noch nicht erreicht
## ist. `min_rare` = true erzwingt die seltene Variante (Feinschliff usw.).
static func roll(count: int, weapon: WeaponData, luck: float = 0.0, min_rare: bool = false) -> Array:
	var pool: Array = []
	for card in CARDS:
		if not is_capped(card, weapon):
			pool.append(card)
	pool.shuffle()
	var offers: Array = []
	for card in pool.slice(0, count):
		var rare: bool = min_rare or randf() < RARE_CHANCE + luck * 0.2
		offers.append({"card": card, "rare": rare, "value": value_for(card, rare, weapon)})
	return offers

## Nimmt ein Angebot an. Gibt true zurück, wenn die Waffe dabei evolviert.
static func apply(offer: Dictionary, weapon: WeaponData) -> void:
	var card: Dictionary = offer["card"]
	var key: String = card["key"]
	var current: float = float(RunState.run_upgrades.get(key, 0.0))
	RunState.run_upgrades[key] = minf(current + float(offer["value"]), cap_for(card, weapon))
	RunState.run_upgrade_count += 1
	RunState.run_upgrades_changed.emit()

# --- Evolution -------------------------------------------------------------

## Erste Stufe der Linie, zu der `weapon` gehört (rückwärts über next_tier).
static func line_root(weapon: WeaponData) -> WeaponData:
	var current := weapon
	for i in 8:
		var previous: WeaponData = null
		for other in Database.get_weapons():
			if other and other.next_tier == current:
				previous = other
				break
		if not previous:
			break
		current = previous
	return current

## Stufe 0..3 innerhalb der Linie.
static func tier_index(weapon: WeaponData) -> int:
	var root := line_root(weapon)
	var index := 0
	var current := root
	while current and current != weapon and index < 8:
		current = current.next_tier
		index += 1
	return index

const TIER_NUMERALS := ["I", "II", "III", "IV", "V"]

static func tier_name(weapon: WeaponData) -> String:
	return TIER_NUMERALS[clampi(tier_index(weapon), 0, TIER_NUMERALS.size() - 1)]

## Darf die Waffe jetzt evolvieren? Nach je drei Upgrades eine Stufe, aber nur
## bis zur höchsten Stufe, die in der Stadt gebaut ist (RunState.run_weapon_cap).
static func can_evolve(weapon: WeaponData) -> bool:
	if not weapon or not weapon.next_tier or weapon == RunState.run_weapon_cap:
		return false
	var needed: int = UPGRADES_PER_EVOLUTION * (tier_index(weapon) + 1)
	return RunState.run_upgrade_count >= needed

## Upgrades bis zur nächsten Evolution - für die Anzeige. -1 = keine mehr.
static func upgrades_until_evolution(weapon: WeaponData) -> int:
	if not weapon or not weapon.next_tier or weapon == RunState.run_weapon_cap:
		return -1
	return maxi(UPGRADES_PER_EVOLUTION * (tier_index(weapon) + 1) - RunState.run_upgrade_count, 0)
