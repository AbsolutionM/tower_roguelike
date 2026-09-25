extends Node2D
class_name WeaponController

## Sucht das Ziel, dreht die Waffe dorthin und schlägt zu.
## Das Ziel wird jede Sekunde neu bestimmt - auch während der Abklingzeit,
## damit man vor dem Schlag sieht, wen es trifft.

signal target_changed(target: Node2D)
## Der Sonderschlag hat sich weiterbewegt (0..1) - fuers HUD.
signal special_charge_changed(ratio: float)

## Der gezeichnete Platzhalter rechnet in ganzen Pixeln - dieser Faktor bringt
## ihn auf dieselbe Größe wie ein echtes Haltesprite.
## Der gezeichnete Platzhalter ist keine Pixelkunst und bleibt in seiner
## alten Groesse, obwohl die Klinge jetzt ohne Zwischenskalierung haengt.
const PLACEHOLDER_SCALE := 0.33

## Weltdrehung des Haltesprites im Ruhezustand. Die Klingen sind im Sprite
## diagonal nach oben rechts gezeichnet; -45 Grad stellt sie senkrecht.
const UPRIGHT_ROTATION := -PI * 0.25
## Anhebung der vorgestreckten Ruhehaltung beidhändiger Klingen.
const REST_TILT := deg_to_rad(25.0)
## Vorlauf der Klinge vor dem Arm im Schlag.
const STRIKE_LEAD := 0.45

@export var equipped_weapon: WeaponData
@export var sword: Node
@export var weapon_pivot: Node2D
@export var show_target_marker: bool = true

var fire_timer: float = 0.0
var current_target: Node2D = null

## Halber Öffnungswinkel des Angriffskegels. Angegriffen wird nur, wer vor
## dem Helden steht - in der Richtung, in die er läuft; der Schwung deckt
## mit seinen 55 Grad je Seite den Kegel gerade ab.
const CONE_HALF_ANGLE := deg_to_rad(50.0)

## Laufrichtung des Trägers, vom Spieler gelesen.
func _facing() -> Vector2:
	var player := get_parent()
	if player and "facing" in player:
		var facing: Vector2 = player.facing
		if facing.length_squared() > 0.001:
			return facing.normalized()
	return Vector2.DOWN

var _stats: PlayerStats
var _visualized_weapon: WeaponData
var _hold_sprite_base_scale: Vector2 = Vector2.ONE
## Reichweite der Klinge in Weltpixeln, aus dem Sprite gemessen.
var _melee_reach: float = 0.0
var _hold_sprite_base_rotation: float = 0.0
var _hold_placeholder: WeaponSymbol
var _marker: TargetMarker
var _last_cooldown: float = 1.0
## Gelandete Treffer seit dem letzten Sonderschlag.
var _special_hits: int = 0

func _ready() -> void:
	var parent := get_parent()
	if parent:
		_stats = parent.get_node_or_null("PlayerStats")

	var hold_sprite := _get_hold_sprite()
	if hold_sprite:
		_hold_sprite_base_scale = hold_sprite.scale
		_hold_sprite_base_rotation = hold_sprite.rotation

	if _stats:
		_stats.hit_landed.connect(_on_hit_landed)
	RunState.run_upgrades_changed.connect(_on_run_upgrades_changed)

	# Nachladeleiste über dem Kopf des Helden.
	if parent:
		var cooldown_bar := WeaponCooldownBar.new()
		cooldown_bar.controller = self
		parent.add_child.call_deferred(cooldown_bar)

	if show_target_marker:
		_marker = TargetMarker.new()
		_marker.setup(parent as Node2D)
		add_child(_marker)

func _process(delta: float) -> void:
	# Freigegebene Objekte sind in GDScript "falsy" - deshalb hier zuerst
	# is_instance_valid prüfen, sonst bleibt eine tote Referenz stehen.
	if not is_instance_valid(current_target):
		current_target = null
	if weapon_pivot:
		weapon_pivot.aim_direction = _facing()

	if not equipped_weapon:
		_set_target(null)
		return

	if equipped_weapon != _visualized_weapon:
		_apply_weapon_visuals()

	fire_timer -= delta

	_set_target(find_target_in_range())
	_update_marker()
	_update_hold_orientation()

	if fire_timer > 0.0 or not current_target or not _aim_settled():
		return

	var roll := _roll_damage()
	if equipped_weapon.is_melee:
		if sword and sword.has_method("perform_swing"):
			sword.perform_swing(roll["damage"], roll["crit"])
	else:
		fire_at(current_target, roll["damage"], roll["crit"])

	_last_cooldown = equipped_weapon.cooldown / maxf(_get_attack_speed(), 0.05)
	fire_timer = _last_cooldown

