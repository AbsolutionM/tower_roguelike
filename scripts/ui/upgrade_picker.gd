extends CanvasLayer
class_name UpgradePicker

## Kartenwahl für Waffen-Upgrades: 1 aus N. Pausiert das Spiel.
## Kommen mehrere Angebote kurz hintereinander (fünf Splitter plus Amboss),
## stellt der HUD sie in eine Schlange - es ist immer nur eine Wahl offen.

signal closed

var count: int = 3
var min_rare: bool = false
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
	_offers = WeaponUpgrades.roll(count, _weapon, luck, min_rare)
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
	dim.color = Color(Palette.INK, 0.9)
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
	column.add_child(UIKit.make_label(_weapon_line(), 17, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_CENTER, true))
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

func _pick(offer: Dictionary) -> void:
	WeaponUpgrades.apply(offer, _weapon)
	var player := get_tree().get_first_node_in_group("player")
	if player:
		FX.floating_text(player.global_position + Vector2(0.0, -80.0), str(offer["card"]["name"]), Palette.GOLD, 20, 44.0)
	_close()

func _close() -> void:
	get_tree().paused = false
	closed.emit()
	queue_free()
