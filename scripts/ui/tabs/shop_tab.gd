extends TownTab

## Ganz linker Reiter: Waffen und Accessoires gegen Gold.

func build() -> void:
	var column := make_page("Shop", "Gold gegen Ausrüstung. Material verkaufst du in der Werkstatt.")
	var content := make_scroll(column, 10)

	_build_weapon_sections(content)

	content.add_child(UIKit.make_section("Accessoires", UIKit.COOL))
	var accessories_listed := false
	for accessory in Database.get_accessories():
		if accessory and accessory.shop_price > 0:
			content.add_child(_make_accessory_row(accessory))
			accessories_listed = true
	if not accessories_listed:
		content.add_child(UIKit.make_label("Aktuell keine Accessoires im Angebot.", 15, UIKit.TEXT_DIM))

## Waffen nach Klasse gruppiert, innerhalb der Klasse vom Billigen zum Teuren.
## Bei ueber fuenfzig Waffen ist eine flache Liste nicht mehr lesbar.
func _build_weapon_sections(content: VBoxContainer) -> void:
	var by_category: Dictionary = {}
	for weapon in Database.get_weapons():
		if not weapon or weapon.shop_price <= 0:
			continue
		if not by_category.has(weapon.category):
			by_category[weapon.category] = []
		by_category[weapon.category].append(weapon)

	if by_category.is_empty():
		content.add_child(UIKit.make_section("Waffen", UIKit.ACCENT))
		content.add_child(UIKit.make_label("Aktuell keine Waffen im Angebot.", 15, UIKit.TEXT_DIM))
		return

	var categories: Array = by_category.keys()
	categories.sort()
	for category in categories:
		var weapons: Array = by_category[category]
		weapons.sort_custom(func(a, b): return a.shop_price < b.shop_price)
		content.add_child(UIKit.make_section(
			"%s  (%d)" % [WeaponData.CATEGORY_NAMES.get(category, "Waffen"), weapons.size()],
			UIKit.ACCENT
		))
		for weapon in weapons:
			content.add_child(_make_weapon_row(weapon))

func _make_row(title: String, subtitle: String, detail: String, accent: Color, price: int, owned: bool, on_buy: Callable, icon: Texture2D = null) -> Control:
	var affordable: bool = RunState.gold >= price
	var panel := UICard.new(accent if (affordable and not owned) else Palette.MIST)
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var row := UIKit.make_row(12)
	panel.content.add_child(row)
	row.add_child(UIKit.make_icon(icon, 52.0, accent))

	var info := UIKit.make_column(2)
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(info)
	info.add_child(UIKit.make_label(title, 19, accent))
	info.add_child(UIKit.make_label(subtitle, 14, UIKit.TEXT_DIM))
	if not detail.is_empty():
		info.add_child(UIKit.make_label(detail, 14, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_LEFT, true))

	var actions := UIKit.make_column(4)
	actions.custom_minimum_size = Vector2(132.0, 0.0)
	row.add_child(actions)

	if owned:
		actions.add_child(UIKit.make_label("Im Besitz", 16, UIKit.GOOD, HORIZONTAL_ALIGNMENT_CENTER))
		return panel

	actions.add_child(UIKit.make_label("%d Gold" % price, 15, UIKit.ACCENT, HORIZONTAL_ALIGNMENT_CENTER))
	var buy_button := UIKit.make_button("Kaufen", 17, UIKit.ACCENT)
	buy_button.custom_minimum_size = Vector2(0.0, 44.0)
	buy_button.disabled = not affordable
	buy_button.pressed.connect(func() -> void:
		if on_buy.call():
			refresh()
	)
	actions.add_child(buy_button)
	return panel

func _make_weapon_row(weapon: WeaponData) -> Control:
	return _make_row(
		weapon.weapon_name,
		"%s · %.0f Schaden · %.2fs" % [weapon.get_category_name(), weapon.damage, weapon.cooldown],
		weapon.description,
		UIKit.ACCENT,
		weapon.shop_price,
		RunState.is_weapon_owned(weapon.weapon_id),
		func() -> bool: return RunState.buy_weapon(weapon),
		weapon.icon
	)

func _make_accessory_row(accessory: AccessoryData) -> Control:
	return _make_row(
		accessory.accessory_name,
		accessory.describe(),
		accessory.description,
		accessory.get_rarity_color(),
		accessory.shop_price,
		RunState.is_accessory_owned(accessory.accessory_id),
		func() -> bool: return RunState.buy_accessory(accessory),
		accessory.icon
	)
