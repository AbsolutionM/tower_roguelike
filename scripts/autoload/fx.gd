extends Node

## Zentrale Juice-Bibliothek: Damage Numbers, Funken, Ringe, Staub, Screenshake.
## Alles prozedural - funktioniert ohne einen einzigen Sprite.

signal screen_flash_requested(color: Color, duration: float)

const THEME_PATH := "res://resources/fx/fx_theme.tres"

## Texturen und Pixelgröße für alle Effekte. Slots leer = Pixelblöcke.
var theme: FXTheme

func _ready() -> void:
	theme = load(THEME_PATH) as FXTheme
	if not theme:
		theme = FXTheme.new()

func pixel_size() -> float:
	return maxf(theme.pixel_size, 1.0)

const COLOR_DAMAGE := Palette.BONE
const COLOR_CRIT := Palette.GOLD
const COLOR_HURT := Palette.BLOOD
const COLOR_HEAL := Palette.MOSS

func _host() -> Node:
	if not is_inside_tree():
		return null
	return get_tree().current_scene

func floating_text(world_pos: Vector2, text: String, tint: Color = COLOR_DAMAGE, font_size: int = 20, rise: float = 46.0) -> void:
	var host := _host()
	if not host:
		return

	var label := Label.new()
	label.text = text
	label.size = Vector2(140.0, 36.0)
	label.pivot_offset = Vector2(70.0, 18.0)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.z_index = 200
	label.z_as_relative = false
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", tint)
	label.add_theme_color_override("font_outline_color", Color(Palette.INK, 0.9))
	label.add_theme_constant_override("outline_size", max(4, int(font_size / 3)))
	host.add_child(label)

	label.global_position = world_pos - label.pivot_offset
	label.scale = Vector2(0.35, 0.35)

	var target: Vector2 = label.position + Vector2(randf_range(-18.0, 18.0), -rise)

	var pop := label.create_tween()
	pop.tween_property(label, "scale", Vector2(1.18, 1.18), 0.13).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	pop.tween_property(label, "scale", Vector2.ONE, 0.09)

	var move := label.create_tween()
	move.set_parallel(true)
	move.tween_property(label, "position", target, 0.75).set_trans(Tween.TRANS_QUINT).set_ease(Tween.EASE_OUT)
	move.tween_property(label, "modulate:a", 0.0, 0.3).set_delay(0.45)
	move.chain().tween_callback(label.queue_free)

func damage_number(world_pos: Vector2, amount: float, crit: bool = false, tint: Color = COLOR_DAMAGE) -> void:
	var text := str(int(round(amount)))
	if crit:
		floating_text(world_pos, text + "!", COLOR_CRIT, 26, 54.0)
	else:
		floating_text(world_pos, text, tint, 18, 40.0)

func hit_spark(world_pos: Vector2, tint: Color = COLOR_DAMAGE, count: int = 8, direction: Vector2 = Vector2.ZERO, spread: float = TAU, length: float = 34.0) -> void:
	var host := _host()
	if not host:
		return
	var fx := ShapeFX.new()
	fx.mode = ShapeFX.Mode.SPARKS
	fx.color = tint
	fx.count = count
	fx.direction = direction
	fx.spread = spread
	fx.end_radius = length
	fx.start_width = 4.0
	fx.duration = 0.26
	host.add_child(fx)
	fx.global_position = world_pos

func ring_burst(world_pos: Vector2, tint: Color = COLOR_DAMAGE, start_radius: float = 6.0, end_radius: float = 70.0, duration: float = 0.32, width: float = 7.0) -> void:
	var host := _host()
	if not host:
		return
	var fx := ShapeFX.new()
	fx.mode = ShapeFX.Mode.RING
	fx.color = tint
	fx.start_radius = start_radius
	fx.end_radius = end_radius
	fx.duration = duration
	fx.start_width = width
	fx.end_width = 1.0
	host.add_child(fx)
	fx.global_position = world_pos

func muzzle_flash(world_pos: Vector2, direction: Vector2, tint: Color = Palette.AMBER, size: float = 30.0) -> void:
	var host := _host()
	if not host:
		return
	var fx := ShapeFX.new()
	fx.mode = ShapeFX.Mode.CONE
	fx.color = tint
	fx.direction = direction.normalized()
	fx.end_radius = size
	fx.start_width = size * 0.38
	fx.duration = 0.09
	fx.count = 1
	host.add_child(fx)
	fx.global_position = world_pos
	light_flash(world_pos, tint, 2.4, size / 26.0, 0.12)

func dust_puff(world_pos: Vector2, tint: Color = Color(Palette.MIST, 0.55), count: int = 4, radius: float = 22.0) -> void:
	var host := _host()
	if not host:
		return
	var fx := ShapeFX.new()
	fx.mode = ShapeFX.Mode.PUFF
	fx.color = tint
	fx.count = count
	fx.start_radius = 3.5
	fx.end_radius = radius
	fx.duration = 0.42
	fx.additive = false
	host.add_child(fx)
	fx.global_position = world_pos

