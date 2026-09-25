extends Resource
class_name TowerData

@export var tower_id: String = ""
@export var tower_name: String = "Turm"
@export_multiline var description: String = ""
## Bild für den Start-Tab. Leer = prozedurales Turmbild.
@export var image: Texture2D
@export var accent_color: Color = Color(0.55, 0.75, 1.0)
## Grundbeleuchtung des Turms - dunkler = stimmungsvoller.
## Kachelsatz für Boden und Wände. Leer = gezeichnetes Platzhaltermuster.
@export var tileset: RoomTileset
@export var ambient_color: Color = Color(0.58, 0.57, 0.74)
@export var floors: int = 5
@export var rooms: Array[RoomData] = []
## Pro Raum wird zufällig eines dieser Wetter gezogen. Leer = immer klar.
@export var weather_options: Array[WeatherData] = []
## Erster Turm = offen. Jeder weitere öffnet sich, wenn der vorige bezwungen ist.
@export var unlocked: bool = true
## Schaden der Gegner in diesem Turm. Springt pro Turmstufe eine Schadensstufe
## (Isaac-Prinzip), statt mit jeder Etage ein bisschen zu steigen.
@export var damage_mult: float = 1.0

@export_group("Mini-Bosse")
## Nach je fünf Räumen kommt einer davon; jeder höchstens einmal pro Lauf.
@export var mini_bosses: Array[EnemyData] = []
## Raum, in dem die Mini-Bosse kämpfen (ohne Timer).
@export var mini_boss_room: RoomData
