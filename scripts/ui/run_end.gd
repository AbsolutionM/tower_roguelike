extends Control

## Abschluss eines Runs: was gerettet wurde und was der Tod gekostet hat.

const TOWN_SCENE := "res://scenes/ui/town.tscn"
const GAME_SCENE := "res://scenes/test/test_weapons.tscn"

func _ready() -> void:
	UIKit.apply_pixel_theme(self)
	_build()

func _build() -> void:
	var summary: Dictionary = RunState.last_run_summary
	var died: bool = bool(summary.get("died", false))
	var lost: Array = summary.get("lost", [])
	var kept: Array = summary.get("kept", [])

	var column := UIKit.make_screen_root(self, 28)

	var accent: Color = UIKit.BAD if died else UIKit.GOOD
	var title_text: String = "Gefallen" if died else "Turm verlassen"
	column.add_child(UIKit.make_label(title_text, 42, accent, HORIZONTAL_ALIGNMENT_CENTER))

	column.add_child(UIKit.make_label(_subtitle(died, lost.size()), 18, UIKit.TEXT_DIM,
		HORIZONTAL_ALIGNMENT_CENTER, true))

	var currency := UIKit.make_currency_row(RunState.gold, RunState.get_total_essence())
	currency.alignment = BoxContainer.ALIGNMENT_CENTER
	column.add_child(currency)

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	column.add_child(scroll)

	var content := UIKit.make_column(12)
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(content)

	# Zahlen des Durchgangs - ohne die stand hier ein halber leerer Bildschirm.
	var stats_panel := UIKit.make_panel(UIKit.PANEL, Color(accent, 0.3))
	stats_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var stats_column := UIKit.make_column(6)
	stats_panel.add_child(stats_column)
	stats_column.add_child(UIKit.make_label("Durchgang", 21, accent))
	stats_column.add_child(UIKit.make_stat_sheet(GameManager.get_run_stats(), 2))
	content.add_child(stats_panel)

	if died and not lost.is_empty():
		content.add_child(_make_slot_panel("Verloren", lost, UIKit.BAD))
	content.add_child(_make_slot_panel("Ins Lager gebracht", kept, UIKit.GOOD))

	var footer := UIKit.make_row(10)
	var retry := UIKit.make_button("Nochmal", 20, UIKit.ACCENT)
	retry.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	retry.pressed.connect(func() -> void: get_tree().change_scene_to_file(GAME_SCENE))
	footer.add_child(retry)

	var town := UIKit.make_button("Zur Stadt", 20, UIKit.TEXT_DIM)
	town.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	town.pressed.connect(func() -> void: get_tree().change_scene_to_file(TOWN_SCENE))
	footer.add_child(town)
	column.add_child(footer)

## Ein verlorener Slot ist Einzahl - "1 Beutel-Slots" las sich falsch.
func _subtitle(died: bool, lost_count: int) -> String:
	if not died:
		return "Die gesamte Beute ist im Lager."
	if lost_count <= 0:
		return "Nichts verloren - der Beutel war leer."
	if lost_count == 1:
		return "1 Beutel-Slot verloren."
	return "%d Beutel-Slots verloren." % lost_count

func _make_slot_panel(title: String, slots: Array, accent: Color) -> Control:
	var panel := UIKit.make_panel(UIKit.PANEL, Color(accent, 0.4))
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var column := UIKit.make_column(6)
	panel.add_child(column)
	column.add_child(UIKit.make_label(title, 21, accent))

	if slots.is_empty():
		column.add_child(UIKit.make_label("Nichts.", 16, UIKit.TEXT_DIM))
		return panel

	for slot in slots:
		var item := Database.get_item(str(slot.get("item_id", "")))
		var count: int = int(slot.get("count", 0))
		if not item:
			continue
		var row := UIKit.make_row(8)
		row.add_child(UIKit.make_item_icon(item, 28.0))
		var name_label := UIKit.make_label(item.item_name, 17, item.get_rarity_color())
		name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(name_label)
		row.add_child(UIKit.make_label("x%d" % count, 17, UIKit.TEXT, HORIZONTAL_ALIGNMENT_RIGHT))
		column.add_child(row)

	return panel
