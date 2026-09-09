extends CharacterBody2D
class_name PlayerController

signal dash_cooldown_changed(remaining: float, total: float)

const LIGHT_TEXTURE := preload("res://resources/materials/light_gradient.tres")

@export_group("Bewegung")
@export var speed: float = 200.0
@export var acceleration: float = 2400.0
@export var friction: float = 2800.0

@export_group("Dash")
@export var dash_speed: float = 780.0
@export var dash_duration: float = 0.17
@export var dash_cooldown: float = 1.0
@export var dash_afterimage_interval: float = 0.025

@export_group("Feel")
@export var shadow_offset: Vector2 = Vector2(0.0, 24.0)
@export var shadow_radius: float = 14.0
@export var step_dust_interval: float = 0.3
@export var bob_strength: float = 0.035
@export var light_energy: float = 1.0
@export var light_scale: float = 1.9

@export_group("Daten")
@export var character_data: CharacterData
@export var test_loadout: TestLoadout

@onready var animated_sprite: AnimatedSprite2D = $FirstBody
@onready var weapon_controller: WeaponController = $WeaponController
## Beide Hände - die Sprites haben keine, sie kommen aus den Charakterdaten.
@onready var weapon_hand: Sprite2D = get_node_or_null("WeaponPivot/FirstHand")
@onready var off_hand: Sprite2D = get_node_or_null("SecondHand")

var stats: PlayerStats
var health: PlayerHealth
var ability: PlayerAbility

var move_velocity: Vector2 = Vector2.ZERO
var knockback_velocity: Vector2 = Vector2.ZERO
var facing: Vector2 = Vector2.DOWN
var input_locked: bool = false

var dash_timer: float = 0.0
var dash_cd_timer: float = 0.0
var dash_direction: Vector2 = Vector2.ZERO

var _afterimage_timer: float = 0.0
var _dust_timer: float = 0.0
var _anim_time: float = 0.0
var _sprite_base_scale: Vector2 = Vector2.ONE
var _shadow: BlobShadow
var _light: PointLight2D

func _ready() -> void:
	add_to_group("player")

	stats = get_node_or_null("PlayerStats")
	health = get_node_or_null("PlayerHealth")
	ability = get_node_or_null("PlayerAbility")

	_sprite_base_scale = animated_sprite.scale
	_create_shadow()
	_create_light()
	apply_loadout()

	PlayerInput.dash_pressed.connect(try_dash)
	if health:
		health.died.connect(_on_died)

func _create_shadow() -> void:
	_shadow = BlobShadow.new()
	_shadow.radius = shadow_radius
	_shadow.position = shadow_offset
	add_child(_shadow)

func _create_light() -> void:
	_light = PointLight2D.new()
	_light.texture = LIGHT_TEXTURE
	_light.blend_mode = Light2D.BLEND_MODE_ADD
	_light.energy = light_energy
	_light.texture_scale = light_scale
	_light.color = Palette.AMBER
	add_child(_light)

## Auswahl aus dem Charakter-Screen hat Vorrang, sonst das Test-Loadout der Szene.
func apply_loadout() -> void:
	var selected := RunState.get_selected_character()
	if selected:
		character_data = selected
		var weapon := RunState.get_equipped_weapon()
		if weapon and weapon_controller:
			weapon_controller.equipped_weapon = weapon
	elif test_loadout:
		if test_loadout.character:
			character_data = test_loadout.character
		if test_loadout.weapon and weapon_controller:
			weapon_controller.equipped_weapon = test_loadout.weapon
	apply_character_data()

## Beide Hände bekommen dieselbe Textur und dieselbe Färbung - die zweite Hand
## soll aussehen wie die erste, nur ohne Waffe.
func _apply_hands() -> void:
	for hand in [weapon_hand, off_hand]:
		if not hand:
			continue
		if character_data.hand_texture:
			hand.texture = character_data.hand_texture
		hand.modulate = character_data.sprite_modulate
		hand.visible = hand.texture != null
		# Nicht jede Handtextur ist mittig gezeichnet - ohne diesen Ausgleich
		# sitzt die Hand neben dem Arm statt daran.
		if hand.texture:
			hand.offset = PixelDraw.center_offset(hand.texture)

	# Beide Hände gehören an den Rand der Silhouette, nicht in den Torso.
	# Gemessen wird die bemalte Breite des Körpers, nicht die Texturgröße.
	var reach := _body_reach()
	if reach <= 0.0:
		return
	if off_hand:
		off_hand.distance = reach
	var pivot := get_node_or_null("WeaponPivot")
	if pivot:
		pivot.pivot_radius = reach
		# Beim Zielen nach oben bleibt die Hand hinter dem Körper.
		pivot.pivot_radius_up = -reach * 0.55

## Halbe bemalte Körperbreite in Spieler-Koordinaten, plus etwas Luft.
func _body_reach() -> float:
	var frames: SpriteFrames = animated_sprite.sprite_frames
	if not frames:
		return 0.0
	var animation: StringName = &"Idle_Front"
	if not frames.has_animation(animation):
		var names := frames.get_animation_names()
		if names.is_empty():
			return 0.0
		animation = names[0]
	if frames.get_frame_count(animation) <= 0:
		return 0.0
	var body := PixelDraw.used_size(frames.get_frame_texture(animation, 0))
	return body.x * 0.5 * animated_sprite.scale.x + 4.0

