extends Node

## Hält das aktuelle Wetter. Spieler, Gegner und HUD fragen hier nach.

signal weather_changed(weather: WeatherData)

var current: WeatherData

func set_weather(weather: WeatherData) -> void:
	current = weather
	weather_changed.emit(current)

func clear() -> void:
	set_weather(null)

func get_player_speed_mult() -> float:
	return current.player_speed_mult if current else 1.0

func get_player_damage_mult() -> float:
	return current.player_damage_mult if current else 1.0

func get_player_regen_bonus() -> float:
	return current.player_regen_bonus if current else 0.0

func get_pickup_radius_mult() -> float:
	return current.pickup_radius_mult if current else 1.0

func get_enemy_speed_mult() -> float:
	return current.enemy_speed_mult if current else 1.0

func get_ambient_tint() -> Color:
	return current.ambient_tint if current else Color(1.0, 1.0, 1.0)
