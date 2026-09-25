extends RefCounted
class_name PowerUps

## Power-ups aus Level-ups im Lauf. Anders als Relikte sind sie stapelbar
## (bis `max`) und kleine Schritte; anders als Waffen-Upgrades wirken sie auf
## den Helden. Sie verfallen am Laufende wie die XP.
##
## Werte laufen wie bei den Relikten über add/mult auf PlayerStats, einmal
## pro Stapel. Herzen wirken sofort beim Nehmen (RunState.add_power_up).

const POWER_UPS := [
	{"id": "might", "name": "Kraft", "text": "+8 % Schaden", "max": 5, "mult": {"damage_mult": 1.08}},
	{"id": "haste", "name": "Flinkheit", "text": "+6 % Angriffstempo", "max": 5, "mult": {"attack_speed_mult": 1.06}},
	{"id": "swift", "name": "Leichtfuß", "text": "+12 Lauftempo", "max": 4, "add": {"move_speed": 12.0}},
	{"id": "keen_eye", "name": "Scharfes Auge", "text": "+4 % Krit-Chance", "max": 5, "add": {"crit_chance": 0.04}},
	{"id": "brutal", "name": "Wucht der Krits", "text": "+15 % Krit-Schaden", "max": 4, "add": {"crit_damage": 0.15}},
	{"id": "tough", "name": "Zähigkeit", "text": "+1 Rüstung", "max": 5, "add": {"armor": 1.0}},
	{"id": "vitality", "name": "Vitalität", "text": "+1 Herzcontainer", "max": 3, "containers": 1},
	{"id": "soul_shard", "name": "Seelensplitter", "text": "+1 Seelenherz", "max": 4, "soul": 1},
	{"id": "mend", "name": "Heilung", "text": "2 rote Herzen auffüllen", "max": 99, "heal": 4},
	{"id": "magnet", "name": "Magnet", "text": "+30 Sammelradius", "max": 3, "add": {"pickup_radius": 30.0}},
	{"id": "dash", "name": "Sprintkraft", "text": "Dash-Abklingzeit -8 %", "max": 4, "mult": {"dash_cooldown_mult": 0.92}},
	{"id": "focus", "name": "Fokus", "text": "Fähigkeit-Abklingzeit -8 %", "max": 4, "mult": {"ability_cooldown_mult": 0.92}},
	{"id": "leech", "name": "Blutdurst", "text": "+1 % Lebensraub", "max": 4, "add": {"lifesteal": 0.01}},
	{"id": "fortune", "name": "Glückspilz", "text": "Glück +1", "max": 3, "add": {"luck": 0.05}},
]

static func find(id: String) -> Dictionary:
	for power in POWER_UPS:
		if power["id"] == id:
			return power
	return {}

static func stacks(id: String) -> int:
	return int(RunState.run_power_ups.get(id, 0))

## `count` verschiedene Power-ups, die noch nicht voll gestapelt sind.
## Heilung kommt nur, wenn rote Herzen fehlen.
static func roll(count: int, health: PlayerHealth = null) -> Array:
	var pool: Array = []
	for power in POWER_UPS:
		if stacks(power["id"]) >= int(power["max"]):
			continue
		if power.has("heal") and (not health or health.is_red_full()):
			continue
		pool.append(power)
	pool.shuffle()
	return pool.slice(0, count)
