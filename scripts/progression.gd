extends RefCounted
class_name Progression

## Alle Zahlen für den Langzeit-Fortschritt an einer Stelle.
## Menü und Kampf rechnen mit denselben Funktionen - was im Upgrade-Tab
## steht, ist exakt das, was im Turm passiert.
##
## Zwei getrennte Systeme:
##   Waffen  -> Schmiedestufen +0..+10 (Elden Ring): Material + Gold,
##              Werte wachsen mit der Stufe, Skalierungsnoten steigen mit.
##   Helden  -> Kraftstufen 1..11 (Brawl Stars): Gold + Essenz,
##              jede Stufe gibt pauschal Leben und Schaden, plus Freischaltungen.

# --- Waffen: Schmieden -----------------------------------------------------

const MAX_REINFORCE := 10

## Schaden pro Schmiedestufe (+10 = doppelter Grundschaden).
const REINFORCE_DAMAGE_PER_LEVEL := 0.10
## Skalierungsnoten wachsen mit der Stufe - genau wie in Elden Ring.
const REINFORCE_SCALING_PER_LEVEL := 0.05

const REINFORCE_BASE_GOLD := 45
const REINFORCE_GOLD_GROWTH := 1.42

## Welches Material welche Stufen verlangt. Wird von unten nach oben geprüft:
## der letzte Eintrag, dessen `from_level` erreicht ist, gilt.
const SMITHING_TIERS := [
	{"from_level": 0, "item_id": "iron_scrap", "base": 2, "per_level": 1},
	{"from_level": 3, "item_id": "crystal_shard", "base": 2, "per_level": 1},
	{"from_level": 7, "item_id": "boss_core", "base": 1, "per_level": 1}
]

static func reinforce_gold_cost(level: int) -> int:
	return int(round(REINFORCE_BASE_GOLD * pow(REINFORCE_GOLD_GROWTH, level)))

## { "item_id": String, "count": int } für den Sprung von `level` auf `level+1`.
static func reinforce_material(level: int) -> Dictionary:
	var tier: Dictionary = SMITHING_TIERS[0]
	for entry in SMITHING_TIERS:
		if level >= int(entry["from_level"]):
			tier = entry
	var steps: int = level - int(tier["from_level"])
	return {
		"item_id": str(tier["item_id"]),
		"count": int(tier["base"]) + steps * int(tier["per_level"])
	}

## Schadensfaktor allein aus der Schmiedestufe.
static func reinforce_damage_mult(level: int) -> float:
	return 1.0 + REINFORCE_DAMAGE_PER_LEVEL * float(level)

## Auch Reichweite und Standfestigkeit legen leicht zu, damit eine hoch
## geschmiedete Waffe sich anders anfühlt und nicht nur größere Zahlen macht.
static func reinforce_stagger_mult(level: int) -> float:
	return 1.0 + 0.06 * float(level)

# --- Helden: Kraftstufen ---------------------------------------------------

const MIN_POWER_LEVEL := 1
const MAX_POWER_LEVEL := 11

## Pauschaler Zuwachs pro Stufe auf Leben und Schaden.
const POWER_LEVEL_BONUS := 0.05

## Ab dieser Stufe gibt es das Gadget, ab jener die Sternenkraft.
const GADGET_LEVEL := 5
const STAR_POWER_LEVEL := 9

const POWER_BASE_GOLD := 40
const POWER_GOLD_GROWTH := 1.5
const POWER_BASE_ESSENCE := 2

static func power_gold_cost(level: int) -> int:
	return int(round(POWER_BASE_GOLD * pow(POWER_GOLD_GROWTH, maxi(level - 1, 0))))

static func power_essence_cost(level: int) -> int:
	return POWER_BASE_ESSENCE + maxi(level - 1, 0)

## Faktor auf Leben und Schaden bei Kraftstufe `level`.
static func power_level_mult(level: int) -> float:
	return 1.0 + POWER_LEVEL_BONUS * float(clampi(level, MIN_POWER_LEVEL, MAX_POWER_LEVEL) - 1)

static func unlocks_at(level: int) -> String:
	if level == GADGET_LEVEL:
		return "Gadget"
	if level == STAR_POWER_LEVEL:
		return "Sternenkraft"
	return ""
