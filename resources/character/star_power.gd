extends Resource
class_name StarPowerData

## Freischaltung, die ein Held auf einer bestimmten Kraftstufe bekommt
## (Gadget auf Stufe 5, Sternenkraft auf Stufe 9) - wie in Brawl Stars.
##
## `stat_add` und `stat_mult` greifen direkt auf die Felder von PlayerStats zu,
## z.B. { "lifesteal": 0.06 } oder { "damage_mult": 1.15 }.

@export var star_id: String = ""
@export var star_name: String = "Sternenkraft"
@export_multiline var description: String = ""
@export var icon: Texture2D

@export var stat_add: Dictionary = {}
@export var stat_mult: Dictionary = {}
