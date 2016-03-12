import models
# -*- coding: utf-8 -*-

jugadores = models.PlayersList()
jugadores.add_player(models.Player(0, "Aliberti, Alberto", "Atem", "Andes"))
jugadores.add_player(models.Player(1, "Bethoven, Bartolomé", "Betem", "Buenos"))


print jugadores
print jugadores[0]
jugadores[0].name = "Arruabarrena, Alberto"
print jugadores[0]
#

ranking_inicial = models.Ranking()

print ranking_inicial