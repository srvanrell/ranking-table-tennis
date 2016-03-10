# -*- coding: utf-8 -*-


class Player:
    def __init__(self, pid=-1, name="Apellido, Nombre", association="Asociación", city="Ciudad"):
        self.pid = pid
        self.name = name
        self.association = association
        self.city = city

    def __repr__(self):
        return ",".join([str(self.pid), self.name, self.association, self.city])


class PlayersList:
    def __init__(self):
        self.players = {}

    def __getitem__(self, pid):
        return self.get_player(pid)

    def get_player(self, pid):
        return self.players.get(pid)

    def __len__(self):
        return len(self.players)

    def __repr__(self):
        return "\n".join(str(self.get_player(p)) for p in self.players)

    def add_player(self, player):
        if player.pid not in self.players:
            self.players[player.pid] = player

    def get_pid(self, name):
        for player in self.players.itervalues():
            if name == player.name:
                return player.pid
        print "Jugador desconocido"
        return None

