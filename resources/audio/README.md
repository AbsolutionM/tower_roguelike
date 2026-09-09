# Töne einlegen

Das Spiel ruft überall `Audio.play(Audio.ID_...)`. Welche Datei dabei klingt,
steht in `bank.tres` - im Code muss dafür nichts geändert werden.

## So fügst du einen Ton hinzu

1. Datei nach `assets/audio/<name>.ogg` (oder `.mp3`/`.wav`) legen.
2. `resources/audio/bank.tres` im Editor öffnen.
3. Beim passenden Eintrag unter `streams` die Datei eintragen.

Mehrere Dateien in einem Eintrag heißt: bei jedem Abspielen wird gewürfelt.
Das lohnt sich besonders bei `enemy_hit` und `swing`, weil die im Sekundentakt
kommen.

## Stellschrauben pro Eintrag

| Feld | Wofür |
|---|---|
| `volume_db` | Lautstärke. Treffer und Schüsse liegen bei -8, der Rest bei -4. |
| `pitch_min` / `pitch_max` | Tonhöhen-Streuung. 0.94 bis 1.06 klingt lebendig, ohne zu leiern. |
| `min_interval` | Kürzester Abstand zweier Wiedergaben. Verhindert Klangbrei bei Dauerfeuer. |

## Die 17 Plätze

| ID | Wann |
|---|---|
| `enemy_hit` | Jeder Treffer an einem Gegner *(belegt)* |
| `enemy_die` | Gegner stirbt |
| `player_hurt` | Der Held nimmt Schaden |
| `player_die` | Der Held fällt |
| `shoot` | Schuss aus einer Fernkampfwaffe |
| `swing` | Schlag mit einer Nahkampfwaffe |
| `dash` | Ausweichsprung |
| `ability` | Charakterfähigkeit |
| `special` | Sonderschlag der Waffe löst aus |
| `pickup` | Material aufgesammelt |
| `coin` | Gold aufgesammelt |
| `purchase` | Kauf im Shop |
| `forge` | Waffe geschmiedet |
| `level_up` | Held steigt eine Kraftstufe |
| `boss_spawn` | Boss betritt den Raum |
| `room_change` | Neuer Raum |
| `ui_tap` | Menüknopf *(noch nicht verdrahtet)* |

Fehlt ein Eintrag oder ist er leer, bleibt es an der Stelle einfach still -
das Spiel läuft auch mit halb gefüllter Bank.
