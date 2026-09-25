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
## Wie weit die Arme beim Laufen um den Körper pendeln, in Grad je Seite.
## Der Handkreis zeigt in Laufrichtung - ein Pumpen entlang des Arms wäre
## unsichtbar, das Pendel quer dazu ist es nicht.
@export var gait_swing_degrees: float = 28.0
## Die Geh-Animation läuft gezeichnet mit 10 Bildern pro Sekunde. Bei vollem
## Lauftempo so viel schneller, damit ein Schritt etwa eine halbe
## Körperlänge trägt statt einer ganzen - die Füße rutschen sonst.
@export var walk_animation_scale: float = 1.3
@export var light_energy: float = 1.4
@export var light_scale: float = 2.3

@export_group("Daten")
@export var character_data: CharacterData
@export var test_loadout: TestLoadout

@onready var animated_sprite: AnimatedSprite2D = $RigView/Rig/FirstBody
@onready var weapon_controller: WeaponController = $WeaponController
## Beide Hände - die Sprites haben keine, sie kommen aus den Charakterdaten.
@onready var weapon_hand: Sprite2D = get_node_or_null("RigView/Rig/WeaponPivot/FirstHand")
@onready var off_hand: Sprite2D = get_node_or_null("RigView/Rig/SecondHand")
## Zweite Zeichnung der Waffenhand in der Welt, über der Klinge: die Faust
## liegt vor dem Griff, nicht der Griff vor der Faust.
@onready var hand_overlay: Sprite2D = get_node_or_null("Sword/HandOverlay")

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
		# Im Turm startet jede Waffe auf Stufe I ihrer Linie und wächst im Lauf.
		var weapon := RunState.begin_weapon_run(RunState.get_equipped_weapon())
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
		# Nicht jede Handtextur ist mittig gezeichnet. Der Ausgleich läuft über
		# die Position, nicht über `offset` - den würde `flip_h` mitspiegeln.
		hand.offset = Vector2.ZERO
		if hand.texture:
			hand.center = PixelDraw.center_offset(hand.texture)
	if hand_overlay:
		hand_overlay.texture = character_data.hand_texture
		hand_overlay.modulate = character_data.sprite_modulate
		hand_overlay.visible = hand_overlay.texture != null

	# Beide Hände sitzen auf einem Kreis um den Körpermittelpunkt. Der Kreis
	# selbst ist der WeaponPivot - der wandert dorthin, wo die Figur wirklich
	# gezeichnet ist, nicht auf den Knotenursprung in der Texturmitte.
	var reach := _body_reach()
	if reach <= 0.0:
		return

	var pivot := get_node_or_null("RigView/Rig/WeaponPivot")
	if pivot:
		pivot.position.y = _hand_height()
		pivot.rest_position = pivot.position
		pivot.body_radius = reach

## Höhe der Fäuste in Spieler-Koordinaten: von der Unterkante der gemalten
## Figur aus nach oben gemessen (CharacterData.hand_height_from_feet).
##
## Der Knotenursprung liegt in der Texturmitte, die bemalte Figur reicht aber
## weiter nach unten - deshalb wird von der gemalten Unterkante gerechnet,
## nicht vom Ursprung.
func _hand_height() -> float:
	var frame := _idle_frame()
	if not frame:
		return 0.0
	var painted_bottom: float = -PixelDraw.center_offset(frame).y + PixelDraw.used_size(frame).y * 0.5
	return (painted_bottom - float(character_data.hand_height_from_feet)) * animated_sprite.scale.y

## Das Bild, an dem gemessen wird.
func _idle_frame() -> Texture2D:
	var frames: SpriteFrames = animated_sprite.sprite_frames
	if not frames:
		return null
	var animation: StringName = &"Idle_Front"
	if not frames.has_animation(animation):
		var names := frames.get_animation_names()
		if names.is_empty():
			return null
		animation = names[0]
	if frames.get_frame_count(animation) <= 0:
		return null
	return frames.get_frame_texture(animation, 0)

## Wie weit die Hände vom Körpermittelpunkt kreisen, als Anteil der halben
## bemalten Körperbreite. Unter 1.0 heißt: die Hand überlappt die Silhouette
## und liest sich als angesetzt statt als schwebend.
const HAND_INSET := 0.62

