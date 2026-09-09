extends Resource
class_name TowerData

@export var tower_id: String = ""
@export var tower_name: String = "Turm"
@export_multiline var description: String = ""
## Bild für den Start-Tab. Leer = prozedurales Turmbild.
@export var image: Texture2D
@export var accent_color: Color = Color(0.55, 0.75, 1.0)
## Grundbeleuchtung des Turms - dunkler = stimmungsvoller.
@export var ambient_color: Color = Color(0.42, 0.4, 0.58)
@export var floors: int = 5
@export var rooms: Array[RoomData] = []
## Pro Raum wird zufällig eines dieser Wetter gezogen. Leer = immer klar.
@export var weather_options: Array[WeatherData] = []
@export var unlocked: bool = true
