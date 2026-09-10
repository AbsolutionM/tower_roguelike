extends Resource
class_name RoomData

@export var room_name: String = "Raum"

@export_group("Gegner")
@export var enemy_pool: Array[EnemyData] = []
## Gegner beim Betreten des Raums.
@export var enemy_count: int = 4


@export_group("Layout")
## Größe des Raums. Ist er größer als der Bildschirm, folgt die Kamera dem Spieler.
@export var room_size: Vector2 = Vector2(660.0, 1150.0)
@export var fixed_camera: bool = true
@export var spawn_margin: float = 70.0
@export var min_player_distance: float = 190.0
## 0 = Standarddauer aus dem GameManager benutzen.
@export var duration_override: float = 0.0

@export_group("Boss")
## Ist gesetzt, wird statt eines normalen Raums ein Bosskampf gestartet.
@export var boss_data: EnemyData
## Bosskämpfe laufen ohne Zeitdruck - der Raum endet erst mit dem Boss.
@export var disable_timer: bool = false

@export_group("Layout")
## Ist ein Satz gesetzt, wird ein festes Layout daraus gebaut statt
## Gegner und Felsen zufällig zu verteilen.
@export var layout_set: RoomLayoutSet

@export_group("Hindernisse")
## Blockierende Felsen im Raum - zwingen dazu, Wege zu suchen.
@export var obstacle_scene: PackedScene
@export var obstacle_count: int = 0

@export_group("Loot-Quellen")
@export var chest_scene: PackedScene
@export var chest_count: int = 0
@export var harvestable_scene: PackedScene
@export var harvestable_count: int = 0