# --- Sonderschlag ----------------------------------------------------------

## Jeder gelandete Treffer laedt auf. Ist die Waffe voll, loest sie von selbst
## aus - der Spieler muss dafuer nichts druecken.
func _on_hit_landed() -> void:
	var special := _current_special()
	if not special:
		return

	_special_hits += 1
	special_charge_changed.emit(get_special_charge())
	if _special_hits < _hits_required(special):
		return

	_special_hits = 0
	special_charge_changed.emit(0.0)
	# Fernkampftreffer melden aus einem Physik-Callback heraus. Geschosse
	# dort einzuhaengen bricht mit "flushing queries" ab - also verzoegert.
	_fire_special.call_deferred(special)

func _current_special() -> WeaponSpecial:
	return equipped_weapon.special if equipped_weapon else null

## Ladestand von 0 bis 1, fuer die Anzeige im HUD.
func get_special_charge() -> float:
	var special := _current_special()
	if not special or special.hits_required <= 0:
		return 0.0
	return clampf(float(_special_hits) / float(_hits_required(special)), 0.0, 1.0)

## Ladung-Upgrades senken die nötigen Treffer, nie unter zwei.
func _hits_required(special: WeaponSpecial) -> int:
	var fewer: int = int(_stats.upgrade("charge", equipped_weapon)) if _stats else 0
	return maxi(special.hits_required - fewer, 2)

# --- Lauf-Upgrades und Evolution -------------------------------------------

func _on_run_upgrades_changed() -> void:
	if not equipped_weapon:
		return
	if WeaponUpgrades.can_evolve(equipped_weapon):
		_evolve()
	else:
		_configure_swing()

## Nächste Stufe der Linie: neue Werte (Upgrades bleiben als Prozente),
## Weißblitz, Hit-Stop und ein voll geladener Sonderschlag.
func _evolve() -> void:
	var next: WeaponData = equipped_weapon.next_tier
	equipped_weapon = next
	RunState.run_weapon = next
	RunState.loadout_changed.emit()
	var player := get_parent() as Node2D
	var origin: Vector2 = player.global_position if player else global_position
	FX.screen_flash(Color(1.0, 1.0, 1.0, 0.7), 0.4)
	FX.hitstop(0.25, 0.05)
	FX.ring_burst(origin, Palette.GOLD, 10.0, 160.0, 0.5, 8.0)
	FX.floating_text(origin + Vector2(0.0, -100.0), "%s  (Stufe %s)" % [next.weapon_name, WeaponUpgrades.tier_name(next)], Palette.GOLD, 24, 60.0)
	Audio.play(Audio.ID_LEVEL_UP)
	_apply_weapon_visuals()
	var special := _current_special()
	if special:
		_special_hits = _hits_required(special) - 1
		special_charge_changed.emit(get_special_charge())
	RunState.weapon_evolved.emit(next)

func _fire_special(special: WeaponSpecial) -> void:
	var player := get_parent() as Node2D
	if not player:
		return
	Audio.play(Audio.ID_SPECIAL)
	var base: float = _stats.get_weapon_base_damage(equipped_weapon) if _stats else equipped_weapon.damage
	WeaponSpecialRunner.execute(special, equipped_weapon, player, current_target, base)

# --- Zielerfassung ---------------------------------------------------------

## Erst zuschlagen, wenn der Handkreis in Laufrichtung zeigt. Sonst löst
## beim Umdrehen ein Schlag aus, dessen Bogen noch halb auf der alten Seite
## liegt - und der Schlag friert die Drehung ein.
const AIM_SETTLED := deg_to_rad(20.0)

func _aim_settled() -> bool:
	if not weapon_pivot:
		return true
	return absf(angle_difference(weapon_pivot.aim_rotation, _facing().angle())) <= AIM_SETTLED

## Mitte des Handkreises in der Welt. Von hier aus reichen Arm und Klinge -
## nicht vom Knotenursprung, der eine Gürtelhöhe darüber liegt.
func attack_origin() -> Vector2:
	if weapon_pivot:
		return global_position + weapon_pivot.position
	return global_position

