extends Resource
class_name SoundEntry

## Ein benannter Ton. Mehrere Streams = bei jedem Abspielen wird gewürfelt,
## damit sich derselbe Treffer nicht wie eine Schreibmaschine anhört.

@export var sound_id: String = ""
@export var streams: Array[AudioStream] = []
@export_range(-40.0, 12.0) var volume_db: float = 0.0
@export_range(0.1, 3.0) var pitch_min: float = 0.94
@export_range(0.1, 3.0) var pitch_max: float = 1.06
## Kürzester Abstand zwischen zwei Wiedergaben. Verhindert Klangbrei bei
## schnellen Waffen.
@export_range(0.0, 1.0) var min_interval: float = 0.04

func pick() -> AudioStream:
	if streams.is_empty():
		return null
	return streams[randi() % streams.size()]