func apply_character_data() -> void:
	if not character_data:
		return

	if character_data.sprite_frames:
		animated_sprite.sprite_frames = character_data.sprite_frames
	animated_sprite.modulate = character_data.sprite_modulate
	_apply_hands()
	if _light:
		_light.color = character_data.accent_color.lerp(Color(1.0, 1.0, 1.0), 0.45)
	if character_data.dash_speed > 0.0:
		dash_speed = character_data.dash_speed
	if character_data.dash_duration > 0.0:
		dash_duration = character_data.dash_duration
	if character_data.dash_cooldown > 0.0:
		dash_cooldown = character_data.dash_cooldown

	if stats:
		stats.character_data = character_data
		stats.recalculate()
		speed = stats.move_speed
	else:
		speed = character_data.base_speed

	if health:
		health.setup(stats.max_health if stats else character_data.base_health)
	if ability:
		ability.ability = character_data.ability
	if weapon_controller and character_data.starting_weapon and not weapon_controller.equipped_weapon:
		weapon_controller.equipped_weapon = character_data.starting_weapon

func get_move_speed() -> float:
	return stats.move_speed if stats else speed

func get_dash_cooldown() -> float:
	return dash_cooldown * (stats.dash_cooldown_mult if stats else 1.0)

func _physics_process(delta: float) -> void:
	_anim_time += delta
	_tick_timers(delta)

	if dash_timer > 0.0:
		move_velocity = dash_direction * dash_speed
		_afterimage_timer -= delta
		if _afterimage_timer <= 0.0:
			_afterimage_timer = dash_afterimage_interval
			FX.afterimage(animated_sprite, 0.3, Color(Palette.TEAL, 0.5))
	else:
		var input_dir: Vector2 = Vector2.ZERO if input_locked else PlayerInput.get_move_vector()
		if input_dir.length() > 0.05:
			facing = input_dir.normalized()
			move_velocity = move_velocity.move_toward(input_dir * get_move_speed(), acceleration * delta)
			_tick_step_dust(delta)
		else:
			move_velocity = move_velocity.move_toward(Vector2.ZERO, friction * delta)

	velocity = move_velocity + knockback_velocity
	move_and_slide()
	knockback_velocity = knockback_velocity.move_toward(Vector2.ZERO, 2400.0 * delta)

	_update_animation()
	_update_bob(delta)

func _tick_timers(delta: float) -> void:
	if dash_timer > 0.0:
		dash_timer = maxf(dash_timer - delta, 0.0)
	if dash_cd_timer > 0.0:
		dash_cd_timer = maxf(dash_cd_timer - delta, 0.0)
		dash_cooldown_changed.emit(dash_cd_timer, get_dash_cooldown())

func _tick_step_dust(delta: float) -> void:
	_dust_timer -= delta
	if _dust_timer > 0.0:
		return
	_dust_timer = step_dust_interval
	FX.dust_puff(global_position + shadow_offset, Color(Palette.MIST, 0.4), 3, 14.0)

func try_dash() -> void:
	if input_locked or dash_timer > 0.0 or dash_cd_timer > 0.0:
		return

	var direction := PlayerInput.get_move_vector()
	if direction.length() < 0.05:
		direction = facing
	dash_direction = direction.normalized()
	facing = dash_direction

	dash_timer = dash_duration
	dash_cd_timer = get_dash_cooldown()
	_afterimage_timer = 0.0

	if health:
		health.set_invulnerable(dash_duration + 0.08)

	FX.ring_burst(global_position, Palette.TEAL, 10.0, 52.0, 0.3, 5.0)
	FX.dust_puff(global_position + shadow_offset, Color(Palette.BONE, 0.5), 5, 28.0)
	FX.shake(2.0)
	dash_cooldown_changed.emit(dash_cd_timer, get_dash_cooldown())

func apply_knockback(direction: Vector2, force: float) -> void:
	knockback_velocity = direction.normalized() * force

func _on_died() -> void:
	input_locked = true
	move_velocity = Vector2.ZERO
	knockback_velocity = Vector2.ZERO

func _update_animation() -> void:
	var frames := animated_sprite.sprite_frames
	if not frames:
		return

	var is_moving: bool = move_velocity.length() > 12.0
	var suffix := "Front"

	if absf(facing.x) < 0.1:
		suffix = "Back" if facing.y < 0.0 else "Front"
	else:
		suffix = "Side_Back" if facing.y < -0.35 else "Side_Front"
		animated_sprite.flip_h = facing.x < 0.0

	var target_anim: String = ("Walking_" if is_moving else "Idle_") + suffix
	if not frames.has_animation(target_anim):
		return
	if animated_sprite.animation != target_anim:
		animated_sprite.play(target_anim)
	elif not animated_sprite.is_playing():
		animated_sprite.play()

func _update_bob(delta: float) -> void:
	var speed_ratio: float = clampf(move_velocity.length() / maxf(get_move_speed(), 1.0), 0.0, 1.0)
	var bob: float = sin(_anim_time * 15.0) * bob_strength * speed_ratio
	var target_scale := Vector2(_sprite_base_scale.x * (1.0 - bob), _sprite_base_scale.y * (1.0 + bob))
	animated_sprite.scale = animated_sprite.scale.lerp(target_scale, clampf(delta * 14.0, 0.0, 1.0))
