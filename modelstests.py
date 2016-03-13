import models
# -*- coding: utf-8 -*-

jugadores = models.PlayersList()
jugadores.add_player(models.Player(0, "Aliberti, Alberto", "Atem", "Andes"))
jugadores.add_player(models.Player(1, "Bethoven, Bartolomé", "Betem", "Buenos"))


print jugadores
print jugadores[0]
jugadores[0].name = "Arruabarrena, Alberto"
print jugadores[0]
jugadores.add_new_player(models.Player(-1, "Nada, Roberto", "Daecpu", "Montevideo"))
jugadores.add_player(models.Player(0, "Pacino, Al", "Godfather", "New York"))

players = models.PlayersList()
players.load_list(jugadores.to_list())

players[0].name = "Cage, Nicolas"

print jugadores
print players 

#

ranking_inicial = models.Ranking()
ranking_inicial.add_entry(0,500,0)
ranking_inicial.add_entry(0,500,0)

print ranking_inicial
