extends RefCounted
class_name Relics

## Relikte aus dem Ideensheet. Sie wirken auf den Helden, egal welche Waffe,
## und verfallen am Laufende. Werte-Relikte laufen wie StarPowerData über
## stat_add / stat_mult auf PlayerStats; Effekt-Relikte fragen die Spielteile
## mit RunState.has_relic(id) ab.
##
## Herzcontainer und Seelenherzen wirken sofort beim Aufheben (PlayerHealth),
## nicht über PlayerStats - sonst gäbe es sie erst im nächsten Lauf.
##
## Nicht im Pool, weil das System dahinter noch fehlt: Bombenbeutel (Bomben),
## Zwillingsseele (Geister-Doppel).

enum Rarity { COMMON, UNCOMMON, RARE, EPIC }

const RARITY_NAMES := ["Gewöhnlich", "Ungewöhnlich", "Selten", "Episch"]
const RARITY_WEIGHTS := [50.0, 30.0, 15.0, 5.0]
## "Luck +1" im Sheet entspricht so viel PlayerStats.luck.
const LUCK_POINT := 0.05

const RELICS := [
	# --- Werte-Relikte ---
	{"id": "iron_tooth", "name": "Eisenzahn", "rarity": Rarity.COMMON, "text": "+3 Schaden", "add": {"flat_damage": 3.0}},
	{"id": "power_ring", "name": "Kraftring", "rarity": Rarity.COMMON, "text": "+10 % Schaden", "mult": {"damage_mult": 1.10}},
	{"id": "feather_boots", "name": "Federstiefel", "rarity": Rarity.COMMON, "text": "+20 Tempo", "add": {"move_speed": 20.0}},
	{"id": "zeal_glove", "name": "Handschuh des Eifers", "rarity": Rarity.COMMON, "text": "+10 % Angriffstempo", "mult": {"attack_speed_mult": 1.10}},
	{"id": "leather_armor", "name": "Lederpanzer", "rarity": Rarity.COMMON, "text": "+2 Rüstung", "add": {"armor": 2.0}},
	{"id": "glass_eye", "name": "Glasauge", "rarity": Rarity.COMMON, "text": "+5 % Krit-Chance", "add": {"crit_chance": 0.05}},
	{"id": "collector_bag", "name": "Sammlerbeutel", "rarity": Rarity.COMMON, "text": "+40 Sammelradius", "add": {"pickup_radius": 40.0}},
	{"id": "rabbit_foot", "name": "Hasenpfote", "rarity": Rarity.COMMON, "text": "Glück +1", "add": {"luck": LUCK_POINT}},
	{"id": "hourglass_shard", "name": "Sanduhrsplitter", "rarity": Rarity.UNCOMMON, "text": "Dash-Abklingzeit -20 %", "mult": {"dash_cooldown_mult": 0.8}},
	{"id": "focus_stone", "name": "Fokusstein", "rarity": Rarity.UNCOMMON, "text": "Fähigkeit-Abklingzeit -20 %", "mult": {"ability_cooldown_mult": 0.8}},
	{"id": "vampire_tooth", "name": "Vampirzahn", "rarity": Rarity.UNCOMMON, "text": "+3 % Lebensraub", "add": {"lifesteal": 0.03}},
	{"id": "moss_amulet", "name": "Moosamulett", "rarity": Rarity.UNCOMMON, "text": "+0,5 Regeneration", "add": {"health_regen": 0.5}},
	{"id": "thorn_vest", "name": "Dornenweste", "rarity": Rarity.UNCOMMON, "text": "+25 Dornen", "add": {"thorns": 25.0}},
	{"id": "shadow_cloak", "name": "Schattenumhang", "rarity": Rarity.UNCOMMON, "text": "+8 % Ausweichen", "add": {"dodge_chance": 0.08}},
	{"id": "red_jewel", "name": "Rotes Juwel", "rarity": Rarity.UNCOMMON, "text": "+1 Herzcontainer", "containers": 1},
	{"id": "blue_candle", "name": "Blaue Kerze", "rarity": Rarity.UNCOMMON, "text": "+2 Seelenherzen", "soul": 2},
	{"id": "executioner_axe", "name": "Scharfrichterbeil", "rarity": Rarity.RARE, "text": "+50 % Krit-Schaden", "add": {"crit_damage": 0.5}},
	{"id": "berserker_blood", "name": "Berserkerblut", "rarity": Rarity.RARE, "text": "+25 % Schaden, -2 Rüstung", "mult": {"damage_mult": 1.25}, "add": {"armor": -2.0}},
	{"id": "east_wind", "name": "Wind des Ostens", "rarity": Rarity.RARE, "text": "+35 Tempo, Dash -15 %", "add": {"move_speed": 35.0}, "mult": {"dash_cooldown_mult": 0.85}},
	{"id": "giant_crest", "name": "Wappen des Riesen", "rarity": Rarity.RARE, "text": "+2 Herzcontainer, -15 Tempo", "containers": 2, "add": {"move_speed": -15.0}},
	{"id": "clover", "name": "Kleeblatt", "rarity": Rarity.RARE, "text": "Glück +3", "add": {"luck": LUCK_POINT * 3.0}},
	{"id": "star_shard", "name": "Sternensplitter", "rarity": Rarity.EPIC, "text": "Schaden, Tempo und Krit ×1,12", "mult": {"damage_mult": 1.12, "attack_speed_mult": 1.12, "move_speed": 1.12, "crit_chance": 1.12, "crit_damage": 1.12}},
	{"id": "dragon_heart", "name": "Drachenherz", "rarity": Rarity.EPIC, "text": "+2 Herzcontainer, +1 Regeneration", "containers": 2, "add": {"health_regen": 1.0}},
	{"id": "glass_cannon", "name": "Glaskanone", "rarity": Rarity.EPIC, "text": "+60 % Schaden, -2 Herzcontainer", "mult": {"damage_mult": 1.6}, "containers": -2},
	# --- Effekt-Relikte ---
	{"id": "crystal_armor", "name": "Kristallpanzer", "rarity": Rarity.UNCOMMON, "text": "Kristallherz: Schild über allen Herzen, lädt pro Raum ½ nach"},
	{"id": "pocket_watch", "name": "Taschenuhr", "rarity": Rarity.UNCOMMON, "text": "+3 s pro Raum", "add": {"bonus_room_time": 3.0}},
	{"id": "key_ring", "name": "Schlüsselbund", "rarity": Rarity.COMMON, "text": "+3 Schlüssel, Goldtruhen bieten 1 Karte mehr"},
	{"id": "gold_greed", "name": "Goldgier", "rarity": Rarity.UNCOMMON, "text": "Gold ×1,5; jeder Treffer kostet 3 Gold"},
	{"id": "ore_finder", "name": "Erzspürer", "rarity": Rarity.UNCOMMON, "text": "+1 Erz je Ader"},
	{"id": "adrenaline", "name": "Adrenalin", "rarity": Rarity.RARE, "text": "Unter 2 Herzen: +30 % Schaden und Tempo"},
	{"id": "perfectionist", "name": "Perfektionist", "rarity": Rarity.RARE, "text": "Raum ohne Treffer: +1 Upgrade-Splitter"},
	{"id": "bounty", "name": "Kopfgeld", "rarity": Rarity.RARE, "text": "Erster Kill im Raum droppt ein Herz"},
	{"id": "time_thief", "name": "Zeitdieb", "rarity": Rarity.RARE, "text": "Jeder Elite-Kill +3 s Raumzeit"},
	{"id": "phantom_step", "name": "Phantomschritt", "rarity": Rarity.RARE, "text": "Dash hinterlässt eine Klinge (30 Schaden)"},
	{"id": "chain_reaction", "name": "Kettenreaktion", "rarity": Rarity.RARE, "text": "Getötete Gegner explodieren zu 20 % (40 Schaden)"},
	{"id": "rebirth", "name": "Wiedergeburt", "rarity": Rarity.EPIC, "text": "Einmal pro Lauf: beim Tod mit 2 Herzen aufstehen"},
	{"id": "midas_hand", "name": "Midas-Hand", "rarity": Rarity.EPIC, "text": "5 % der Kills werden zu Gold (20)"},
	{"id": "tower_heart", "name": "Turmherz-Splitter", "rarity": Rarity.EPIC, "text": "Jede neue Etage +5 % Schaden (max. 5)"},
]