## Kreisradius der Hände in Spieler-Koordinaten, gemessen an der bemalten Breite.
func _body_reach() -> float:
	var frame := _idle_frame()
	if not frame:
		return 0.0
	return PixelDraw.used_size(frame).x * 0.5 * animated_sprite.scale.x * HAND_INSET

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
		if stats:
			health.setup(stats.heart_containers, stats.soul_hearts)
		else:
			health.setup(character_data.red_hearts, character_data.soul_hearts)
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
	_update_gait()

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
	Audio.play(Audio.ID_DASH)

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

	# Schritttempo folgt dem Lauftempo, damit die Füße nicht über den Boden
	# rutschen. Im Stand normal.
	animated_sprite.speed_scale = lerpf(1.0, walk_animation_scale, _speed_ratio()) if is_moving else 1.0

func _speed_ratio() -> float:
	return clampf(move_velocity.length() / maxf(get_move_speed(), 1.0), 0.0, 1.0)

## Schrittphase 0..1 aus dem laufenden Bild der Geh-Animation, -1 im Stand.
## Alles, was mit dem Schritt gehen soll, hängt an dieser einen Zahl - so
## bleiben Beine, Arme und Stauchen im Takt, statt drei Sinuswellen
## nebeneinander laufen zu lassen.
func _walk_phase() -> float:
	if not animated_sprite.is_playing() or not String(animated_sprite.animation).begins_with("Walking_"):
		return -1.0
	var count: int = animated_sprite.sprite_frames.get_frame_count(animated_sprite.animation)
	if count <= 0:
		return -1.0
	return float(animated_sprite.frame) / float(count)

## Arme pumpen gegenläufig in Laufrichtung. Die Auslenkung springt mit dem
## Animationsbild in ganzen Sprite-Pixeln - eine Hand, die zwischen zwei
## gezeichneten Bildern weich dahingleitet, wirkt schwammig.
func _update_gait() -> void:
	var pivot := get_node_or_null("RigView/Rig/WeaponPivot")
	if not pivot:
		return

	var texel: float = animated_sprite.scale.x
	var phase := _walk_phase()
	var swinging: bool = pivot.has_method("is_swinging") and pivot.is_swinging()

	if phase >= 0.0 and move_velocity.length() > 12.0:
		var wave: float = sin(phase * TAU)
		var angle: float = wave * deg_to_rad(gait_swing_degrees)
		# An den Umkehrpunkten heben sich beide Hände einen Sprite-Pixel, in
		# der Mitte hängen sie am tiefsten.
		var lift := Vector2(0.0, -roundf(absf(wave)) * texel)
		# Im Schlag führt die Waffenhand den Bogen, die freie Hand steht -
		# da hat kein Schritt dazwischenzufunken.
		if swinging:
			pivot.set_gait(Vector2.ZERO, Vector2.ZERO, 0.0)
		else:
			# Die freie Hand sitzt gegenüber und schwingt mit demselben Winkel
			# von selbst zur anderen Seite; am Griff beidhändig als eine.
			pivot.set_gait(lift, lift, angle)
		return

	# Im Stand: ein Atemzug von einem Sprite-Pixel, beide Hände gemeinsam.
	var breath: float = roundf(sin(_anim_time * 2.4) * 0.6) * texel
	pivot.set_gait(Vector2(0.0, breath), Vector2(0.0, breath), 0.0)

## Stauchen im Takt der Schritte - zwei Auftritte pro Animationsdurchlauf.
func _update_bob(delta: float) -> void:
	var phase := _walk_phase()
	var wave: float = sin(phase * TAU * 2.0) if phase >= 0.0 else sin(_anim_time * 15.0)
	var bob: float = wave * bob_strength * _speed_ratio()
	var target_scale := Vector2(_sprite_base_scale.x * (1.0 - bob), _sprite_base_scale.y * (1.0 + bob))
	animated_sprite.scale = animated_sprite.scale.lerp(target_scale, clampf(delta * 14.0, 0.0, 1.0))
