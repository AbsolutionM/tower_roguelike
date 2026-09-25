extends Node

var is_active: bool = false
var end_time_msec: int = 0

func trigger(duration: float = 0.1, slow_scale: float = 0.05) -> void:
	if is_active:
		return
	is_active = true

	Engine.time_scale = slow_scale * DevMode.time_scale
	end_time_msec = Time.get_ticks_msec() + int(duration * 1000.0)

func _process(_delta: float) -> void:
	if is_active and Time.get_ticks_msec() >= end_time_msec:
		# Zurück zum Grundtempo - im Dev-Modus kann das Zeitlupe oder Zeitraffer sein.
		Engine.time_scale = DevMode.time_scale
		is_active = false
