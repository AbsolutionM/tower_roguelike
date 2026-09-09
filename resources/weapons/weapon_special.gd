extends Resource
class_name WeaponSpecial

## Der Sonderschlag einer Waffe. Er laedt sich mit jedem Treffer auf und
## loest von selbst aus, sobald `hits_required` erreicht ist.
##
## Jede Waffenklasse hat einen Standard-Sonderschlag. Einzelne Waffen koennen
## stattdessen einen eigenen bekommen - dafuer einfach eine andere Resource
## in `WeaponData.special` haengen.

enum Kind {
	SHOCKWAVE,      ## Druckwelle rundum, wirft alles weg
	CLEAVE,         ## Weiter Rundumschlag mit hohem Schaden
	BLEED_BURST,    ## Alle Gegner in Reichweite bluten sofort aus
	PIERCE_SHOT,    ## Ein grosser Schuss, der alles durchschlaegt
	SPREAD_BURST,   ## Faecher aus Geschossen nach vorn
	VOLLEY,         ## Geschosse rundum in alle Richtungen
	CHAIN_BOLT,     ## Blitz, der von Gegner zu Gegner springt
	LIFE_STRIKE,    ## Treffer heilt den Traeger
	FROST_NOVA,     ## Bremst alle Gegner im Umkreis
	METEOR          ## Einschlag auf das aktuelle Ziel
}

@export var special_id: String = ""
@export var special_name: String = "Sonderschlag"
@export_multiline var description: String = ""
@export var kind: Kind = Kind.SHOCKWAVE

## So viele Treffer laden den Sonderschlag auf.
@export_range(1, 60) var hits_required: int = 8
## Schaden als Vielfaches des normalen Waffenschadens.
@export var damage_mult: float = 2.0
@export var radius: float = 150.0
@export var knockback: float = 320.0
## Anzahl Geschosse bzw. Sprunge, je nach Art.
@export var count: int = 8
## Dauer der Wirkung, wo eine gebraucht wird (Frost, Blutung).
@export var duration: float = 2.0
@export var color: Color = Color(0.949, 0.694, 0.204, 1.0)

func describe() -> String:
	if not description.is_empty():
		return description
	return "Loest nach %d Treffern aus." % hits_required
