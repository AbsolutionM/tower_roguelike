extends Resource
class_name SoundBank

## Sammlung aller Töne des Spiels. Neuer Ton = neuer Eintrag hier, kein Code.
##
## Die IDs sind fest verdrahtet (siehe Audio.ID_*), damit ein Tippfehler
## in der Resource nicht still bleibt.

@export var entries: Array[SoundEntry] = []

func get_entry(sound_id: String) -> SoundEntry:
	for entry in entries:
		if entry and entry.sound_id == sound_id:
			return entry
	return null
