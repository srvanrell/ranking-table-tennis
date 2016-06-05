import os
import csv


def save_csv(filename, headers, list_to_save):
    """Save list into a csv file with given header."""
    with open(filename, 'w') as outcsv:
        writer = csv.writer(outcsv)
        writer.writerow(headers)
        writer.writerows(list_to_save)


def load_csv(filename, first_row=1):
    """Loads csv table into a list. By default first row is not read"""
    with open(filename, 'r') as incsv:
        reader = csv.reader(incsv)
        list_to_return = []
        for row in reader:
            aux_row = []
            for item in row:
                if item.isdigit():
                    aux_row.append(int(item))
                else:
                    aux_row.append(item)
            list_to_return.append(aux_row)
        return list_to_return[first_row:]

# Tables to assign points

config_folder = os.path.dirname(__file__) + "/config/"

# difference, points to winner, points to loser
expected_result_table = load_csv(config_folder + "expected_result.csv")

# negative difference, points to winner, points to loser
unexpected_result_table = load_csv(config_folder + "unexpected_result.csv")

# points to be assigned by round
raw_bonus_table = load_csv(config_folder + "puntos_por_ronda.csv", first_row=0)
categories = raw_bonus_table[0][2:]
bonus_rounds_points = {}
bonus_rounds_priority = {}
for i, categ in enumerate(categories):
    bonus_rounds_points[categ] = {}
    for bonus_row in raw_bonus_table[1:]:
        priority = bonus_row[0]
        reached_round = bonus_row[1]
        points = bonus_row[2 + i]
        bonus_rounds_points[categ][reached_round] = points
        bonus_rounds_priority[reached_round] = priority

# Points for being part of a tournament
participation_points = int(load_csv(config_folder + "puntos_por_participar.csv").pop().pop())


class Player:
    def __init__(self, pid=-1, name="Apellido, Nombre", association="Asociación", city="Ciudad", last_tournament=-1):
        self.pid = pid
        self.name = name
        self.association = association
        self.city = city
        self.last_tournament = last_tournament

    def __str__(self):
        return ";".join([str(self.pid), self.name, self.association, self.city, str(self.last_tournament)])


class PlayersList:
    def __init__(self):
        self.players = {}

    def __getitem__(self, pid):
        return self.get_player(pid)

    def __len__(self):
        return len(self.players)

    def __str__(self):
        return "\n".join(str(p) for p in self)

    def __iter__(self):
        return iter(self.players.values())

    def get_player(self, pid):
        return self.players.get(pid)

    def add_player(self, player):
        if player.pid not in self.players:
            self.players[player.pid] = player
        else:
            print("WARNING: Already exists a player for that pid. Check:", str(player))

    def add_new_player(self, name, association="", city="", last_tournament=-1):
        pid = 0
        while pid in self.players:
            pid += 1
        self.add_player(Player(pid, name, association, city, last_tournament))

    def get_pid(self, name):
        for player in self:
            if name == player.name:
                return player.pid
        print("WARNING: Unknown player:", name)
        return None

    def to_list(self):
        players_list = [[p.pid, p.name, p.association, p.city, p.last_tournament] for p in self]
        return players_list

    def load_list(self, players_list):
        for pid, name, association, city, last_tournament in players_list:
            self.add_player(Player(pid, name, association, city, last_tournament))


class RankingEntry:
    def __init__(self, pid, rating, bonus):
        self.pid = pid
        self.rating = rating
        self.bonus = bonus

    def get_total(self):
        return self.bonus + self.rating

    def __str__(self):
        return ";".join([str(self.pid), str(self.get_total()), str(self.rating), str(self.bonus)])


