extends Area2D
class_name ItemPickup

## Loot-Drop mit Sprung-Animation, Magnet-Einzug und Einsammel-Effekt.
## Ohne Icon wird ein leuchtender Kreis in item.color gezeichnet.

@export var item: ItemData
@export var count: int = 1
@export var magnet_speed: float = 620.0
@export var pickup_distance: float = 18.0
@export var sprite: Sprite2D
@export var radius: float = 7.0

var player: Node2D
var collected: bool = false

var _stats: Node
var _time: float = 0.0
var _pop_velocity: Vector2 = Vector2.ZERO
var _height: float = 0.0
var _height_velocity: float = 0.0
var _settled: bool = true
var _magnet_speed_current: float = 0.0
var _use_sprite: bool = false

func _ready() -> void:
	add_to_group("pickups")
	z_index = 10
	z_as_relative = false

	player = get_tree().get_first_node_in_group("player")
	if player:
		_stats = player.get_node_or_null("PlayerStats")

	if not sprite:
		sprite = get_node_or_null("Sprite2D")

	_use_sprite = item != null and item.icon != null
	if sprite:
		if _use_sprite:
			sprite.texture = item.icon
			sprite.scale = Vector2.ONE * item.pickup_scale
		else:
			sprite.visible = false

	scale = Vector2.ZERO
	var tween := create_tween()
	tween.tween_property(self, "scale", Vector2.ONE, 0.22).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)

## Lässt das Item in einem kleinen Bogen aus der Quelle herausspringen.
func pop_out() -> void:
	var angle: float = randf() * TAU
	_pop_velocity = Vector2(cos(angle), sin(angle)) * randf_range(70.0, 160.0)
	_height_velocity = randf_range(150.0, 220.0)
	_height = 1.0
	_settled = false

func _process(delta: float) -> void:
	if collected:
		return

	_time += delta

	if not _settled:
		_update_pop(delta)
	else:
		_update_magnet(delta)

	if not _use_sprite:
		queue_redraw()
	elif sprite:
		sprite.position = Vector2(0.0, -_height + _bob())

func _bob() -> float:
	return sin(_time * 4.0) * 2.5

func _update_pop(delta: float) -> void:
	_pop_velocity = _pop_velocity.move_toward(Vector2.ZERO, 280.0 * delta)
	global_position += _pop_velocity * delta

	_height_velocity -= 900.0 * delta
	_height = maxf(_height + _height_velocity * delta, 0.0)

	if _height > 0.0 or _height_velocity > 0.0:
		return

	if absf(_height_velocity) > 70.0:
		_height_velocity = absf(_height_velocity) * 0.42
		FX.dust_puff(global_position, Color(Palette.MIST, 0.35), 2, 9.0)
	else:
		_height_velocity = 0.0
		_settled = true

func _update_magnet(delta: float) -> void:
	if not player or not is_instance_valid(player):
		return

	# Herzen, für die gerade kein Platz ist, bleiben liegen statt am Helden zu kleben.
	if not _has_room_for_hearts():
		_magnet_speed_current = 0.0
		return

	var to_player := player.global_position - global_position
	var distance := to_player.length()

	if distance <= pickup_distance:
		collect()
		return

	var attract_radius: float = _stats.pickup_radius if _stats else 95.0
	if distance > attract_radius:
		_magnet_speed_current = 0.0
		return

	_magnet_speed_current = move_toward(_magnet_speed_current, magnet_speed, magnet_speed * 3.0 * delta)
	global_position += to_player.normalized() * _magnet_speed_current * delta

func _draw() -> void:
	if _use_sprite or not item:
		return

	var center := Vector2(0.0, -_height + _bob())
	var tint: Color = item.color
	var scaled_radius: float = radius * item.pickup_scale
	var pixel: float = FX.pixel_size()

	# Schein darunter, damit Beute im dunklen Raum auffaellt.
	PixelDraw.disc(self, center, scaled_radius * 1.9, pixel, Color(tint, 0.18))
	ItemSymbol.paint(self, center, scaled_radius * 2.4, item.symbol, tint)

func collect() -> void:
	if collected or not item:
		return

	match item.item_type:
		ItemData.ItemType.CURRENCY:
			RunState.add_gold(item.value * count)
		ItemData.ItemType.ESSENCE:
			RunState.add_essence(item.essence_id, count)
		ItemData.ItemType.HEART:
			# Wie in Isaac: bei vollen roten Herzen bleibt das Herz liegen.
			if not _apply_hearts(false):
				return
		ItemData.ItemType.SOUL_HEART:
			if not _apply_hearts(true):
				return
		ItemData.ItemType.KEY:
			RunState.add_keys(item.value * count)
		_:
			if not _store_in_bag():
				return

	collected = true
	Audio.play(Audio.ID_COIN if item.item_type == ItemData.ItemType.CURRENCY else Audio.ID_PICKUP)
	_collect_effect()
	queue_free()

func _has_room_for_hearts() -> bool:
	if not item or not player:
		return true
	var health = player.get_node_or_null("PlayerHealth")
	if not health:
		return true
	match item.item_type:
		ItemData.ItemType.HEART:
			return not health.is_red_full()
		ItemData.ItemType.SOUL_HEART:
			return health.can_add_soul()
	return true

## False = kein Platz für dieses Herz, es bleibt liegen.
func _apply_hearts(soul: bool) -> bool:
	if not player:
		return false
	var health = player.get_node_or_null("PlayerHealth")
	if not health:
		return false
	var halves: int = item.value * count
	var gained: int = health.add_soul_hearts(halves) if soul else health.heal_hearts(halves)
	return gained > 0

## False = Beutel voll, das Item bleibt liegen.
func _store_in_bag() -> bool:
	if RunState.add_run_item(item, count):
		return true
	FX.floating_text(global_position + Vector2(0.0, -22.0), "Beutel voll", FX.COLOR_HURT, 16, 30.0)
	return false

func _collect_effect() -> void:
	# Herzen melden sich selbst über PlayerHealth.
	if item.item_type != ItemData.ItemType.HEART and item.item_type != ItemData.ItemType.SOUL_HEART:
		var amount: int = item.value * count if item.item_type in [ItemData.ItemType.CURRENCY, ItemData.ItemType.KEY] else count
		var label_text := "+%d" % amount
		if item.item_type == ItemData.ItemType.KEY:
			label_text += " Schlüssel"
		FX.floating_text(global_position + Vector2(0.0, -18.0), label_text, item.color, 17, 34.0)
	FX.ring_burst(global_position, item.color, 3.0, 26.0, 0.22, 3.0)
