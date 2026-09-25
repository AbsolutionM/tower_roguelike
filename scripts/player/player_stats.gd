extends Node
class_name PlayerStats

## Rechnet Attribute + Upgrades + Accessoires + Waffen-Affinität zusammen.
## Alle anderen Systeme fragen nur noch hier nach.

signal stats_changed
## Ein Treffer ist gelandet - laedt den Sonderschlag der Waffe auf.
signal hit_landed

@export var character_data: CharacterData

## Herzcontainer (rote Herzen) in ganzen Herzen.
var heart_containers: int = 3
## Seelenherzen (blau), mit denen der Held startet - in ganzen Herzen.
var soul_hearts: int = 0
var move_speed: float = 200.0
var damage_mult: float = 1.0
var flat_damage: float = 0.0
var attack_speed_mult: float = 1.0
var dash_cooldown_mult: float = 1.0
var pickup_radius: float = 95.0
var crit_chance: float = 0.05
var crit_damage: float = 2.0
var armor: float = 0.0
var luck: float = 0.0
## Anteil des ausgeteilten Schadens, der als Heilung zurückkommt (0-1).
## Sammelt sich in PlayerHealth, bis ein halbes Herz voll ist.
var lifesteal: float = 0.0
## Heilpunkte pro Sekunde - PlayerHealth macht daraus halbe Herzen.
var health_regen: float = 0.0
## Schaden, der bei einem Treffer an nahe Gegner zurückgeht.
var thorns: float = 0.0
## Chance, einen Treffer komplett zu vermeiden (0-1).
var dodge_chance: float = 0.0
## Multiplikator auf die Abklingzeit der Fähigkeit.
var ability_cooldown_mult: float = 1.0
## Zusätzliche Sekunden pro Raum (Relikte).
var bonus_room_time: float = 0.0

## Baut die Werte für Menüs, ohne dass ein Spieler in der Szene existiert.
static func preview(character: CharacterData) -> PlayerStats:
	var stats := PlayerStats.new()
	stats.character_data = character
	stats.recalculate()
	return stats

func _ready() -> void:
	add_to_group("player_stats")
	RunState.loadout_changed.connect(recalculate)
	RunState.run_upgrades_changed.connect(recalculate)
	Weather.weather_changed.connect(_on_weather_changed)
	recalculate()

func _on_weather_changed(_weather: WeatherData) -> void:
	recalculate()

func recalculate() -> void:
	_apply_base()
	_apply_power_level()
	_apply_weapon_upgrades()
	_apply_accessories()
	_apply_weather()
	stats_changed.emit()

## Kraftstufe des Helden: pauschal mehr Schaden pro Stufe, Herzcontainer
## auf bestimmten Stufen, dazu die Freischaltungen auf Stufe 5 und 9.
func _apply_power_level() -> void:
	if not character_data:
		return
	var level := RunState.get_character_level(character_data.character_id)
	damage_mult *= Progression.power_level_mult(level)
	heart_containers += Progression.bonus_hearts(level)

	for star in character_data.get_unlocked_stars(level):
		for stat_name in star.stat_add:
			_add_stat(str(stat_name), float(star.stat_add[stat_name]))
		for stat_name in star.stat_mult:
			_mult_stat(str(stat_name), float(star.stat_mult[stat_name]))

## Eigenschaften der ausgerüsteten Waffe und ihres Upgrade-Baums.
func _apply_weapon_upgrades() -> void:
	var weapon := RunState.get_active_weapon()
	if not weapon:
		return

	lifesteal += weapon.lifesteal + upgrade("thirst", weapon)
	move_speed += weapon.move_speed_bonus
	crit_damage += weapon.crit_damage_bonus
	# Gewicht 3.0 ist neutral - alles darüber bremst, alles darunter macht flink.
	move_speed -= (weapon.weight - 3.0) * 6.0
	armor += weapon.armor_bonus

## Wetter wirkt zuletzt, damit es auf allem anderen aufsetzt.
func _apply_weather() -> void:
	move_speed *= Weather.get_player_speed_mult()
	damage_mult *= Weather.get_player_damage_mult()
	health_regen += Weather.get_player_regen_bonus()
	pickup_radius *= Weather.get_pickup_radius_mult()

## Ein gelandeter Treffer, unabhängig vom Schaden. Treibt den Sonderschlag an.
func report_hit() -> void:
	hit_landed.emit()

## Wird von Waffen und Fähigkeiten gemeldet - treibt den Lebensraub an.
func report_damage(amount: float) -> void:
	if lifesteal <= 0.0 or amount <= 0.0:
		return
	var parent := get_parent()
	if not parent:
		return
	var health = parent.get_node_or_null("PlayerHealth")
	if health and health.has_method("heal_silent"):
		health.heal_silent(amount * lifesteal)