## Reichweite, in der tatsächlich getroffen wird - Nahkampf rechnet den Arm mit.
func get_attack_range() -> float:
	if not equipped_weapon:
		return 0.0
	if equipped_weapon.is_melee and weapon_pivot:
		return weapon_pivot.pivot_radius + _melee_reach
	return equipped_weapon.weapon_range * _reach_mult()

func _reach_mult() -> float:
	return 1.0 + (_stats.upgrade("reach", equipped_weapon) if _stats else 0.0)

## Der nächste Gegner im Kegel vor dem Helden. Wer seitlich oder hinter
## ihm steht, wird nicht angegriffen - man muss sich ihm zuwenden.
func find_target_in_range() -> Node2D:
	var max_range := get_attack_range()
	# Der Kegel liegt dort, wo der Handkreis gerade hinzeigt - nicht dort,
	# wohin der Held schon laufen will. Sonst löst beim Umdrehen ein Schlag
	# aus, während die Klinge noch auf der alten Seite ist.
	var facing := Vector2.RIGHT.rotated(weapon_pivot.aim_rotation) if weapon_pivot else _facing()
	var origin := attack_origin()
	var nearest: Node2D = null
	var nearest_distance: float = max_range

	for enemy in get_tree().get_nodes_in_group("enemies"):
		if not is_instance_valid(enemy):
			continue
		# Der Körper zählt, nicht der Mittelpunkt: wer den Kegel mit dem Rand
		# berührt, wird angegriffen. Dafür der Kreis um den Gegner - Abstand
		# minus Radius gegen die Reichweite, Winkel minus halbe Sichtbreite
		# gegen die Kegelöffnung.
		var radius: float = enemy.get_visual_radius() if enemy.has_method("get_visual_radius") else 20.0
		var offset: Vector2 = enemy.global_position - origin
		var distance := offset.length()
		var edge_distance: float = distance - radius
		if edge_distance >= nearest_distance:
			continue
		if distance > radius:
			var half_width: float = asin(clampf(radius / distance, 0.0, 1.0))
			if absf(facing.angle_to(offset)) - half_width > CONE_HALF_ANGLE:
				continue
		nearest_distance = edge_distance
		nearest = enemy

	return nearest

func _set_target(new_target: Node2D) -> void:
	if not is_instance_valid(current_target):
		current_target = null
	if new_target == current_target:
		return

	if is_instance_valid(current_target) and current_target.has_method("set_targeted"):
		current_target.set_targeted(false)

	current_target = new_target

	if current_target and current_target.has_method("set_targeted"):
		current_target.set_targeted(true)

	target_changed.emit(current_target)

func _update_marker() -> void:
	if not _marker:
		return
	_marker.target = current_target
	_marker.origin_offset = weapon_pivot.position if weapon_pivot else Vector2.ZERO
	_marker.attack_range = get_attack_range()
	# Der Kegel folgt dem Kreis, nicht der rohen Laufrichtung - so dreht er
	# sich weich mit, statt bei jedem Richtungswechsel zu springen.
	_marker.cone_direction = weapon_pivot.aim_rotation if weapon_pivot else _facing().angle()
	_marker.cone_half_angle = CONE_HALF_ANGLE
	# Bei Fernkampf ist der Ring so groß wie der halbe Raum und damit nur
	# Störung. Im Nahkampf zeigt er, wie weit man wirklich trifft.
	_marker.show_range_ring = equipped_weapon.is_melee
	_marker.accent = equipped_weapon.projectile_color if not equipped_weapon.is_melee else Palette.AMBER
	_marker.cooldown_ratio = 1.0 - clampf(fire_timer / maxf(_last_cooldown, 0.001), 0.0, 1.0)

# --- Waffe -----------------------------------------------------------------

func _get_attack_speed() -> float:
	if not _stats:
		return 1.0
	return float(_stats.get_weapon_modifiers(equipped_weapon)["attack_speed"])

func _get_hold_sprite() -> Sprite2D:
	if not sword:
		return null
	return sword.sprite

