extends Control
class_name TownTab

## Basis für die fünf Reiter im Stadtbildschirm.
## Unterklassen füllen build() - refresh() baut den Reiter komplett neu auf.

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_PASS
	refresh()

func refresh() -> void:
	for child in get_children():
		remove_child(child)
		child.queue_free()
	build()

func build() -> void:
	pass

## Standard-Gerüst: Überschrift oben, scrollbarer Inhalt darunter.
func make_page(title: String, subtitle: String = "") -> VBoxContainer:
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 22)
	margin.add_theme_constant_override("margin_right", 22)
	margin.add_theme_constant_override("margin_top", 12)
	margin.add_theme_constant_override("margin_bottom", 8)
	add_child(margin)

	var column := UIKit.make_column(12)
	margin.add_child(column)

	column.add_child(UIKit.make_label(title, 26, UIKit.TEXT))
	if not subtitle.is_empty():
		column.add_child(UIKit.make_label(subtitle, 16, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_LEFT, true))

	return column

func make_scroll(parent: VBoxContainer, separation: int = 10) -> VBoxContainer:
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	parent.add_child(scroll)

	var content := UIKit.make_column(separation)
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(content)
	return content

func is_click(event: InputEvent) -> bool:
	if event is InputEventMouseButton:
		return event.pressed and event.button_index == MOUSE_BUTTON_LEFT
	if event is InputEventScreenTouch:
		return event.pressed
	return false
