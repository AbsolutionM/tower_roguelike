extends Resource
class_name WeatherData

## Wetter eines Turms: verändert Optik und Spielwerte.

enum Kind { CLEAR, RAIN, SNOW, FOG, STORM, ASH }

@export var weather_id: String = ""
@export var weather_name: String = "Klar"
@export var kind: Kind = Kind.CLEAR
@export_multiline var description: String = ""

@export_group("Optik")
## Wird mit der Grundbeleuchtung des Turms multipliziert.
@export var ambient_tint: Color = Color(1.0, 1.0, 1.0)
## Vollflächiger Schleier (Nebel, Dunst). Alpha 0 = aus.
@export var overlay_color: Color = Color(0.5, 0.6, 0.8, 0.0)
@export var particle_count: int = 0
## Optional: Textur pro Partikel. Leer = Pixelblöcke.
@export var particle_texture: Texture2D
@export var particle_color: Color = Color(0.7, 0.82, 1.0, 0.5)
@export var particle_speed: float = 900.0
@export var particle_length: float = 26.0
@export var particle_width: float = 2.0
@export var particle_angle_degrees: float = 12.0
## Sekunden zwischen Blitzen. 0 = keine Blitze.
@export var lightning_interval: float = 0.0
@export var lightning_color: Color = Color(0.85, 0.9, 1.0, 0.5)

@export_group("Auswirkungen")
@export var player_speed_mult: float = 1.0
@export var player_damage_mult: float = 1.0
## Zusätzliche Lebensregeneration pro Sekunde.
@export var player_regen_bonus: float = 0.0
@export var pickup_radius_mult: float = 1.0
@export var enemy_speed_mult: float = 1.0

## Kurze Zusammenfassung der Auswirkungen für die Menüs.
func describe_effects() -> String:
	var parts: Array[String] = []
	if not is_equal_approx(player_speed_mult, 1.0):
		parts.append("%+d%% Tempo" % int(round((player_speed_mult - 1.0) * 100.0)))
	if not is_equal_approx(player_damage_mult, 1.0):
		parts.append("%+d%% Schaden" % int(round((player_damage_mult - 1.0) * 100.0)))
	if not is_zero_approx(player_regen_bonus):
		parts.append("%+.1f Regeneration" % player_regen_bonus)
	if not is_equal_approx(pickup_radius_mult, 1.0):
		parts.append("%+d%% Sammelradius" % int(round((pickup_radius_mult - 1.0) * 100.0)))
	if not is_equal_approx(enemy_speed_mult, 1.0):
		parts.append("%+d%% Gegnertempo" % int(round((enemy_speed_mult - 1.0) * 100.0)))
	return ", ".join(parts)