## Setzt das Waffen-Sprite in der Hand aus der WeaponData-Resource.
func _apply_weapon_visuals() -> void:
	_visualized_weapon = equipped_weapon
	_last_cooldown = equipped_weapon.cooldown
	# Eine neue Waffe faengt mit leerem Sonderschlag an.
	_special_hits = 0
	special_charge_changed.emit(0.0)

	if weapon_pivot:
		weapon_pivot.two_handed = equipped_weapon.two_handed
		weapon_pivot.extra_radius = float(equipped_weapon.hand_reach_texels) * WeaponData.PIXEL_SCALE

	var hold_sprite := _get_hold_sprite()
	if not hold_sprite:
		return

	var has_texture: bool = equipped_weapon.hold_texture != null
	if has_texture:
		hold_sprite.texture = equipped_weapon.hold_texture
	hold_sprite.scale = _hold_sprite_base_scale * equipped_weapon.hold_scale
	hold_sprite.rotation = _rest_rotation()
	hold_sprite.position = Vector2.ZERO
	hold_sprite.offset = _hold_offset(hold_sprite)
	hold_sprite.visible = has_texture

	# Ohne Haltesprite wird ein Platzhalter gezeichnet - sonst wäre die Waffe
	# unsichtbar oder es bliebe die Klinge der vorherigen Waffe stehen.
	var placeholder := _ensure_placeholder(hold_sprite)
	if not placeholder:
		return
	placeholder.visible = not has_texture
	if placeholder.visible:
		placeholder.category = equipped_weapon.category
		placeholder.tint = equipped_weapon.projectile_color if not equipped_weapon.is_melee else Palette.BONE
		placeholder.position = Vector2.ZERO
		placeholder.scale = _hold_sprite_base_scale * equipped_weapon.hold_scale * PLACEHOLDER_SCALE
		placeholder.queue_redraw()

	_configure_swing()

## Schwungdauer, Schwungwinkel und Rueckstoss der Klinge aus den Waffenwerten.
func _configure_swing() -> void:
	if not sword or not sword.has_method("configure"):
		return
	# Geschmiedete Waffen stoßen Gegner spürbar weiter zurück.
	var level: int = _stats.weapon_level(equipped_weapon) if _stats else RunState.get_weapon_level(equipped_weapon.weapon_id)
	var stagger_mult := Progression.reinforce_stagger_mult(level)
	stagger_mult *= 1.0 + (_stats.upgrade("impact", equipped_weapon) if _stats else 0.0)
	_melee_reach = _blade_reach() * _reach_mult()
	sword.configure(
		equipped_weapon.swing_duration,
		equipped_weapon.swing_angle_degrees,
		equipped_weapon.knockback * stagger_mult,
		_melee_reach
	)

## Die Reichweite ist die Klinge - gemessen am Sprite, siehe WeaponData.
func _blade_reach() -> float:
	return equipped_weapon.get_blade_reach()

## Versatz der Textur gegenueber der Faust.
## Schusswaffen liegen mittig in der Hand. Klingen sind im Sprite diagonal
## gezeichnet - der Versatz entlang dieser Diagonalen setzt den Griff in die
## Faust und laesst die Klinge herausragen, egal wie gross das Sprite ist.
func _hold_offset(sprite: Sprite2D) -> Vector2:
	if not sprite.texture or not equipped_weapon.holds_upright():
		return Vector2.ZERO
	var size: Vector2 = sprite.texture.get_size()
	return Vector2(size.x, -size.y) * WeaponData.GRIP_FRACTION

## Ruhehaltung des Sprites, wie sie in den Waffendaten steht.
func _rest_rotation() -> float:
	return _hold_sprite_base_rotation + deg_to_rad(equipped_weapon.hold_rotation_degrees)

