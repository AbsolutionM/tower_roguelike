extends CanvasLayer
class_name UpgradePicker

## Kartenwahl: Waffen-Upgrades und/oder Relikte, eins davon wird genommen.
## Pausiert das Spiel.
## Kommen mehrere Angebote kurz hintereinander (fünf Splitter plus Amboss),
## stellt der HUD sie in eine Schlange - es ist immer nur eine Wahl offen.

signal closed

var count: int = 3
var min_rare: bool = false
## Relikte, die zusätzlich zur Wahl stehen, und ihre Mindestseltenheit.
var relic_count: int = 0
var min_rarity: int = 0
## Power-ups aus einem Level-up.
var power_count: int = 0
var source: String = ""

var _offers: Array = []
var _weapon: WeaponData

func _ready() -> void:
	layer = 110
	process_mode = Node.PROCESS_MODE_ALWAYS
	get_tree().paused = true
	_weapon = RunState.get_active_weapon()
	var stats := get_tree().get_first_node_in_group("player_stats")
	var luck: float = stats.luck if stats else 0.0
	_offers = []
	var player := get_tree().get_first_node_in_group("player")
	var health: PlayerHealth = player.get_node_or_null("PlayerHealth") if player else null
	for power in PowerUps.roll(power_count, health):
		_offers.append({"type": "power", "power": power})
	for relic in Relics.roll(relic_count, luck, min_rarity):
		_offers.append({"type": "relic", "relic": relic})
	for offer in WeaponUpgrades.roll(count, _weapon, luck, min_rare):
		offer["type"] = "upgrade"
		_offers.append(offer)
	if _offers.is_empty():
		# Alles am Deckel - statt einer leeren Wahl gibt es Funken zurück.
		RunState.add_sparks(15)
		_close()
		return
	_build()

func _build() -> void:
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	UIKit.apply_pixel_theme(root)
	add_child(root)

	var dim := ColorRect.new()
	dim.color = Color(Palette.INK, 0.97)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(dim)

	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 36)
	margin.add_theme_constant_override("margin_right", 36)
	root.add_child(margin)

	var column := UIKit.make_column(14)
	column.alignment = BoxContainer.ALIGNMENT_CENTER
	margin.add_child(column)

	column.add_child(UIKit.make_label(source if not source.is_empty() else "Waffen-Upgrade", 34, Palette.GOLD, HORIZONTAL_ALIGNMENT_CENTER))
	if power_count > 0:
		column.add_child(UIKit.make_label("Level %d - wähle ein Power-up. Es gilt bis zum Ende des Laufs." % RunState.run_level, 17, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_CENTER, true))
	elif count > 0:
		column.add_child(UIKit.make_label(_weapon_line(), 17, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_CENTER, true))
	else:
		column.add_child(UIKit.make_label("Relikte wirken bis zum Ende des Laufs.", 17, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_CENTER, true))
	column.add_child(UIKit.make_spacer(8.0))

	for offer in _offers:
		column.add_child(_make_card(offer))

## "Knochenschwert · Stufe I · noch 2 bis zur Evolution"
func _weapon_line() -> String:
	if not _weapon:
		return ""
	var line := "%s · Stufe %s" % [_weapon.weapon_name, WeaponUpgrades.tier_name(_weapon)]
	var left := WeaponUpgrades.upgrades_until_evolution(_weapon)
	if left > 0:
		line += " · noch %d bis zur Evolution" % left
	elif left == 0:
		line += " · evolviert mit dieser Karte"
	else:
		line += " · höchste gebaute Stufe"
	if _weapon.affinity != WeaponData.Affinity.NONE:
		line += "\nAffinität: " + str(WeaponData.AFFINITY_NAMES[_weapon.affinity])
	return line

func _make_card(offer: Dictionary) -> Control:
	if offer.get("type", "upgrade") == "relic":
		return _make_relic_card(offer["relic"])
	if offer.get("type", "upgrade") == "power":
		return _make_power_card(offer["power"])
	var card: Dictionary = offer["card"]
	var rare: bool = offer["rare"]
	var accent: Color = Palette.VIOLET if rare else Palette.TEAL
	var matches := WeaponUpgrades.matches_affinity(card, _weapon)

	var title: String = str(card["name"])
	if rare:
		title += "  (selten)"
	if matches:
		title += "  ★"
	var text := WeaponUpgrades.describe(card, float(offer["value"]))
	var have: float = float(RunState.run_upgrades.get(card["key"], 0.0))
	var cap := WeaponUpgrades.cap_for(card, _weapon)
	text += "\nBisher %s · Deckel %s" % [WeaponUpgrades.format_value(card, have), WeaponUpgrades.format_value(card, cap)]

	var button := UIKit.make_button("%s\n%s" % [title, text], 17, accent)
	button.custom_minimum_size = Vector2(0.0, 132.0)
	button.alignment = HORIZONTAL_ALIGNMENT_CENTER
	button.pressed.connect(func() -> void: _pick(offer))
	return button

func _make_relic_card(relic: Dictionary) -> Control:
	var accent := Relics.rarity_color(relic)
	var text := "Relikt: %s  (%s)\n%s" % [relic["name"], Relics.rarity_name(relic), relic["text"]]
	var button := UIKit.make_button(text, 17, accent)
	button.custom_minimum_size = Vector2(0.0, 132.0)
	button.alignment = HORIZONTAL_ALIGNMENT_CENTER
	button.pressed.connect(func() -> void: _pick({"type": "relic", "relic": relic}))
	return button

func _make_power_card(power: Dictionary) -> Control:
	var have := PowerUps.stacks(power["id"])
	var text := "%s\n%s" % [power["name"], power["text"]]
	if int(power["max"]) < 99:
		text += "\nStufe %d / %d" % [have + 1, int(power["max"])]
	var button := UIKit.make_button(text, 17, Palette.GOLD)
	button.custom_minimum_size = Vector2(0.0, 132.0)
	button.alignment = HORIZONTAL_ALIGNMENT_CENTER
	button.pressed.connect(func() -> void: _pick({"type": "power", "power": power}))
	return button

func _pick(offer: Dictionary) -> void:
	var label: String
	if offer.get("type", "upgrade") == "power":
		RunState.add_power_up(offer["power"]["id"])
		label = str(offer["power"]["name"])
	elif offer.get("type", "upgrade") == "relic":
		RunState.add_relic(offer["relic"]["id"])
		label = str(offer["relic"]["name"])
	else:
		WeaponUpgrades.apply(offer, _weapon)
		label = str(offer["card"]["name"])
	var player := get_tree().get_first_node_in_group("player")
	if player:
		FX.floating_text(player.global_position + Vector2(0.0, -80.0), label, Palette.GOLD, 20, 44.0)
	_close()

func _close() -> void:
	get_tree().paused = false
	closed.emit()
	queue_free()
