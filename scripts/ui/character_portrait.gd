extends Control
class_name CharacterPortrait

## Großes, lebendiges Charakterbild für den Helden-Reiter.
##
## Die Charakter-Sprites haben keine Hände - die kommen aus
## `CharacterData.hand_texture` und werden hier separat angesetzt und animiert.
## Der Körper atmet, die Hände schwingen leicht versetzt dazu, und die
## rechte Hand hält die ausgerüstete Waffe.

const IDLE_ANIMATION := "Idle_Front"

var character: CharacterData
var weapon: WeaponData

## Anteil der Panelhöhe, den die Figur einnehmen soll.
@export var fill_ratio: float = 0.74
@export var breathe_speed: float = 2.2
@export var sway_speed: float = 1.5

var _root: Node2D
var _body: Node2D
var _left_hand: Sprite2D
var _right_hand: Sprite2D
var _weapon_sprite: Sprite2D

var _time: float = 0.0
var _body_size: Vector2 = Vector2(32.0, 32.0)
var _body_base_y: float = 0.0
var _hand_anchor: Vector2 = Vector2(24.0, 6.0)

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	clip_contents = true
	_build()
	resized.connect(_layout)
	_layout()

func _build() -> void:
	if not character:
		return

	_root = Node2D.new()
	add_child(_root)

	_body = _make_body()
	if _body:
		_root.add_child(_body)

	# Hände liegen vor dem Körper, die Waffe hängt an der rechten Hand.
	_left_hand = _make_hand(true)
	_right_hand = _make_hand(false)
	if _left_hand:
		_root.add_child(_left_hand)
	# Reihenfolge: Waffe zuerst, dann die Haende darueber.
	_weapon_sprite = _make_weapon()
	if _weapon_sprite:
		_root.add_child(_weapon_sprite)
	if _right_hand:
		_root.add_child(_right_hand)

## Bevorzugt die Leerlauf-Animation, sonst ein Standbild.
func _make_body() -> Node2D:
	var frames: SpriteFrames = character.sprite_frames
	if frames and frames.has_animation(IDLE_ANIMATION) and frames.get_frame_count(IDLE_ANIMATION) > 0:
		var animated := AnimatedSprite2D.new()
		animated.sprite_frames = frames
		animated.animation = IDLE_ANIMATION
		animated.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		animated.modulate = character.sprite_modulate
		animated.play()
		animated.offset = _measure(frames.get_frame_texture(IDLE_ANIMATION, 0))
		return animated

	var texture: Texture2D = character.portrait
	if not texture:
		return null
	var sprite := Sprite2D.new()
	sprite.texture = texture
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	sprite.modulate = character.sprite_modulate
	sprite.offset = _measure(texture)
	return sprite

## Die Sprites haben viel leeren Rand. Gemessen wird die tatsächlich bemalte
## Fläche - sonst wird die Figur winzig und die Hände sitzen im Nichts.
## Rückgabe: Versatz, der die bemalte Fläche auf den Knotenursprung zentriert.
func _measure(texture: Texture2D) -> Vector2:
	if not texture:
		return Vector2.ZERO
	_body_size = PixelDraw.used_size(texture)
	return PixelDraw.center_offset(texture)

## Ohne Handtextur bleibt die Figur handlos, statt einen Platzhalter zu zeigen.
func _make_hand(mirrored: bool) -> Sprite2D:
	if not character.hand_texture:
		return null
	var hand := Sprite2D.new()
	hand.texture = character.hand_texture
	hand.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	hand.modulate = character.sprite_modulate
	hand.flip_h = mirrored
	# Nicht jede Handtextur ist mittig gezeichnet.
	hand.offset = PixelDraw.center_offset(character.hand_texture)
	return hand

## Nur das Haltesprite - Inventar-Icons sind teils undurchsichtige JPGs und
## würden als weißer Klotz in der Hand landen.
func _make_weapon() -> Sprite2D:
	if not weapon or not weapon.hold_texture:
		return null

	var sprite := Sprite2D.new()
	sprite.texture = weapon.hold_texture
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

	# Auf Körpergröße normieren, damit kein Sprite die Figur erschlägt.
	var texture_size: Vector2 = weapon.hold_texture.get_size()
	var factor: float = _body_size.y * 0.7 / maxf(texture_size.length(), 1.0)
	sprite.scale = Vector2.ONE * factor

	# Der Griff sitzt in der Hand, die Klinge zeigt nach schräg oben hinaus.
	sprite.offset = Vector2(texture_size.x * 0.35, -texture_size.y * 0.25)
	return sprite

## Skaliert die Figur auf die aktuelle Panelgröße und setzt die Handpunkte.
func _layout() -> void:
	if not _root:
		return

	var view := size
	var target_height: float = maxf(view.y * fill_ratio, 1.0)
	var scale_factor: float = maxf(floorf(target_height / maxf(_body_size.y, 1.0)), 1.0)
	_root.scale = Vector2.ONE * scale_factor
	_root.position = Vector2(view.x * 0.5, view.y * 0.52)

	_body_base_y = 0.0
	# Hände sitzen auf Schulterhöhe, knapp außerhalb der Silhouette.
	_hand_anchor = Vector2(_body_size.x * 0.52, _body_size.y * 0.12)
	queue_redraw()

func _process(delta: float) -> void:
	_time += delta
	if not _root:
		return

	var breathe: float = sin(_time * breathe_speed)

	if _body:
		_body.position.y = _body_base_y + breathe * 0.9
		# Minimales Stauchen - die Figur wirkt dadurch, als würde sie atmen.
		_body.scale = Vector2(1.0, 1.0 + breathe * 0.02)

	if _left_hand:
		_left_hand.position = Vector2(-_hand_anchor.x, _hand_anchor.y + sin(_time * breathe_speed + 0.9) * 1.3)
		_left_hand.rotation = sin(_time * sway_speed + 1.7) * 0.10

	if _right_hand:
		_right_hand.position = Vector2(_hand_anchor.x, _hand_anchor.y + sin(_time * breathe_speed + 0.4) * 1.3)
		_right_hand.rotation = sin(_time * sway_speed) * 0.14
		if _weapon_sprite:
			_weapon_sprite.position = _right_hand.position
			_weapon_sprite.rotation = _right_hand.rotation - PI * 0.22

	queue_redraw()

func _draw() -> void:
	if not _root or not _body:
		return

	# Bodenschatten im Pixelraster, atmet mit der Figur mit.
	var pixel: float = UIKit.PIXEL
	var breathe: float = sin(_time * breathe_speed)
	var foot := Vector2(size.x * 0.5, _root.position.y + _body_size.y * 0.5 * _root.scale.y)
	var radius_x: float = _body_size.x * 0.34 * _root.scale.x * (1.0 + breathe * 0.03)
	PixelDraw.ellipse(self, foot, radius_x, radius_x * 0.32, pixel, Color(Palette.INK, 0.45))