func _apply_base() -> void:
	if character_data:
		heart_containers = character_data.red_hearts
		soul_hearts = character_data.soul_hearts
		move_speed = character_data.base_speed + character_data.agility * 5.0
		damage_mult = 1.0 + character_data.power * 0.04
		attack_speed_mult = 1.0 + character_data.agility * 0.02
		crit_chance = 0.03 + character_data.fortune * 0.01
		luck = character_data.fortune * 0.015
		armor = float(character_data.toughness - 5) * 1.6
		ability_cooldown_mult = clampf(1.0 - float(character_data.focus - 5) * 0.045, 0.5, 1.5)
	else:
		heart_containers = 3
		soul_hearts = 0
		move_speed = 200.0
		damage_mult = 1.0
		attack_speed_mult = 1.0
		crit_chance = 0.05
		luck = 0.0
		armor = 0.0
		ability_cooldown_mult = 1.0

	flat_damage = 0.0
	dash_cooldown_mult = 1.0
	pickup_radius = 95.0
	crit_damage = 2.0
	lifesteal = 0.0
	health_regen = 0.0
	thorns = 0.0
	dodge_chance = 0.0
	bonus_room_time = 0.0

func _apply_accessories() -> void:
	if not character_data:
		return
	for accessory in RunState.get_equipped_accessories(character_data.character_id):
		heart_containers += accessory.heart_container_bonus
		soul_hearts += accessory.soul_heart_bonus
		move_speed += accessory.flat_speed_bonus
		flat_damage += accessory.flat_damage_bonus
		damage_mult *= accessory.damage_multiplier
		lifesteal += accessory.lifesteal_bonus
		health_regen += accessory.regen_bonus
		crit_chance += accessory.crit_bonus
		pickup_radius += accessory.pickup_radius_bonus
		armor += accessory.armor_bonus

func _add_stat(stat_name: String, value: float) -> void:
	var current = get(stat_name)
	if current == null:
		push_warning("PlayerStats hat kein Feld '%s'" % stat_name)
		return
	if typeof(current) == TYPE_INT:
		set(stat_name, int(current) + int(round(value)))
	else:
		set(stat_name, float(current) + value)

func _mult_stat(stat_name: String, factor: float) -> void:
	var current = get(stat_name)
	if current == null:
		push_warning("PlayerStats hat kein Feld '%s'" % stat_name)
		return
	if typeof(current) == TYPE_INT:
		set(stat_name, int(round(float(current) * factor)))
	else:
		set(stat_name, float(current) * factor)

## Kombiniert Spielerwerte, Waffen-Upgrades und Charakter-Affinität.
func get_weapon_modifiers(weapon: WeaponData) -> Dictionary:
	var mods := {
		"damage": damage_mult,
		"attack_speed": attack_speed_mult,
		"crit": crit_chance,
		"flat": flat_damage
	}
	if not weapon:
		return mods

	if character_data:
		var affinity := character_data.get_affinity(weapon.category)
		if affinity:
			mods["damage"] = float(mods["damage"]) * affinity.damage_mult
			mods["attack_speed"] = float(mods["attack_speed"]) * affinity.attack_speed_mult
			mods["crit"] = float(mods["crit"]) + affinity.crit_bonus

	mods["attack_speed"] = float(mods["attack_speed"]) * weapon.attack_speed_mult * (1.0 + upgrade("tempo", weapon))
	mods["crit"] = float(mods["crit"]) + weapon.crit_bonus + upgrade("precision", weapon)
	return mods

## Wert eines Waffen-Upgrades aus dem laufenden Lauf, am Stufen-Deckel
## abgeschnitten. Außerhalb des Turms immer 0.
func upgrade(key: String, weapon: WeaponData = null) -> float:
	if not GameManager.run_active:
		return 0.0
	return WeaponUpgrades.effective(key, weapon if weapon else RunState.get_active_weapon())

## Schmiedestufe einer Waffe. Im Lauf gilt für jede Stufe der Linie die
## Schmiedestufe der Stadtwaffe - sonst wäre das Schmieden mit der
## Evolution verloren.
func weapon_level(weapon: WeaponData) -> int:
	if GameManager.run_active and RunState.run_weapon_cap and WeaponUpgrades.line_root(weapon) == WeaponUpgrades.line_root(RunState.run_weapon_cap):
		return RunState.get_weapon_level(RunState.run_weapon_cap.weapon_id)
	return RunState.get_weapon_level(weapon.weapon_id)

## Grundschaden der Waffe inklusive Schmiedestufe und Attributskalierung.
## Einzige Stelle, an der Waffenschaden entsteht - Menü und Kampf fragen hier.
func get_weapon_base_damage(weapon: WeaponData) -> float:
	if not weapon:
		return 0.0
	return weapon.get_effective_damage(character_data, weapon_level(weapon)) * (1.0 + upgrade("sharpness", weapon))

