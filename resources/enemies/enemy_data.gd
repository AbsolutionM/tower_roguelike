extends Resource
class_name EnemyData

enum Behavior { CHASE, CHARGER, SHOOTER, ORBITER }
enum Movement { GROUND, HOP, FLY }

@export var enemy_name: String = "Gegner"
@export var max_health: float = 30.0
@export var move_speed: float = 40.0
## Leer lassen, dann wird das Platzhalter-Symbol gezeichnet.
@export var sprite_texture: Texture2D
@export var sprite_scale: float = 1.0
@export var tint: Color = Color(1.0, 1.0, 1.0)
@export var symbol: EnemySymbol.Kind = EnemySymbol.Kind.BLOB
@export var symbol_size: float = 26.0

@export_group("Bewegungsart")
@export var movement: Movement = Movement.GROUND
## HOP: Pause zwischen den Sprüngen.
@export var hop_interval: float = 1.0
@export var hop_height: float = 36.0
@export var hop_duration: float = 0.42
## Während des Sprungs wird das Tempo damit multipliziert.
@export var hop_speed_mult: float = 2.8
## FLY: Schwebehöhe und Auf-und-Ab.
@export var fly_height: float = 30.0
@export var fly_bob: float = 7.0

@export_group("Verhalten")
@export var behavior: Behavior = Behavior.CHASE
@export var contact_damage: float = 8.0
@export var contact_range: float = 38.0
@export var attack_cooldown: float = 1.2
@export var charge_speed: float = 430.0
@export var charge_windup: float = 0.55
@export var charge_trigger_range: float = 260.0
@export var keep_distance: float = 190.0
@export var shoot_range: float = 340.0
@export var projectile_scene: PackedScene
@export var projectile_speed: float = 240.0
@export var projectile_damage: float = 6.0

@export_group("Optik")
@export var trail_colors: Array[Color] = [
	Color(0.4, 0.8, 0.3, 0.45),
	Color(0.3, 0.6, 0.25, 0.4),
	Color(0.55, 0.85, 0.4, 0.5)
]
@export var squash_amount: float = 0.15
@export var squash_speed: float = 6.0
@export var knockback_friction: float = 600.0
@export var shadow_radius: float = 16.0

@export_group("Spezialfähigkeiten")
## Explodiert beim Tod und trifft den Spieler im Umkreis.
@export var explode_on_death: bool = false
@export var explosion_damage: float = 18.0
@export var explosion_radius: float = 130.0
## Zerfällt beim Tod in kleinere Gegner.
@export var split_data: EnemyData
@export var split_count: int = 2
## Heilt andere Gegner in der Nähe (0 = aus).
@export var heal_aura_rate: float = 0.0
@export var heal_aura_radius: float = 170.0

@export_group("Boss")
@export var is_boss: bool = false
@export var boss_title: String = ""
## Wird in Phasenwechseln und beim Spezialangriff gerufen.
@export var minion_data: EnemyData
@export var minions_per_wave: int = 3
@export var spray_projectiles: int = 12
@export var special_interval: float = 3.4

@export_group("Loot")
@export var drop_table: DropTable
@export var essence_id: String = ""
@export_range(0.0, 1.0) var essence_chance: float = 0.0
