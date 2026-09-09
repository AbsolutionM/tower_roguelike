extends Resource
class_name AbilityData

## Spezialfähigkeit eines Charakters (der dritte Button).
## Neue Fähigkeit = neuer Eintrag in Kind + ein Fall in PlayerAbility._execute().

enum Kind {
	SHOCKWAVE,
	BULLET_RING,
	BLINK,
	HEAL_PULSE,
	FAN_SHOT,
	DASH_STRIKE,
	SHIELD,
	TIME_SLOW,
	MAGNET_PULSE,
	CHAIN_LIGHTNING
}

@export var ability_id: String = ""
@export var ability_name: String = "Fähigkeit"
@export var icon: Texture2D
@export_multiline var description: String = ""
@export var kind: Kind = Kind.SHOCKWAVE
@export var cooldown: float = 6.0
@export var damage: float = 25.0
@export var radius: float = 150.0
@export var knockback: float = 340.0
@export var color: Color = Color(0.45, 0.85, 1.0)

@export_group("Geschosse")
@export var projectile_scene: PackedScene
@export var projectile_count: int = 10
@export var projectile_speed: float = 420.0
## Öffnungswinkel für FAN_SHOT.
@export var spread_degrees: float = 60.0

@export_group("Bewegung")
@export var blink_distance: float = 220.0
@export var dash_distance: float = 280.0

@export_group("Dauer & Sonstiges")
## Für SHIELD und TIME_SLOW.
@export var duration: float = 3.0
## TIME_SLOW: Gegnertempo wird damit multipliziert.
@export var slow_factor: float = 0.35
@export var heal_amount: float = 25.0
@export var chain_jumps: int = 5
@export var chain_range: float = 220.0