class Ranking:
    def __init__(self, tournament_name="", date="", location=""):
        self.ranking = {}
        self.date = date
        self.tournament_name = tournament_name
        self.location = location

    def __iter__(self):
        return iter(self.ranking.values())

    def add_entry(self, entry):
        if entry.pid not in self.ranking:
            self.ranking[entry.pid] = RankingEntry(entry.pid, entry.rating, entry.bonus)
        else:
            print("WARNING: Already exists an entry for pid:", entry.pid)

    def add_new_entry(self, pid, initial_rating=0, initial_bonus=0):
        self.add_entry(RankingEntry(pid, initial_rating, initial_bonus))

    def get_entry(self, pid):
        return self.ranking.get(pid)

    def __getitem__(self, pid):
        return self.get_entry(pid)

    def __str__(self):
        aux = "%s (%s - %s)\n" % (self.tournament_name, self.location, self.date)
        return aux + "\n".join(str(re) for re in self)

    def load_list(self, ranking_list):
        for pid, rating, bonus in ranking_list:
            self.add_entry(RankingEntry(pid, rating, bonus))

    def to_list(self):
        ranking_list = [[p.pid, p.rating, p.bonus] for p in self]
        return ranking_list

    @staticmethod
    def _points_to_assign(rating_winner, rating_loser):
        """Returns points to add to winner and to deduce from loser, given ratings of winner and loser."""
        rating_diff = rating_winner - rating_loser

        assignation_table = expected_result_table
        if rating_diff < 0:
            rating_diff *= -1.0
            assignation_table = unexpected_result_table

        j = 0
        while rating_diff > assignation_table[j][0]:
            j += 1

        points_to_winner = assignation_table[j][1]
        points_to_loser = assignation_table[j][2]

        return [points_to_winner, points_to_loser]

    def compute_new_ratings(self, old_ranking, matches):
        """return assigned points per match
        (a list containing [winner_pid, loser_pid, points_to_winner, points_to_loser])"""
        # TODO make a better way to copy a ranking object
        for entry in old_ranking:
            self.add_entry(entry)

        # List of points assigned in each match
        assigned_points = []

        for winner_pid, loser_pid, unused, unused2 in matches:
            # workaround to add extra bonus points from match list
            if winner_pid < 0:
                continue

            [to_winner, to_loser] = self._points_to_assign(old_ranking[winner_pid].rating,
                                                           old_ranking[loser_pid].rating)
            self[winner_pid].rating += to_winner
            self[loser_pid].rating -= to_loser
            self[loser_pid].rating = max(0, self[loser_pid].rating)

            assigned_points.append([winner_pid, loser_pid, to_winner, -to_loser])

        return assigned_points

    def compute_bonus_points(self, matches):
        best_round = {}

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
                # workaround to add extra bonus points from match list
                if pid < 0:
                    continue

                categpid = "%s-%d" % (category, pid)
                if best_round.get(categpid):
                    if bonus_rounds_priority[best_round.get(categpid)] < bonus_rounds_priority[played_round]:
                        best_round[categpid] = played_round
                else:
                    best_round[categpid] = played_round

        # List of points assigned in each match
        assigned_points = []
        for categpid in best_round:
            category = categpid.split("-")[0]
            pid = int(categpid.split("-")[1])
            round_points = bonus_rounds_points[category]
            self[pid].bonus += round_points[best_round[categpid]]
            assigned_points.append([pid, round_points[best_round[categpid]], best_round[categpid], category])
        return assigned_points

    def add_participation_points(self, pid_list):
        """Add bonus points for each participant given """
        assigned_points = []
        for pid in pid_list:
            self[pid].bonus += participation_points
            assigned_points.append([pid, participation_points])
        return assigned_points

    def bonus2rating(self):
        """For each entry, add bonus points to rating and then set bonus to zero."""
        for entry in self:
            entry.rating += entry.bonus
            entry.bonus = 0


class Match:
    def __init__(self, winner_name, loser_name, match_round, category):
        self.winner_name = winner_name
        self.loser_name = loser_name
        self.round = match_round
        self.category = category

    def __str__(self):
        return ";".join([self.winner_name, self.loser_name, self.round, self.category])


class Tournament:
    def __init__(self, name="", date="", location=""):
        self.name = name
        self.date = date
        self.location = location
        self.matches = []

    def get_players_names(self):
        players_set = set()
        for match in self.matches:
            # workaround to add extra bonus points from match list
            if not match.winner_name == "to_add_bonus_points":
                players_set.add(match.winner_name)
            players_set.add(match.loser_name)
        return sorted(list(players_set))

    def add_match(self, winner_name, loser_name, match_round, category):
        self.matches.append(Match(winner_name, loser_name, match_round, category))
