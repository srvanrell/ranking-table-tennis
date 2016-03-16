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

    def get_total(self):
        return self.bonus + self.rating

    def __repr__(self):
        return ";".join([str(self.pid), str(self.get_total()), str(self.rating), str(self.bonus)])


class Ranking:
    def __init__(self, tournament_name="", date="", location=""):
        self.ranking = {}
        self.date = date
        self.tournament_name = tournament_name
        self.location = location

    def __iter__(self):
        return self.ranking.itervalues()

    def add_entry(self, entry):
        if entry.pid not in self.ranking:
            self.ranking[entry.pid] = RankingEntry(entry.pid, entry.rating, entry.bonus)
        else:
            print "WARNING: Already exists an entry for pid:", entry.pid

    def add_new_entry(self, pid):
        self.add_entry(RankingEntry(pid, 0, 0))

    def get_entry(self, pid):
        return self.ranking.get(pid)

    def __getitem__(self, pid):
        return self.get_entry(pid)

    def __repr__(self):
        aux = "%s (%s - %s)\n" % (self.tournament_name, self.location, self.date)
        return aux + "\n".join(str(self.get_entry(re)) for re in self.ranking)

    def load_list(self, ranking_list):
        for pid, rating, bonus in ranking_list:
            self.add_entry(RankingEntry(pid, rating, bonus))

    def to_list(self):
        ranking_list = [[p.pid, p.rating, p.bonus] for p in self]
        return ranking_list

    def compute_new_ratings(self, old_ranking, matches):
        """return assigned points per match
        (a list containing [winner_pid, loser_pid, points_to_winner, points_to_loser])"""
        # TODO make a better way to copy a ranking object
        for entry in old_ranking:
            self.add_entry(entry)

        # List of points assigned in each match.add_entry(
        assigned_points = []

        for winner_pid, loser_pid, unused, unused2 in matches:
            [to_winner, to_loser] = utils.points_to_assign(old_ranking[winner_pid].rating,
                                                           old_ranking[loser_pid].rating)
            self[winner_pid].rating += to_winner
            self[loser_pid].rating -= to_loser

            assigned_points.append([winner_pid, loser_pid, to_winner, -to_loser])

        return assigned_points

    def compute_bonus_points(self, matches):
        best_round = {}

        # FIXME maybe should not be read at utils and here instead
        round_priority = utils.rounds_priority

        for winner, loser, round_match, category in matches:
            # changing labels of finals round match
            if round_match == "final":
                winner_round_match = "primero"
                loser_round_match = "segundo"
            elif round_match == "tercer puesto":
                winner_round_match = "tercero"
                loser_round_match = "cuarto"
            else:
                winner_round_match = round_match
                loser_round_match = round_match

            # finding best round per category of each player
            for pid, played_round in [(winner, winner_round_match),
                                      (loser, loser_round_match)]:
                categpid = "%s-%d" % (category, pid)
                if best_round.get(categpid):
                    if round_priority[best_round.get(categpid)] < round_priority[played_round]:
                        best_round[categpid] = played_round
                else:
                    best_round[categpid] = played_round

        # List of points assigned in each match
        assigned_points = []
        for categpid in best_round:
            category = categpid.split("-")[0]
            pid = int(categpid.split("-")[1])
            # FIXME maybe should not be read at utils and here instead
            round_points = utils.round_points[category]
            self[pid].bonus += round_points[best_round[categpid]]
            assigned_points.append([pid, round_points[best_round[categpid]], best_round[categpid], category])
        return assigned_points

