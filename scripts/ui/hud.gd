extends Control
class_name HUD

## Verbindet die UI mit Player, RunState und RoomController.
## Sucht seine Kinder über feste Pfade - Namen im Szenenbaum bitte so lassen.

@onready var health_bar: StatBar = get_node_or_null("TopBar/HealthBar")
@onready var timer_bar: StatBar = get_node_or_null("TopBar/TimerBar")
@onready var timer_label: Label = get_node_or_null("TopBar/TimerLabel")
@onready var gold_label: Label = get_node_or_null("TopBar/GoldLabel")
@onready var essence_label: Label = get_node_or_null("TopBar/EssenceLabel")
@onready var room_label: Label = get_node_or_null("TopBar/RoomLabel")
@onready var dash_button: ActionButton = get_node_or_null("DashButton")
@onready var ability_button: ActionButton = get_node_or_null("AbilityButton")
@onready var fade_overlay: ColorRect = get_node_or_null("FadeOverlay")
@onready var flash_overlay: ColorRect = get_node_or_null("FlashOverlay")
@onready var bag_label: Label = get_node_or_null("TopBar/BagLabel")
@onready var boss_label: Label = get_node_or_null("TopBar/BossLabel")
@onready var boss_bar: StatBar = get_node_or_null("TopBar/BossBar")
@onready var floor_label: Label = get_node_or_null("TopBar/FloorLabel")
@onready var special_bar: StatBar = get_node_or_null("TopBar/SpecialBar")

var _boss: Node = null
var _pause_overlay: Control = null

func _ready() -> void:
	UIKit.apply_pixel_theme(self)
	# Muss auch im Pausenzustand laufen, sonst kommt man aus der Pause nicht raus.
	process_mode = Node.PROCESS_MODE_ALWAYS
	mouse_filter = Control.MOUSE_FILTER_IGNORE

	RunState.gold_changed.connect(_on_gold_changed)
	RunState.essence_changed.connect(_on_essence_changed)
	FX.screen_flash_requested.connect(_on_screen_flash)

	RunState.run_inventory_changed.connect(_update_bag_label)
	RunState.bag_full.connect(_on_bag_full)

	_on_gold_changed(RunState.gold)
	_update_essence_label()
	_update_bag_label()

	if fade_overlay:
		fade_overlay.color.a = 0.0
	if flash_overlay:
		flash_overlay.color.a = 0.0

	# Wetter-Effekte liegen hinter dem restlichen HUD.
	var weather_overlay := WeatherOverlay.new()
	add_child(weather_overlay)
	move_child(weather_overlay, 0)

	await get_tree().process_frame
	_bind_player()
	_bind_room_controller()

func _bind_player() -> void:
	var player := get_tree().get_first_node_in_group("player")
	if not player:
		return

	var health = player.get_node_or_null("PlayerHealth")
	if health:
		health.health_changed.connect(_on_health_changed)
		_on_health_changed(health.current_health, health.max_health)

	# Ladebalken des Waffen-Sonderschlags.
	var controller = player.get_node_or_null("WeaponController")
	if controller and controller.has_signal("special_charge_changed"):
		controller.special_charge_changed.connect(_on_special_charge)
		_on_special_charge(controller.get_special_charge())

	if player.has_signal("dash_cooldown_changed"):
		player.dash_cooldown_changed.connect(_on_dash_cooldown)

	var ability = player.get_node_or_null("PlayerAbility")
	if ability:
		ability.cooldown_changed.connect(_on_ability_cooldown)
		if ability_button and ability.ability:
			# Der Knopf trägt die Farbe der Fähigkeit - Knopf und Effekt
			# im Raum gehören damit sichtbar zusammen.
			ability_button.button_color = ability.ability.color
			if ability.ability.icon:
				ability_button.icon = ability.ability.icon
			elif not ability.ability.ability_name.is_empty():
				ability_button.label_text = ability.ability.ability_name.substr(0, 1).to_upper()

func _bind_room_controller() -> void:
	var room_controller := get_tree().get_first_node_in_group("room_controller")
	if not room_controller:
		return
	room_controller.room_started.connect(_on_room_started)
	room_controller.room_finished.connect(_on_room_finished)
	_on_room_started(room_controller.get_current_room())

## ESC (bzw. Zurück-Taste auf Android) öffnet die Pause statt sofort abzubrechen.
func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		_toggle_pause()

func _toggle_pause() -> void:
	if is_instance_valid(_pause_overlay):
		_close_pause()
	else:
		_open_pause()

func _open_pause() -> void:
	_pause_overlay = Control.new()
	_pause_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_pause_overlay.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(_pause_overlay)

	var dim := ColorRect.new()
	dim.color = Color(Palette.INK, 0.86)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_pause_overlay.add_child(dim)

	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 60)
	margin.add_theme_constant_override("margin_right", 60)
	_pause_overlay.add_child(margin)

	var column := UIKit.make_column(14)
	column.alignment = BoxContainer.ALIGNMENT_CENTER
	margin.add_child(column)

	column.add_child(UIKit.make_label("Pause", 44, UIKit.TEXT, HORIZONTAL_ALIGNMENT_CENTER))
	column.add_child(UIKit.make_label(GameManager.get_progress_text(), 18, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_CENTER))
	column.add_child(UIKit.make_label(
		"Beutel %d/%d - beim Tod gehen %d Slots verloren." % [RunState.get_used_slots(), RunState.MAX_RUN_SLOTS, RunState.SLOTS_LOST_ON_DEATH],
		16, UIKit.TEXT_DIM, HORIZONTAL_ALIGNMENT_CENTER, true
	))
	column.add_child(UIKit.make_spacer(20.0))

	var resume := UIKit.make_primary_button("Fortsetzen", 24, UIKit.ACCENT)
	resume.pressed.connect(_close_pause)
	column.add_child(resume)

	var leave := UIKit.make_button("Turm verlassen", 20, UIKit.TEXT_DIM)
	leave.pressed.connect(_leave_run)
	column.add_child(leave)

	get_tree().paused = true

