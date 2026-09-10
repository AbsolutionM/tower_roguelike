extends Node

## Temporär: Rundgang über alle Bildschirme nach der Verkleinerung.

func _ready() -> void:
	DisplayServer.window_set_size(Vector2i(720, 1280))
	await get_tree().create_timer(0.6).timeout

	RunState.add_gold(4000)
	RunState.add_essence("slime", 40)
	RunState.add_to_stash("iron_scrap", 18)
	RunState.add_to_stash("ore_chunk", 12)
	RunState.add_to_stash("slime_gel", 22)
	for id in ["katar", "greataxe", "bow_hunter", "whip_thorn", "chakram"]:
		RunState.unlock_weapon(id)

	var town := get_tree().current_scene
	var names := ["shop", "held", "start", "werkstatt", "upgrades"]
	for i in 5:
		town._select_tab(i)
		await get_tree().create_timer(1.1).timeout
		await _shot("R%d_%s" % [i, names[i]])

	get_tree().change_scene_to_file("res://scenes/game.tscn")
	for i in 3:
		await get_tree().create_timer(6.0).timeout
		await _shot("R%d_kampf" % (5 + i))

	RunState.end_run(true)
	get_tree().change_scene_to_file("res://scenes/ui/run_end.tscn")
	await get_tree().create_timer(1.3).timeout
	await _shot("R9_ende")
	get_tree().quit()

func _shot(shot_name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("user://" + shot_name + ".png")
