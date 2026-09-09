extends Node

## Zentraler Tonausgang. Alles im Spiel ruft `Audio.play(Audio.ID_...)`.
##
## Töne kommen aus `resources/audio/bank.tres` - dort trägt man die Dateien
## ein, ohne Code anzufassen. Fehlt ein Eintrag, passiert schlicht nichts;
## das Spiel läuft also auch mit halb gefüllter Bank.
##
## Warum ein Pool statt eines Players pro Ton: bei schnellen Waffen fallen
## Dutzende Treffer pro Sekunde an, und jeder neue Node wäre eine Zuteilung
## mitten im Kampf.

const BANK_PATH := "res://resources/audio/bank.tres"
const VOICES := 14

# --- Feste IDs. Wer einen neuen Ton will, ergänzt hier und in der Bank. ---
const ID_ENEMY_HIT := "enemy_hit"
const ID_ENEMY_DIE := "enemy_die"
const ID_PLAYER_HURT := "player_hurt"
const ID_PLAYER_DIE := "player_die"
const ID_SHOOT := "shoot"
const ID_SWING := "swing"
const ID_DASH := "dash"
const ID_ABILITY := "ability"
const ID_SPECIAL := "special"
const ID_PICKUP := "pickup"
const ID_COIN := "coin"
const ID_PURCHASE := "purchase"
const ID_FORGE := "forge"
const ID_LEVEL_UP := "level_up"
const ID_BOSS_SPAWN := "boss_spawn"
const ID_ROOM_CHANGE := "room_change"
const ID_UI_TAP := "ui_tap"

var bank: SoundBank

var _voices: Array[AudioStreamPlayer] = []
var _next_voice: int = 0
## sound_id -> Zeitpunkt der letzten Wiedergabe.
var _last_played: Dictionary = {}

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	if ResourceLoader.exists(BANK_PATH):
		# Ohne Cache laden: sonst haelt der Ressourcen-Cache die Tonbank noch,
		# wenn das Autoload beim Beenden schon aufgeraeumt hat, und Godot
		# meldet "resources still in use at exit".
		bank = ResourceLoader.load(BANK_PATH, "", ResourceLoader.CACHE_MODE_IGNORE_DEEP) as SoundBank

	for i in VOICES:
		var player := AudioStreamPlayer.new()
		player.bus = "Master"
		add_child(player)
		_voices.append(player)

## Spielt einen Ton aus der Bank. Unbekannte ID = still, kein Fehler.
func play(sound_id: String, volume_offset: float = 0.0) -> void:
	if not bank:
		return
	var entry := bank.get_entry(sound_id)
	if not entry:
		return

	var stream := entry.pick()
	if not stream:
		return

	# Zu dichte Wiederholungen zusammenfassen - sonst wird Dauerfeuer zu Lärm.
	var now: float = float(Time.get_ticks_msec()) / 1000.0
	if now - float(_last_played.get(sound_id, -99.0)) < entry.min_interval:
		return
	_last_played[sound_id] = now

	var player := _take_voice()
	player.stream = stream
	player.volume_db = entry.volume_db + volume_offset
	player.pitch_scale = randf_range(entry.pitch_min, entry.pitch_max)
	player.play()

## Reihum den nächsten Player - der älteste wird notfalls unterbrochen.
func _take_voice() -> AudioStreamPlayer:
	for i in _voices.size():
		var index: int = (_next_voice + i) % _voices.size()
		if not _voices[index].playing:
			_next_voice = (index + 1) % _voices.size()
			return _voices[index]
	var fallback := _voices[_next_voice]
	_next_voice = (_next_voice + 1) % _voices.size()
	return fallback

## Beim Beenden die Streams loesen. Ohne das haelt der Pool die Tonbank
## fest und Godot meldet "resources still in use at exit".
func _exit_tree() -> void:
	for player in _voices:
		if is_instance_valid(player):
			player.stop()
			player.stream = null
	# Auch die Bank selbst leeren: die Eintraege halten die Streams sonst
	# ueber das Ende der Szene hinaus fest.
	if bank:
		for entry in bank.entries:
			if entry:
				entry.streams.clear()
		bank.entries.clear()
	bank = null

## Welche IDs die Bank noch nicht abdeckt - fürs Nachlegen von Dateien.
func missing_ids() -> Array[String]:
	var wanted: Array[String] = [
		ID_ENEMY_HIT, ID_ENEMY_DIE, ID_PLAYER_HURT, ID_PLAYER_DIE,
		ID_SHOOT, ID_SWING, ID_DASH, ID_ABILITY, ID_SPECIAL,
		ID_PICKUP, ID_COIN, ID_PURCHASE, ID_FORGE, ID_LEVEL_UP,
		ID_BOSS_SPAWN, ID_ROOM_CHANGE, ID_UI_TAP
	]
	var missing: Array[String] = []
	for id in wanted:
		var entry := bank.get_entry(id) if bank else null
		if not entry or entry.streams.is_empty():
			missing.append(id)
	return missing