func _close_pause() -> void:
	get_tree().paused = false
	if is_instance_valid(_pause_overlay):
		_pause_overlay.queue_free()
	_pause_overlay = null

## Freiwillig aussteigen - die Beute bleibt erhalten.
func _leave_run() -> void:
	get_tree().paused = false
	_pause_overlay = null
	RunState.end_run(false)
	get_tree().change_scene_to_file("res://scenes/ui/run_end.tscn")

func _process(_delta: float) -> void:
	_update_boss()

	if floor_label:
		floor_label.text = GameManager.get_progress_text()

	_update_timer()

## Ein Balken allein sagt nicht, ob noch zwanzig Sekunden oder drei bleiben.
func _update_timer() -> void:
	var remaining: float = GameManager.get_time_remaining()
	var urgent: bool = remaining < 5.0
	var tint: Color = Palette.BLOOD if urgent else Palette.AZURE

	if timer_bar:
		timer_bar.set_value(remaining, maxf(GameManager.current_duration, 0.001))
		timer_bar.fill_color = tint

	if not timer_label:
		return
	# Räume ohne Uhr (Bossraum) stehen auf 99999 Sekunden - da gehört ein
	# Strich hin, keine fünfstellige Zahl.
	if GameManager.current_duration > 999.0:
		timer_label.text = "--"
	else:
		timer_label.text = "%d" % int(ceil(remaining))
	timer_label.add_theme_color_override("font_color", tint)

func _update_bag_label() -> void:
	if bag_label:
		bag_label.text = "Beutel %d/%d" % [RunState.get_used_slots(), RunState.MAX_RUN_SLOTS]

func _on_bag_full() -> void:
	if not bag_label:
		return
	bag_label.add_theme_color_override("font_color", Palette.BLOOD)
	_pop(bag_label)
	await get_tree().create_timer(0.9).timeout
	if is_instance_valid(bag_label):
		bag_label.add_theme_color_override("font_color", Palette.BONE)

func _update_boss() -> void:
	if not boss_bar or not boss_label:
		return

	if not is_instance_valid(_boss):
		_boss = get_tree().get_first_node_in_group("bosses")

	if not is_instance_valid(_boss):
		boss_bar.visible = false
		boss_label.visible = false
		return

	boss_bar.visible = true
	boss_label.visible = true

	var title := ""
	if _boss.enemy_data:
		title = _boss.enemy_data.boss_title
		if title.is_empty():
			title = _boss.enemy_data.enemy_name
	boss_label.text = title
	boss_bar.set_value(_boss.current_health, _boss.max_health)

func _on_health_changed(current: float, maximum: float) -> void:
	if health_bar:
		health_bar.set_value(current, maximum)

## Der Sonderschlag laedt sich mit Treffern auf und loest von selbst aus.
func _on_special_charge(ratio: float) -> void:
	if not special_bar:
		return
	special_bar.visible = ratio > 0.0
	special_bar.set_value(ratio, 1.0)

func _on_dash_cooldown(remaining: float, total: float) -> void:
	if dash_button:
		dash_button.set_cooldown(remaining, total)

func _on_ability_cooldown(remaining: float, total: float) -> void:
	if ability_button:
		ability_button.set_cooldown(remaining, total)

func _on_gold_changed(amount: int) -> void:
	if not gold_label:
		return
	gold_label.text = "%d" % amount
	_pop(gold_label)

func _on_essence_changed(_essence_id: String, _amount: int) -> void:
	_update_essence_label()
	if essence_label:
		_pop(essence_label)

func _update_essence_label() -> void:
	if essence_label:
		essence_label.text = "%d" % RunState.get_total_essence()

func _pop(node: Control) -> void:
	node.pivot_offset = node.size * 0.5
	node.scale = Vector2(1.25, 1.25)
	var tween := node.create_tween()
	tween.tween_property(node, "scale", Vector2.ONE, 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)

func _on_room_started(room: RoomData) -> void:
	if fade_overlay:
		var tween := fade_overlay.create_tween()
		tween.tween_property(fade_overlay, "color:a", 0.0, 0.35)

	if room_label and room:
		room_label.text = room.room_name
		if Weather.current:
			room_label.text += "  ·  " + Weather.current.weather_name
		room_label.pivot_offset = room_label.size * 0.5
		room_label.modulate.a = 1.0
		room_label.scale = Vector2(0.7, 0.7)
		var tween := room_label.create_tween()
		tween.tween_property(room_label, "scale", Vector2.ONE, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		tween.tween_property(room_label, "modulate:a", 0.45, 0.4).set_delay(1.0)

func _on_room_finished() -> void:
	if fade_overlay:
		var tween := fade_overlay.create_tween()
		tween.tween_property(fade_overlay, "color:a", 0.6, 0.22)

func _on_screen_flash(color: Color, duration: float) -> void:
	if not flash_overlay:
		return
	flash_overlay.color = color
	var tween := flash_overlay.create_tween()
	tween.tween_property(flash_overlay, "color:a", 0.0, duration).set_ease(Tween.EASE_OUT)