## Klingen stehen hochkant in der Faust, statt auf den Gegner zu zeigen.
## Dafuer wird die Drehung von Arm und Schwungarm herausgerechnet - waehrend
## des Schlags nicht, sonst wuerde der Schwung stehenbleiben.
func _update_hold_orientation() -> void:
	if not equipped_weapon or not equipped_weapon.holds_upright() or not weapon_pivot:
		return
	var hold_sprite := _get_hold_sprite()
	if not hold_sprite:
		return

	# Bei gespiegeltem Arm (Zielen nach links) laufen lokale Winkel
	# andersherum: die Klinge zeigt in der Welt nach θ - (Klinge + φ) statt
	# θ + (Klinge + φ). Das Vorzeichen allein reicht nicht - es fehlt eine
	# Vierteldrehung, sonst liegt das Schwert beim Zielen nach oben quer.
	var mirrored: bool = weapon_pivot.scale.y < 0.0
	var upright: float
	if mirrored:
		upright = -(UPRIGHT_ROTATION - weapon_pivot.rotation) + PI * 0.5
	else:
		upright = UPRIGHT_ROTATION - weapon_pivot.rotation

	# Entlang des Arms: die Klinge zeigt vom Handkreis nach außen. Das ist
	# die Schlaghaltung - so reicht die Spitze in jeder Richtung gleich weit,
	# nach oben und unten wie zur Seite.
	var along: float = _rest_rotation()

	# Ruhehaltung: kleine Klingen hochkant, beidhändige vorgestreckt und
	# leicht angehoben, damit sie den Körper nicht verdecken.
	var rest: float = upright
	if equipped_weapon.two_handed:
		rest = along + (REST_TILT if mirrored else -REST_TILT)

	# Im Schlag läuft die Klinge dem Arm ein Stück voraus, in Schlagrichtung.
	var strike: float = along
	if sword and "strike_sign" in sword:
		strike += sword.strike_sign * STRIKE_LEAD * sword.swing_lead
	var blend: float = sword.swing_blend if sword and "swing_blend" in sword else 0.0
	hold_sprite.rotation = lerp_angle(rest, strike, blend)

func _ensure_placeholder(hold_sprite: Sprite2D) -> WeaponSymbol:
	if is_instance_valid(_hold_placeholder):
		return _hold_placeholder

	var host := hold_sprite.get_parent()
	if not host:
		return null

	_hold_placeholder = WeaponSymbol.new()
	# Das Symbol zeigt nach +X, die Szenen-Grundhaltung ist auf Klingen gedreht.
	_hold_placeholder.rotation = _hold_sprite_base_rotation - PI * 0.5
	_hold_placeholder.z_index = hold_sprite.z_index
	host.add_child(_hold_placeholder)
	return _hold_placeholder

func _roll_damage() -> Dictionary:
	if _stats:
		return _stats.compute_damage(_stats.get_weapon_base_damage(equipped_weapon), equipped_weapon)
	# Ohne Statistik-Knoten wenigstens die Schmiedestufe berücksichtigen.
	var level := RunState.get_weapon_level(equipped_weapon.weapon_id)
	return {"damage": equipped_weapon.get_base_damage(level), "crit": false}

func fire_at(target: Node2D, damage: float, crit: bool) -> void:
	if not equipped_weapon.projectile_scene:
		push_warning("Waffe '%s' ist Fernkampf, hat aber keine projectile_scene" % equipped_weapon.weapon_name)
		return

	var scene_root := get_tree().current_scene
	if not scene_root:
		return

	var base_direction := global_position.direction_to(target.global_position)
	var count: int = maxi(equipped_weapon.projectiles_per_shot, 1)
	var spread: float = deg_to_rad(equipped_weapon.spread_degrees)

	for i in count:
		var offset: float = 0.0
		if count > 1:
			offset = lerpf(-spread * 0.5, spread * 0.5, float(i) / float(count - 1))
		elif spread > 0.0:
			offset = randf_range(-spread * 0.5, spread * 0.5)

		var shot_direction := base_direction.rotated(offset)
		var projectile = equipped_weapon.projectile_scene.instantiate()
		scene_root.add_child(projectile)
		projectile.global_position = global_position + shot_direction * 16.0
		if projectile.has_method("setup"):
			projectile.setup(
				shot_direction,
				equipped_weapon.projectile_speed,
				damage,
				equipped_weapon.pierce_count,
				equipped_weapon.projectile_color,
				crit
			)
		# Zielsuche und Rueckkehr erst nach setup - das setzt pierce zurueck.
		if projectile.has_method("set_flight"):
			projectile.set_flight(
				equipped_weapon.homing_strength,
				equipped_weapon.return_distance,
				get_parent() as Node2D
			)

	FX.muzzle_flash(
		global_position + base_direction * 22.0,
		base_direction,
		equipped_weapon.projectile_color,
		equipped_weapon.muzzle_flash_size
	)
	Audio.play(Audio.ID_SHOOT)
	FX.shake(equipped_weapon.screen_shake)
	_recoil(base_direction)

func _recoil(direction: Vector2) -> void:
	if not weapon_pivot:
		return
	weapon_pivot.position = weapon_pivot.rest_position - direction * 5.0
	var tween := weapon_pivot.create_tween()
	tween.tween_property(weapon_pivot, "position", weapon_pivot.rest_position, 0.12).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