## Fertige Werteübersicht für die Menüs: [{ "name": String, "value": String }, ...]
func describe_sheet() -> Array:
	var weapon := RunState.get_active_weapon()
	var attack_speed: float = attack_speed_mult
	var crit: float = crit_chance
	var damage_display: float = flat_damage * damage_mult
	if weapon:
		var mods := get_weapon_modifiers(weapon)
		attack_speed = float(mods["attack_speed"])
		crit = float(mods["crit"])
		damage_display = (get_weapon_base_damage(weapon) + float(mods["flat"])) * float(mods["damage"])

	var attacks_per_second: float = 0.0
	if weapon and weapon.cooldown > 0.0:
		attacks_per_second = attack_speed / weapon.cooldown

	return [
		{"name": "Angriff", "value": "%.1f" % damage_display},
		{"name": "Angriffe/s", "value": "%.2f" % attacks_per_second},
		{"name": "Krit-Chance", "value": "%.0f%%" % (clampf(crit, 0.0, 1.0) * 100.0)},
		{"name": "Krit-Schaden", "value": "%.0f%%" % (crit_damage * 100.0)},
		{"name": "Herzen", "value": describe_hearts()},
		{"name": "Tempo", "value": "%.0f" % move_speed},
		{"name": "Rüstung", "value": "%.1f" % armor},
		{"name": "Lebensraub", "value": "%.1f%%" % (lifesteal * 100.0)},
		{"name": "Regeneration", "value": _describe_regen()},
		{"name": "Ausweichen", "value": "%.0f%%" % (dodge_chance * 100.0)},
		{"name": "Dornen", "value": "%.0f" % thorns},
		{"name": "Sammelradius", "value": "%.0f" % pickup_radius},
		{"name": "Fähigkeit", "value": "%.0f%%" % (ability_cooldown_mult * 100.0)},
		{"name": "Glück", "value": "%.0f%%" % (luck * 100.0)}
	]

## Regeneration als "½ Herz alle 40s" - Punkte pro Sekunde sagen mit Herzen nichts mehr.
func _describe_regen() -> String:
	if health_regen <= 0.0:
		return "-"
	return "½ Herz/%.0fs" % (PlayerHealth.HALF_HEART_VALUE / health_regen)

## "3 rot + 1 blau" - für Menüs.
func describe_hearts() -> String:
	var parts: Array[String] = []
	if heart_containers > 0:
		parts.append("%d rot" % heart_containers)
	if soul_hearts > 0:
		parts.append("%d blau" % soul_hearts)
	return " + ".join(parts) if not parts.is_empty() else "-"

## Liefert { "damage": float, "crit": bool } für einen Waffen-Grundschaden.
func compute_damage(base_damage: float, weapon: WeaponData = null) -> Dictionary:
	var mods := get_weapon_modifiers(weapon)
	var damage: float = (base_damage + float(mods["flat"])) * float(mods["damage"])
	var is_crit: bool = randf() < clampf(float(mods["crit"]), 0.0, 1.0)
	if is_crit:
		damage *= crit_damage + upgrade("crit_power", weapon)
	return {"damage": damage, "crit": is_crit}

# --- Trefferwirkungen der Waffen-Upgrades ----------------------------------

## Von Klinge und Geschoss gerufen, wenn ein Gegner getroffen wurde.
## Würfelt Brand, Frost, Gift und Kettenblitz aus und baut Blutung auf.
## Die Affinität der Waffe verstärkt ihr Element wie im Ideensheet.
func on_weapon_hit(target: Node, damage: float) -> void:
	if not (target is Enemy) or not is_instance_valid(target) or target.is_dying:
		return
	var weapon := RunState.get_active_weapon()
	if not weapon:
		return
	var aff: int = weapon.affinity
	var A := WeaponData.Affinity
	var enemy: Enemy = target

	if randf() < upgrade("burn", weapon):
		var strong: bool = aff == A.BURN
		enemy.status.apply_burn(4.0 * (1.5 if strong else 1.0), 4.0 if strong else 3.0)
		enemy.status.burn_spreads = strong
	if randf() < upgrade("frost", weapon):
		var strong_frost: bool = aff == A.FROST
		enemy.status.apply_slow(0.6 if strong_frost else 0.75, 2.0, 3 if strong_frost else 0, 1.0)
	if randf() < upgrade("poison", weapon):
		enemy.status.apply_poison(8 if aff == A.POISON else 5)
	if randf() < upgrade("shock", weapon):
		_chain_lightning(enemy, damage, 3 if aff == A.SHOCK else 2, 0.6 if aff == A.SHOCK else 0.4)

	var buildup: float = weapon.bleed_buildup + upgrade("bleed", weapon)
	if buildup > 0.0 and enemy.status.add_bleed(buildup, 70.0 if aff == A.BLEED else 100.0):
		FX.hit_spark(enemy.global_position, Palette.BLOOD, 10)
		enemy.take_status_damage(damage, Palette.BLOOD)

func _chain_lightning(from: Enemy, damage: float, jumps: int, factor: float) -> void:
	var hit: Array = [from]
	var current: Node2D = from
	for i in jumps:
		var next: Node2D = null
		var best: float = 180.0
		for other in get_tree().get_nodes_in_group("enemies"):
			if hit.has(other) or not is_instance_valid(other):
				continue
			var distance: float = current.global_position.distance_to(other.global_position)
			if distance < best:
				best = distance
				next = other
		if not next:
			return
		FX.lightning(current.global_position, next.global_position, Palette.TEAL)
		next.take_status_damage(damage * factor, Palette.TEAL)
		hit.append(next)
		current = next
