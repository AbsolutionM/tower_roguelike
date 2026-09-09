extends Control
class_name WeatherOverlay

## Zeichnet Regen, Schnee, Nebel und Blitze im Bildschirmraum.
## Braucht keine Texturen und ist unabhängig von der Kamera.

var _positions: PackedVector2Array = PackedVector2Array()
var _speeds: PackedFloat32Array = PackedFloat32Array()
var _lightning_timer: float = 0.0

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	Weather.weather_changed.connect(_on_weather_changed)
	_rebuild(Weather.current)

func _on_weather_changed(weather: WeatherData) -> void:
	_rebuild(weather)

func _rebuild(weather: WeatherData) -> void:
	_positions = PackedVector2Array()
	_speeds = PackedFloat32Array()
	_lightning_timer = weather.lightning_interval if weather else 0.0

	if not weather or weather.particle_count <= 0:
		queue_redraw()
		return

	var view := get_viewport_rect().size
	for i in weather.particle_count:
		_positions.append(Vector2(randf() * view.x, randf() * view.y))
		_speeds.append(randf_range(0.75, 1.3))
	queue_redraw()

func _process(delta: float) -> void:
	var weather: WeatherData = Weather.current
	if not weather:
		return

	_tick_lightning(weather, delta)

	if _positions.is_empty():
		return

	var view := get_viewport_rect().size
	var angle := deg_to_rad(weather.particle_angle_degrees)
	var direction := Vector2(sin(angle), cos(angle))

	for i in _positions.size():
		var next: Vector2 = _positions[i] + direction * weather.particle_speed * _speeds[i] * delta
		if next.y > view.y + 40.0:
			next = Vector2(randf() * view.x, -40.0)
		elif next.x < -40.0:
			next.x = view.x + 20.0
		elif next.x > view.x + 40.0:
			next.x = -20.0
		_positions[i] = next

	queue_redraw()

func _tick_lightning(weather: WeatherData, delta: float) -> void:
	if weather.lightning_interval <= 0.0:
		return
	_lightning_timer -= delta
	if _lightning_timer > 0.0:
		return
	_lightning_timer = weather.lightning_interval * randf_range(0.6, 1.4)
	FX.screen_flash(weather.lightning_color, 0.35)
	FX.shake(3.0)

func _draw() -> void:
	var weather: WeatherData = Weather.current
	if not weather:
		return

	var view := get_viewport_rect().size

	if weather.overlay_color.a > 0.0:
		draw_rect(Rect2(Vector2.ZERO, view), weather.overlay_color)

	if _positions.is_empty():
		return

	var angle := deg_to_rad(weather.particle_angle_degrees)
	var direction := Vector2(sin(angle), cos(angle))

	var pixel: float = maxf(weather.particle_width, 2.0)

	if weather.kind == WeatherData.Kind.SNOW or weather.kind == WeatherData.Kind.ASH:
		for i in _positions.size():
			PixelDraw.stamp(self, _positions[i], pixel * _speeds[i], weather.particle_color, weather.particle_texture)
		return

	for i in _positions.size():
		var start: Vector2 = _positions[i]
		var end: Vector2 = start + direction * weather.particle_length * _speeds[i]
		PixelDraw.line(self, start, end, pixel, weather.particle_color, weather.particle_texture)
