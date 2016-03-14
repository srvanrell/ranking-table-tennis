# -*- coding: utf-8 -*-

import utils


class Player:
    def __init__(self, pid=-1, name="Apellido, Nombre", association="Asociación", city="Ciudad"):
        self.pid = pid
        self.name = name
        self.association = association
        self.city = city

    def __repr__(self):
        return ";".join([str(self.pid), self.name, self.association, self.city])


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
        else:
            print "WARNING: Already exists a player for that pid. Check:", str(player)
    
    def add_new_player(self, name):
        pid = 0
        while pid in self.players:
            pid += 1
        self.add_player(Player(pid, name))
    
    # def __contains__(self, ):

    def get_pid(self, name):
        for player in self.players.itervalues():
            if name == player.name:
                return player.pid
        print "WARNING: Unknown player:", name
        return None

    def to_list(self):
        players_list = [[p.pid, p.name, p.association, p.city] for p in self.players.itervalues()]
        return players_list

    def load_list(self, players_list):
        for pid, name, association, city in players_list:
            self.add_player(Player(pid, name, association, city))

    def __iter__(self):
        return self.players.itervalues()


class RankingEntry:
    def __init__(self, pid, rating, bonus):
        self.pid = pid
        self.rating = rating
        self.bonus = bonus
        
    def __repr__(self):
        return ";".join([str(self.pid), str(self.rating), str(self.bonus)])


class Ranking:
    def __init__(self, tournament_name="", date="", location=""):
        self.ranking = {}
        self.date = date
        self.tournament_name = tournament_name
        self.location = location

    def __iter__(self):
        return self.ranking.itervalues()

    # TODO change to Ranking entry instead of list of inputs
    def add_entry(self, pid, rating, bonus):
        if pid not in self.ranking:
            self.ranking[pid] = RankingEntry(pid, rating, bonus)
        else:
            print "WARNING: Already exists an entry for pid:", pid

    def add_new_entry(self, pid):
        self.add_entry(pid, 0, 0)

    def get_entry(self, pid):
        return self.ranking.get(pid)
        
    def __getitem__(self, pid):
        return self.get_entry(pid)

    def __repr__(self):
        aux = "%s (%s - %s)\n" % (self.tournament_name, self.location, self.date)
        return aux + "\n".join(str(self.get_entry(re)) for re in self.ranking)
        
    def load_list(self, ranking_list):
        for pid, rating in ranking_list:
            # TODO add bonus points support
            self.add_entry(pid, rating, 0) 
    
    def to_list(self):
        ranking_list = [[p.pid, p.rating, p.bonus] for p in self.ranking.itervalues()]
        return ranking_list

    def compute_new_ranking(self, old_ranking, matches):
        # TODO make a better way to copy a ranking object
        self.tournament_name.replace("old_", "")
        for entry in old_ranking:
            self.add_entry(entry.pid, entry.rating, entry.bonus)

        for winner_pid, loser_pid, unused in matches:
            [to_winner, to_loser] = utils.points_to_assign(old_ranking[winner_pid].rating,
                                                           old_ranking[loser_pid].rating)
            self[winner_pid].rating += to_winner
            self[loser_pid].rating -= to_loser

        # TODO create a log with matches points description
        # FIXME está sumando 3 de más en algunos casos, revisar como asigna los puntos bonus, fijar preferencia manual
        # TODO desacoplar puntos bonus de calculo de rating

        # TODO add points per best round reached
        best_round_to_assign = {}

        # FIXME maybe should not be read at utils and here instead
        round_points = utils.round_points

        for winner, loser, round_match in matches:
            if best_round_to_assign.get(winner):
                if best_round_to_assign.get(winner) < round_points[round_match]:
                    if round_match == "final":
                        best_round_to_assign[winner] = round_points["primero"]
                    elif round_match == "tercer puesto":
                        best_round_to_assign[winner] = round_points["tercero"]
                    else:
                        best_round_to_assign[winner] = round_points[round_match]
            else:
                if round_match == "final":
                    best_round_to_assign[winner] = round_points["primero"]
                elif round_match == "tercer puesto":
                    best_round_to_assign[winner] = round_points["tercero"]
                else:
                    best_round_to_assign[winner] = round_points[round_match]
            if best_round_to_assign.get(loser):
                if best_round_to_assign.get(loser) < round_points[round_match]:
                    if round_match == "final":
                        best_round_to_assign[loser] = round_points["segundo"]
                    elif round_match == "tercer puesto":
                        best_round_to_assign[loser] = round_points["cuarto"]
                    else:
                        best_round_to_assign[loser] = round_points[round_match]
            else:
                if round_match == "final":
                    best_round_to_assign[loser] = round_points["segundo"]
                elif round_match == "tercer puesto":
                    best_round_to_assign[loser] = round_points["cuarto"]
                else:
                    best_round_to_assign[loser] = round_points[round_match]

        for pid in best_round_to_assign:
            # TODO modified and change it to bonus
            self[pid].rating += best_round_to_assign[pid]


