extends TownTab

## Reiter rechts der Mitte: Waffen bauen und Lager verwalten/verkaufen.

func build() -> void:
	var column := make_page("Werkstatt", "Baue Waffen aus Material - oder mach überschüssiges Zeug zu Gold.")
	var content := make_scroll(column, 10)

	content.add_child(UIKit.make_label("Baupläne", 20, UIKit.TEXT_DIM))
	var recipes := _sorted_recipes()
	if recipes.is_empty():
		content.add_child(UIKit.make_label("Keine Baupläne bekannt.", 15, UIKit.TEXT_DIM))
	for recipe in recipes:
		content.add_child(_make_recipe_row(recipe))

	content.add_child(UIKit.make_label("Lager", 20, UIKit.TEXT_DIM))
	var entries := RunState.get_stash_entries()
	if entries.is_empty():
		content.add_child(UIKit.make_label(
			"Lager ist leer. Sammle Material im Turm und verlasse ihn lebend.",
			15, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_LEFT, true
		))
		return
	for entry in entries:
		content.add_child(_make_stash_row(entry["item"], int(entry["count"])))

# --- Bauen -----------------------------------------------------------------

## Was jetzt gebaut werden kann, steht oben; danach das Erreichbare nach Preis;
## Gebautes ganz unten. Ungeordnet sucht man in einer langen Liste zu lange.
func _sorted_recipes() -> Array[CraftingRecipe]:
	var usable: Array[CraftingRecipe] = []
	for recipe in Database.get_recipes():
		if recipe and recipe.result_weapon:
			usable.append(recipe)

	usable.sort_custom(func(a: CraftingRecipe, b: CraftingRecipe) -> bool:
		var rank_a := _recipe_rank(a)
		var rank_b := _recipe_rank(b)
		if rank_a != rank_b:
			return rank_a < rank_b
		if a.gold_cost != b.gold_cost:
			return a.gold_cost < b.gold_cost
		return a.result_weapon.weapon_name < b.result_weapon.weapon_name
	)
	return usable

func _recipe_rank(recipe: CraftingRecipe) -> int:
	if RunState.is_weapon_owned(recipe.result_weapon.weapon_id):
		return 2
	return 0 if recipe.can_craft() else 1

func _make_recipe_row(recipe: CraftingRecipe) -> Control:
	var weapon := recipe.result_weapon
	var owned := RunState.is_weapon_owned(weapon.weapon_id)
	var can_craft := recipe.can_craft()

	var panel := UICard.new(UIKit.ACCENT if can_craft else Palette.MIST)
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var row := UIKit.make_row(12)
	panel.content.add_child(row)

	var info := UIKit.make_column(2)
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(info)
	info.add_child(UIKit.make_label(weapon.weapon_name, 19, UIKit.TEXT))
	info.add_child(UIKit.make_label(
		weapon.describe_line(),
		14, UIKit.TEXT_DIM
	))

	for entry in recipe.get_required():
		var item := Database.get_item(str(entry["item_id"]))
		var needed: int = int(entry["count"])
		var have: int = RunState.get_stash_count(str(entry["item_id"]))
		var item_name: String = item.item_name if item else str(entry["item_id"])

		# Material mit kleinem Icon - reine Textlisten liest niemand.
		var material_row := UIKit.make_row(6)
		material_row.add_child(UIKit.make_item_icon(item, 22.0))
		# Fehlendes Material bleibt gedämpft - Rot wäre hier ein Fehler,
		# nicht "noch nicht gesammelt".
		material_row.add_child(UIKit.make_label(
			"%s  %d/%d" % [item_name, have, needed],
			14,
			UIKit.GOOD if have >= needed else UIKit.TEXT_DIM
		))
		info.add_child(material_row)

	var actions := UIKit.make_column(4)
	actions.custom_minimum_size = Vector2(132.0, 0.0)
	row.add_child(actions)

	if owned:
		actions.add_child(UIKit.make_label("Gebaut", 16, UIKit.GOOD, HORIZONTAL_ALIGNMENT_CENTER))
		return panel

	actions.add_child(UIKit.make_label("%d Gold" % recipe.gold_cost, 15, UIKit.ACCENT, HORIZONTAL_ALIGNMENT_CENTER))
	var craft_button := UIKit.make_button("Bauen", 17, UIKit.ACCENT)
	craft_button.custom_minimum_size = Vector2(0.0, 44.0)
	craft_button.disabled = not can_craft
	craft_button.pressed.connect(func() -> void:
		if RunState.craft(recipe):
			refresh()
	)
	actions.add_child(craft_button)
	return panel

# --- Verkaufen -------------------------------------------------------------

func _make_stash_row(item: ItemData, count: int) -> Control:
	var rarity_color: Color = item.get_rarity_color()
	var panel := UICard.new(rarity_color)
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var row := UIKit.make_row(12)
	panel.content.add_child(row)
	row.add_child(UIKit.make_item_icon(item, 46.0))

	var info := UIKit.make_column(2)
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(info)
	info.add_child(UIKit.make_label("%s  x%d" % [item.item_name, count], 19, rarity_color))
	info.add_child(UIKit.make_label(
		"%s · %d Gold pro Stück" % [item.get_rarity_name(), maxi(item.value, 1)],
		14, UIKit.TEXT_DIM
	))

	var actions := UIKit.make_row(6)
	actions.custom_minimum_size = Vector2(180.0, 0.0)
	row.add_child(actions)

	var sell_one := UIKit.make_button("1x", 16, UIKit.TEXT_DIM)
	sell_one.custom_minimum_size = Vector2(60.0, 44.0)
	sell_one.pressed.connect(func() -> void:
		RunState.sell_stash_item(item, 1)
		refresh()
	)
	actions.add_child(sell_one)

	var sell_all := UIKit.make_button("Alle", 16, UIKit.ACCENT)
	sell_all.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sell_all.custom_minimum_size = Vector2(0.0, 44.0)
	sell_all.pressed.connect(func() -> void:
		RunState.sell_stash_item(item, count)
		refresh()
	)
	actions.add_child(sell_all)

	return panel
