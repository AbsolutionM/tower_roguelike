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
var _weapon_sprite: Node2D

var _time: float = 0.0
var _body_size: Vector2 = Vector2(32.0, 32.0)
var _body_base_y: float = 0.0
var _hand_anchor: Vector2 = Vector2(24.0, 6.0)
## Ausgleich für nicht mittig gezeichnete Handtexturen.
var _hand_center: Vector2 = Vector2.ZERO

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
	# Zentrierung kommt über die Position - `offset` würde von `flip_h`
	# mitgespiegelt und die linke Hand doppelt so weit wegschieben.
	_hand_center = PixelDraw.center_offset(character.hand_texture)
	return hand

## Nur das Haltesprite - Inventar-Icons sind teils undurchsichtige JPGs und
## würden als weißer Klotz in der Hand landen.
##
## Versatz und Ruhedrehung kommen aus denselben Regeln wie im Kampf
## (WeaponController._hold_offset und _rest_rotation), damit eine Waffe im
## Heldenbild so in der Faust liegt wie nachher im Turm.
func _make_weapon() -> Node2D:
	if not weapon:
		return null
	if not weapon.hold_texture:
		# Ohne Haltesprite dieselbe gezeichnete Form wie im Kampf.
		var symbol := WeaponSymbol.new()
		symbol.category = weapon.category
		symbol.tint = Palette.BONE if weapon.is_melee else weapon.projectile_color
		symbol.scale = Vector2.ONE * (_body_size.y * 0.55 / 22.0)
		return symbol

	var sprite := Sprite2D.new()
	sprite.texture = weapon.hold_texture
	sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

	# Auf Körpergröße normieren, damit kein Sprite die Figur erschlägt.
	var texture_size: Vector2 = weapon.hold_texture.get_size()
	var factor: float = _body_size.y * 0.7 / maxf(texture_size.length(), 1.0)
	sprite.scale = Vector2.ONE * factor

	# Klingen sind diagonal gezeichnet: der Versatz entlang dieser Diagonalen
	# setzt den Griff in die Faust. Schusswaffen liegen mittig darin.
	if weapon.holds_upright():
		sprite.offset = Vector2(texture_size.x, -texture_size.y) * 0.34
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
	# Wie im Spiel: die Hand überlappt die Silhouette, statt daneben zu schweben.
	_hand_anchor = Vector2(_body_size.x * 0.31, _body_size.y * 0.12)
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

	# Die Handpunkte sind, wo die Hand *gemalt* ist. Die Knotenposition liegt
	# um `_hand_center` daneben, weil die Handtextur viel leeren Rand hat -
	# die Waffe muss dem gemalten Punkt folgen, nicht dem Knoten, sonst hängt
	# sie neben dem Kopf statt in der Faust.
	var left_point := Vector2(-_hand_anchor.x, _hand_anchor.y + sin(_time * breathe_speed + 0.9) * 0.7)
	var right_point := Vector2(_hand_anchor.x, _hand_anchor.y + sin(_time * breathe_speed + 0.4) * 0.7)
	var right_tilt: float = sin(_time * sway_speed) * 0.14

	if _left_hand:
		_left_hand.position = left_point + Vector2(-_hand_center.x, _hand_center.y)
		_left_hand.rotation = sin(_time * sway_speed + 1.7) * 0.10

	if _right_hand:
		_right_hand.position = right_point + _hand_center
		_right_hand.rotation = right_tilt

	if _weapon_sprite:
		_weapon_sprite.position = right_point
		if _weapon_sprite is Sprite2D:
			_weapon_sprite.rotation = right_tilt + deg_to_rad(weapon.hold_rotation_degrees)
		else:
			# Der Platzhalter zeigt nach +X: Klingen schräg nach oben, Läufe nach vorn.
			_weapon_sprite.rotation = right_tilt + (-PI * 0.25 if weapon.holds_upright() else 0.0)

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