func impact(world_pos: Vector2, direction: Vector2 = Vector2.ZERO, tint: Color = COLOR_DAMAGE, strength: float = 1.0) -> void:
	var spread: float = TAU if direction.length() < 0.01 else PI * 0.7
	hit_spark(world_pos, tint, int(6 + 6 * strength), direction, spread, 26.0 + 22.0 * strength)
	ring_burst(world_pos, tint, 4.0, 26.0 + 34.0 * strength, 0.24, 5.0)
	light_flash(world_pos, tint, 1.6 * strength, 0.5 + 0.3 * strength, 0.16)

## Gezackter Blitz zwischen zwei Punkten (Kettenblitz, Gewitter-Treffer).
func lightning(from: Vector2, to: Vector2, tint: Color = Palette.TEAL, segments: int = 8, jitter: float = 18.0) -> void:
	var host := _host()
	if not host:
		return

	var pixel := pixel_size()
	var line := Line2D.new()
	line.width = pixel
	line.default_color = tint
	line.z_index = 160
	line.z_as_relative = false
	# Eckige Enden statt runder - passt zum Pixel-Look.
	line.begin_cap_mode = Line2D.LINE_CAP_BOX
	line.end_cap_mode = Line2D.LINE_CAP_BOX
	line.joint_mode = Line2D.LINE_JOINT_SHARP
	line.antialiased = false

	var additive := CanvasItemMaterial.new()
	additive.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	line.material = additive

	var normal := (to - from).orthogonal().normalized()
	for i in segments + 1:
		var t: float = float(i) / float(segments)
		var point: Vector2 = from.lerp(to, t)
		if i > 0 and i < segments:
			point += normal * randf_range(-jitter, jitter)
		line.add_point(PixelDraw.snap(point, pixel))

	host.add_child(line)

	var tween := line.create_tween()
	tween.set_parallel(true)
	tween.tween_property(line, "modulate:a", 0.0, 0.28)
	tween.tween_property(line, "width", 1.0, 0.28)
	tween.chain().tween_callback(line.queue_free)

## Kurzer Lichtblitz an einer Weltposition.
func light_flash(world_pos: Vector2, tint: Color = Palette.AMBER, energy: float = 2.0, light_scale: float = 1.0, duration: float = 0.18) -> void:
	var host := _host()
	if not host:
		return
	var light := LightFlash.new()
	light.color = tint
	light.peak_energy = energy
	light.start_scale = light_scale
	light.end_scale = light_scale * 1.6
	light.duration = duration
	host.add_child(light)
	light.global_position = world_pos

func afterimage(source: Node2D, lifetime: float = 0.35, tint: Color = Color(1.0, 1.0, 1.0, 0.4)) -> void:
	var host := _host()
	if not host or not is_instance_valid(source):
		return

	var texture: Texture2D = null
	var flip_h: bool = false

	if source is Sprite2D:
		texture = source.texture
		flip_h = source.flip_h
	elif source is AnimatedSprite2D:
		var frames: SpriteFrames = source.sprite_frames
		if frames and frames.has_animation(source.animation):
			texture = frames.get_frame_texture(source.animation, source.frame)
		flip_h = source.flip_h

	if not texture:
		return

	var ghost := Sprite2D.new()
	ghost.texture = texture
	ghost.flip_h = flip_h
	ghost.modulate = tint
	ghost.z_index = source.z_index - 1
	ghost.z_as_relative = false
	host.add_child(ghost)
	ghost.global_transform = source.get_global_transform()

	var tween := ghost.create_tween()
	tween.set_parallel(true)
	tween.tween_property(ghost, "modulate:a", 0.0, lifetime)
	tween.tween_property(ghost, "scale", ghost.scale * 0.88, lifetime)
	tween.chain().tween_callback(ghost.queue_free)

func flash(target: CanvasItem, tint: Color = Color(6.0, 6.0, 6.0), duration: float = 0.1) -> void:
	if not is_instance_valid(target):
		return
	target.self_modulate = tint
	var tween := target.create_tween()
	tween.tween_property(target, "self_modulate", Color.WHITE, duration).set_ease(Tween.EASE_OUT)

func shake(amount: float) -> void:
	var camera := _get_camera()
	if camera and camera.has_method("shake"):
		camera.shake(amount)

func zoom_punch(amount: float = 0.06) -> void:
	var camera := _get_camera()
	if camera and camera.has_method("punch_zoom"):
		camera.punch_zoom(amount)

func hitstop(duration: float = 0.06, time_scale: float = 0.05) -> void:
	var hit_stop := get_node_or_null("/root/HitStop")
	if hit_stop and hit_stop.has_method("trigger"):
		hit_stop.trigger(duration, time_scale)

func screen_flash(color: Color = Color(1.0, 1.0, 1.0, 0.35), duration: float = 0.25) -> void:
	screen_flash_requested.emit(color, duration)

func _get_camera() -> Node:
	if not is_inside_tree():
		return null
	return get_tree().get_first_node_in_group("camera")