const RARITY_COLORS := [Palette.BONE, Palette.MOSS, Palette.AZURE, Palette.VIOLET]

static func find(id: String) -> Dictionary:
	for relic in RELICS:
		if relic["id"] == id:
			return relic
	return {}

static func rarity_name(relic: Dictionary) -> String:
	return RARITY_NAMES[int(relic["rarity"])]

static func rarity_color(relic: Dictionary) -> Color:
	return RARITY_COLORS[int(relic["rarity"])]

## `count` verschiedene Relikte, die man noch nicht hat. Glück verschiebt
## die Gewichte zu den seltenen. `min_rarity` für Stacheltruhen.
static func roll(count: int, luck: float = 0.0, min_rarity: int = Rarity.COMMON) -> Array:
	var pool: Array = []
	for relic in RELICS:
		if not RunState.has_relic(relic["id"]) and int(relic["rarity"]) >= min_rarity:
			pool.append(relic)
	var picked: Array = []
	for i in count:
		if pool.is_empty():
			break
		var total: float = 0.0
		for relic in pool:
			total += _weight(relic, luck)
		var pick: float = randf() * total
		for relic in pool:
			pick -= _weight(relic, luck)
			if pick <= 0.0:
				picked.append(relic)
				pool.erase(relic)
				break
	return picked

static func _weight(relic: Dictionary, luck: float) -> float:
	var rarity: int = int(relic["rarity"])
	return RARITY_WEIGHTS[rarity] * (1.0 + luck * 2.0 * float(rarity))
