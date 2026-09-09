extends Node
class_name TestHarness

@export var characters: Array[CharacterData] = []
@export var weapons: Array[WeaponData] = []

var character_index: int = 0
var weapon_index: int = 0

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("debug_next_character"):
		next_character()
	elif event.is_action_pressed("debug_next_weapon"):
		next_weapon()
	elif event.is_action_pressed("debug_next_room"):
		next_room()

func next_character() -> void:
	if characters.is_empty():
		return
	var player = get_tree().get_first_node_in_group("player")
	if not player:
		return
	character_index = (character_index + 1) % characters.size()
	player.character_data = characters[character_index]
	if player.has_method("apply_character_data"):
		player.apply_character_data()
	print("Charakter: ", characters[character_index].character_name)

func next_weapon() -> void:
	if weapons.is_empty():
		return
	var player = get_tree().get_first_node_in_group("player")
	if not player:
		return
	var weapon_controller = player.get_node_or_null("WeaponController")
	if not weapon_controller:
		return
	weapon_index = (weapon_index + 1) % weapons.size()
	weapon_controller.equipped_weapon = weapons[weapon_index]
	print("Waffe: ", weapons[weapon_index].weapon_name)

func next_room() -> void:
	var room_controller = get_tree().get_first_node_in_group("room_controller")
	if room_controller and room_controller.has_method("force_next_room"):
		room_controller.force_next_room()
		print("Erzwinge Raumwechsel...")
