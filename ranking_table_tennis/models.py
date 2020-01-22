import os
import csv
import yaml
import ast
from unidecode import unidecode
import shutil
import pandas as pd


# Loads some names from config.yaml
user_config_path = os.path.expanduser("~") + "/.config/ranking_table_tennis"

if not os.path.exists(user_config_path):
    shutil.copytree(os.path.dirname(__file__) + "/config", user_config_path)

with open(user_config_path + "/config.yaml", 'r') as cfgyaml:
    try:
        cfg = yaml.safe_load(cfgyaml)
    except yaml.YAMLError as exc:
        print(exc)

if not os.path.exists(cfg["io"]["data_folder"]):
    os.mkdir(cfg["io"]["data_folder"])


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

# difference, points to winner, points to loser
expected_result_table = load_csv(user_config_path + "/expected_result.csv")

# negative difference, points to winner, points to loser
unexpected_result_table = load_csv(user_config_path + "/unexpected_result.csv")

# points to be assigned by round and by participation
raw_bonus_table = load_csv(user_config_path + "/points_per_round.csv", first_row=0)
raw_participation_points = load_csv(user_config_path + "/participation_points.csv")

categories = raw_bonus_table[0][2:]
bonus_rounds_points = {}
bonus_rounds_priority = {}
participation_points = {}
for i, categ in enumerate(categories):
    bonus_rounds_points[categ] = {}
    for bonus_row in raw_bonus_table[1:]:
        priority = bonus_row[0]
        reached_round = bonus_row[1]
        points = bonus_row[2 + i]
        bonus_rounds_points[categ][reached_round] = points
        bonus_rounds_priority[reached_round] = priority

    # Points for being part of a tournament
    participation_points[categ] = raw_participation_points[0][i]


class Player:
    def __init__(self, pid=-1, name="Apellido, Nombre", association="Asociación", city="Ciudad", last_tournament=-1,
                 history=None):
        if history is None:
            history = {}
        self.pid = pid
        self.name = unidecode(name).title()
        self.association = association
        self.city = city
        self.last_tournament = last_tournament
        self.history = history

    def __str__(self):
        formated_history = ["\tCategory %s - Tournament %s: %s" % (cat, tid, best_round)
                            for cat, tid, best_round in self.sorted_history]
        return ";".join([str(self.pid), self.name, self.association, self.city, str(self.last_tournament),
                         "\n".join([""] + formated_history)])

    def find_last_tournament(self):
        """ Update and return last tournament index based on player history.
        If history is not available will not update it.

        :return: last_tournament, zero-indexed
        """
        if self.history:
            self.last_tournament = max(self.played_tournaments())
        return self.last_tournament

    @property
    def n_tournaments(self):
        """ Number of played tournaments, regardless of categories. """
        return len(self.played_tournaments())

    def played_tournaments(self):
        """ Return sorted list of played tournaments. Empty history will result in an empty list. """
        if self.history:
            return sorted(set([tid for cat, tid in self.history.keys()]))
        return []

    @property
    def sorted_history(self):
        """ History sorted first by category and then by tournament_id.

        Returns a list which elements are [cat, tid, best_round]
        """
        return [[cat, tid, self.history[(cat, tid)]] for cat, tid in
                sorted(self.history.keys())]


class Players:
    def __init__(self, players_df=None, history_df=None):
        """
        Create a players database from given players DataFrame
        :param players_df: DataFrame with columns: pid, name, affiliation, city, last_tournament and history
        """
        self.players_df = pd.DataFrame(players_df,
                                       columns=["pid", "name", "affiliation", "city", "last_tournament", "history"])
        self.players_df.set_index("pid", drop=True, verify_integrity=True, inplace=True)

        # TODO add a history df to simplify writing and reading of history
        self.history_df = pd.DataFrame(history_df,
                                       columns=["tid", "pid", "category", "best_round", "last_tournament"])

        self.verify_and_normalize()

    def __len__(self):
        return len(self.players_df)

    def __str__(self):
        return str(self.players_df)

    def __getitem__(self, pid):
        return self.players_df.loc[pid]

    def verify_and_normalize(self):
        self.players_df.fillna("", inplace=True)

        # cols_to_upper = ["affiliation"]
        # self.players_df.loc[:, cols_to_upper] = self.players_df.loc[:, cols_to_upper].applymap(
        #     lambda cell: cell.strip().upper())

        cols_to_title = ["name", "city"]
        self.players_df.loc[:, cols_to_title] = self.players_df.loc[:, cols_to_title].applymap(
            lambda cell: unidecode(cell).strip().title())

    def get_pid(self, name):
        uname = unidecode(name).title()
        pid = self.players_df[self.players_df.name == uname].first_valid_index()
        if pid is None:
            print("WARNING: Unknown player:", uname)

        return pid

    def add_new_player(self, name, affiliation="", city="", last_tournament=-1):
        pid = self.players_df.index.max() + 1
        self.players_df.loc[pid] = {"name": name, "affiliation": affiliation, "city": city,
                                    "last_tournament": last_tournament, "history": "{}"}
        self.verify_and_normalize()

    def update_histories(self, tid, best_rounds):
        """ Save player's best rounds into their histories and update
        last_tournament.

        Each history is a string that can be read as a dict with (category, tournament_id) as key.
        """
        for category, pid in best_rounds.keys():
            history_dic = ast.literal_eval(self[pid].history)
            history_dic[(category, tid)] = best_rounds[(category, pid)]
            self.players_df.loc[pid, "history"] = str(history_dic)
            self.players_df.loc[pid, "last_tournament"] = tid


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
            uname = unidecode(name).title()
            if uname == player.name:
                return player.pid
        print("WARNING: Unknown player:", name)
        return None

    def to_list(self):
        players_list = [[p.pid, p.name, p.association, p.city, p.last_tournament, str(p.history)]
                        for p in self]
        return players_list

    def load_list(self, players_list):
        for pid, name, association, city, last_tournament, history_str in players_list:
            if history_str:
                history = ast.literal_eval(history_str)
            else:
                history = {}
            self.add_player(Player(int(pid), name, association, city, int(last_tournament), history))

    def update_histories(self, tid, best_rounds):
        """ Save player's best rounds into their histories and update
        last_tournament.

        Each history is a dict with (tournament_id, category) as key.
        """
        for category, pid in best_rounds.keys():
            self[pid].history[(category, tid)] = best_rounds[(category, pid)]
            self[pid].last_tournament = tid


class RankingEntry:
    def __init__(self, pid, rating, bonus, active=False, category=""):
        self.pid = pid
        self.rating = rating
        self.bonus = bonus
        self.category = category
        self.active = active

    def get_total(self):
        return self.bonus + self.rating

    def __str__(self):
        return ";".join([str(self.pid), str(self.rating), str(self.bonus),
                         self.category, str(self.active)])


class Ranking:
    def __init__(self, tournament_name="", date="", location="", tid=-1):
        self.ranking = {}
        self.date = date
        self.tournament_name = tournament_name
        self.location = location
        self.tid = tid

    def __iter__(self):
        return iter(self.ranking.values())

    def add_entry(self, entry):
        if entry.pid not in self.ranking:
            self.ranking[entry.pid] = RankingEntry(entry.pid, entry.rating, entry.bonus, entry.active, entry.category)
        else:
            print("WARNING: Already exists an entry for pid:", entry.pid)

    def add_new_entry(self, pid, initial_rating=0, initial_bonus=0, active=False, initial_category=""):
        self.add_entry(RankingEntry(pid, initial_rating, initial_bonus, active, initial_category))

    def get_entry(self, pid):
        return self.ranking.get(pid)

    def __getitem__(self, pid):
        return self.get_entry(pid)

    def __str__(self):
        aux = "%s (%s - %s)\n" % (self.tournament_name, self.location, self.date)
        return aux + "\n".join(str(re) for re in self)

    def load_list(self, ranking_list):
        for pid, rating, bonus, active, category in ranking_list:
            self.add_entry(RankingEntry(int(pid), int(rating), int(bonus), bool(active), str(category)))

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

    @staticmethod
    def _get_factor(rating_winner, rating_loser, category_winner, category_loser, not_own_category):
        """Returns factor for rating computation. It considers given winner and loser category.
        Players must play their own category """
        rating_diff = rating_winner - rating_loser
        category_factor = 1.0
        if category_winner != category_loser and not not_own_category:
            category_factor = cfg["aux"]["category expected factor"]
            if rating_diff < 0:
                category_factor = cfg["aux"]["category unexpected factor"]

        factor = cfg["aux"]["rating factor"] * category_factor

        return factor

    def compute_new_ratings(self, old_ranking, matches, pid_not_own_category):
        """return assigned points per match
        (a list containing [winner_pid, loser_pid, points_to_winner, points_to_loser])"""
        # TODO make a better way to copy a ranking object
        for entry in old_ranking:
            self.add_entry(entry)

        # List of points assigned in each match
        assigned_points = []

        for winner_pid, loser_pid, match_round, match_category in matches:
            [to_winner, to_loser] = self._points_to_assign(old_ranking[winner_pid].rating,
                                                           old_ranking[loser_pid].rating)
            factor = self._get_factor(old_ranking[winner_pid].rating, old_ranking[loser_pid].rating,
                                      old_ranking[winner_pid].category, old_ranking[loser_pid].category,
                                      winner_pid in pid_not_own_category or loser_pid in pid_not_own_category)
            to_winner = factor*to_winner
            to_loser = min(self[loser_pid].rating, factor*to_loser)
            self[winner_pid].rating += to_winner
            self[loser_pid].rating -= to_loser

            assigned_points.append([winner_pid, loser_pid, to_winner, -to_loser, match_round, match_category])

        return assigned_points

    def compute_bonus_points(self, best_rounds):
        # List of points assigned in each match
        assigned_points = []
        for category, pid in best_rounds.keys():
            categpid = (category, pid)
            round_points = bonus_rounds_points[category]
            self[pid].bonus += round_points[best_rounds[categpid]]
            assigned_points.append([pid, round_points[best_rounds[categpid]], best_rounds[categpid], category])
        return sorted(assigned_points, key=lambda l: (l[-1], l[1], l[0]), reverse=True)

    def add_participation_points(self, pid_list):
        """Add bonus points for each participant given """
        assigned_points = []
        for pid in pid_list:
            self[pid].bonus += participation_points[self[pid].category]
            assigned_points.append([pid, participation_points[self[pid].category]])
        return assigned_points

    def bonus2rating(self):
        """For each entry, add bonus points to rating and then set bonus to zero."""
        for entry in self:
            entry.rating += entry.bonus
            entry.bonus = 0

    def update_active_players(self, players, initial_active_players):
        # Avoid activate or inactivate players after the first tournament.
        activate_window = cfg["aux"]["tournament window to activate"]
        tourns_to_activate = cfg["aux"]["tournaments to activate"]
        inactivate_window = cfg["aux"]["tournament window to inactivate"]

        for re in self:
            if not re.active:
                last_tourns = [tid for tid in players[re.pid].played_tournaments()
                               if self.tid >= tid > self.tid - activate_window]
                # activate if he has played at least tourns_to_activate tournaments
                active = len(last_tourns) >= tourns_to_activate
            else:
                last_tourns = [tid for tid in players[re.pid].played_tournaments()
                               if self.tid >= tid > self.tid - inactivate_window]
                # don't inactivate during tournaments window if it is an initial active player
                if self.tid < inactivate_window and re.pid in initial_active_players:
                    active = True
                else:
                    active = len(last_tourns) > 0

            self[re.pid].active = active

    def update_categories(self, n_first=10, n_second=10):
        """ Players are ranked based on rating and their active state.
        # WARNING: if sometime is used with more categories it should be modified

        Players are ordered by rating. Active players are sorted first.

        Active players are ranked like this (n_first=12, n_second=16):
        - 1:12    -> first category
        - 13:28   -> second category
        - 29:last -> third category

        Inactive players are ranked based on active players categories
        """
        actives_to_order = [[e.pid, e.rating, e.active, e.category] for e in self if e.active and
                            not e.category == categories[-1]]
        inactives_to_order = [[e.pid, e.rating, e.active, e.category] for e in self if not e.active and
                              not e.category == categories[-1]]

        ordered_actives = sorted(actives_to_order, key=lambda k: (k[2], k[1]), reverse=True)  # to use active player
        ordered_inactives = sorted(inactives_to_order, key=lambda k: (k[2], k[1]), reverse=True)  # to use active player

        # First and last player indexes by category
        # TODO if sometimes is used with more categories it should be modified
        first = [0, n_first, n_first+n_second]
        last = [n_first-1, n_first+n_second-1, len(ordered_actives)-1]

        for cat, f, l in zip(categories[:3], first, last):
            for pid, rating, active, category in ordered_actives[f:l+1]:
                self[pid].category = cat

        for pid, rating, active, category in ordered_inactives:
            # By defaut it is assigned to first category. It will be downgraded if necessary
            self[pid].category = categories[0]

            for cat, f, l in zip(categories[:3], first, last):
                if rating <= self[ordered_actives[f][0]].rating:
                    self[pid].category = cat

    def update_categories_thresholds(self):
        """ Players are ranked based on rating and given thresholds.

        Players are ordered by rating and then assigned to a category

        Example:
        - rating >= 500        -> first category
        - 500 > rating >= 250  -> second category
        - 250 > rating         -> third category
        """
        thresholds = cfg["aux"]["categories thresholds"]
        players_to_order = [[e.pid, e.rating, e.active, e.category] for e in self
                            if not e.category == categories[-1]]
        ordered_players = sorted(players_to_order, key=lambda k: (k[2], k[1]), reverse=True)

        for pid, rating, active, category in ordered_players:
            self[pid].category = categories[-2]  # Last category that it's not fan
            for j, th in enumerate(thresholds):
                if rating >= th:
                    self[pid].category = categories[j]
                    break

    def get_pids(self, category='', status='all'):
        """
        Return a list of pids that may be filtered by category

        If no parameter is given, it won't filter the list
        :param category: It should be a known category
        :param status: valid options are 'all' (default), 'active' or 'inactive'
        :return:
        """
        pids = [p.pid for p in self if (not category or p.category == category)]
        if status == 'active':
            pids = [p.pid for p in self if (not category or p.category == category) and p.active]
        elif status == 'inactive':
            pids = [p.pid for p in self if (not category or p.category == category) and not p.active]

        return pids

    def get_statistics(self):
        """
        Return a dictionary of dictionaries that summarizes the number of players
        by active status and category
        :return:
        """
        statistics = {}
        for status in ['all', 'active', 'inactive']:
            statistics_aux = {cat: len(self.get_pids(cat, status)) for cat in categories}
            statistics_aux['total'] = len(self.get_pids(status=status))
            statistics[status] = statistics_aux
        return statistics


class Match:
    def __init__(self, winner_name, loser_name, match_round, category):
        winner_name = winner_name.strip()
        loser_name = loser_name.strip()
        match_round = match_round.strip().lower()
        category = category.strip().lower()
        self.winner_name = unidecode(winner_name).title()
        self.loser_name = unidecode(loser_name).title()
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

    def add_match(self, winner_name, loser_name, match_round, category):
        self.matches.append(Match(winner_name, loser_name, match_round, category))

    def get_players_names(self, category=''):
        """
        Return a sorted list of players that played the tournament

        If category is given, the list of players is filtered by category
        """
        players_set = set()
        for match in self.matches:
            if not category or category == match.category:
                # workaround to add extra bonus points from match list
                possible_flag = match.winner_name.lower()
                if possible_flag not in [cfg["aux"]["flag bonus sanction"], cfg["aux"]["flag add bonus"],
                                         cfg["aux"]["flag promotion"]]:
                    players_set.add(match.winner_name)
                    players_set.add(match.loser_name)
        return sorted(list(players_set))

    def get_statistics(self):
        """
        Return a dictionary with the number of players by category.

        Category names and 'total' are the keys
        :return:
        """
        statistics = {cat: len(self.get_players_names(cat)) for cat in categories}
        statistics['total'] = len(self.get_players_names())
        return statistics

    def compute_best_rounds(self):
        """
        Return a dictionary with the best round for each player and category

        The keys of the dictionary are tuples like: (category, player_name)

        To get a value use: best_rounds[(category, player_name)]
        """
        best_rounds = {}

        for match in self.matches:
            # changing labels of finals round match
            if match.round == cfg["roundnames"]["final"]:
                winner_round_match = cfg["roundnames"]["champion"]
                loser_round_match = cfg["roundnames"]["second"]
            elif match.round == cfg["roundnames"]["third place playoff"]:
                winner_round_match = cfg["roundnames"]["third"]
                loser_round_match = cfg["roundnames"]["fourth"]
            else:
                winner_round_match = match.round
                loser_round_match = match.round

            # workaround to avoid promotion entries being considered as matches
            possible_flag = match.winner_name.lower()
            if possible_flag == cfg["aux"]["flag promotion"]:
                continue

            # finding best round per category of each player
            for name, played_round in [(match.winner_name, winner_round_match),
                                       (match.loser_name, loser_round_match)]:
                # workaround to add extra bonus points from match list
                possible_flag = name.lower()
                if possible_flag == cfg["aux"]["flag add bonus"] or possible_flag == cfg["aux"]["flag bonus sanction"]:
                    continue

                catname = (match.category, name)
                if best_rounds.get(catname):
                    if bonus_rounds_priority[best_rounds.get(catname)] < bonus_rounds_priority[played_round]:
                        best_rounds[catname] = played_round
                else:
                    best_rounds[catname] = played_round

        return best_rounds


class Tournaments:
    def __init__(self, tournaments_df=None):
        """
        Create a tournaments database from given tournaments DataFrame.
        Verification and normalization is performed on loading.

        There are workarounds available to promote, sanction, or provide championship points

        :param tournaments_df: DataFrame with columns: tournament_name, date, location,
               player_a, player_b, sets_a, sets_b, round, category
        """
        self.tournaments_df = pd.DataFrame(tournaments_df,
                                           columns=["tid", "sheet_name", "tournament_name", "date", "location",
                                                    "player_a", "player_b", "sets_a", "sets_b", "round", "category"])
        self.tournaments_df.insert(4, "year", None)
        self.tournaments_df.insert(len(self.tournaments_df.columns), "winner", None)
        self.tournaments_df.insert(len(self.tournaments_df.columns), "winner_round", None)
        self.tournaments_df.insert(len(self.tournaments_df.columns), "loser", None)
        self.tournaments_df.insert(len(self.tournaments_df.columns), "loser_round", None)
        self.tournaments_df.insert(len(self.tournaments_df.columns), "promote", False)
        self.tournaments_df.insert(len(self.tournaments_df.columns), "sanction", False)
        self.tournaments_df.insert(len(self.tournaments_df.columns), "bonus", False)

        self.verify_and_normalize()

    def __len__(self):
        return len(self.tournaments_df)

    def __str__(self):
        return str(self.tournaments_df)

    def __iter__(self):
        grouped = self.tournaments_df.groupby("tid").groups.keys()
        return iter(grouped)

    @staticmethod
    def _process_match(match_row):
        # workaround to add extra bonus points from match list
        match_row["winner"] = match_row["player_b"]
        match_row["loser"] = match_row["player_b"]
        if match_row["sets_a"] >= 10 and match_row["sets_b"] >= 10:
            match_row["promote"] = True
        elif match_row["sets_a"] <= -10 and match_row["sets_b"] <= -10:
            match_row["sanction"] = True
        elif match_row["sets_a"] < 0 and match_row["sets_b"] < 0:
            match_row["bonus"] = True
        elif match_row["sets_a"] > match_row["sets_b"]:
            match_row["winner"] = match_row["player_a"]
            match_row["loser"] = match_row["player_b"]
        elif match_row["sets_a"] < match_row["sets_b"]:
            match_row["winner"] = match_row["player_b"]
            match_row["loser"] = match_row["player_a"]
        else:
            print("Failed to process matches, a tie was found at:\n", match_row)
            raise ImportError

        # changing labels of finals round match
        if match_row["round"] == cfg["roundnames"]["final"]:
            match_row["winner_round"] = cfg["roundnames"]["champion"]
            match_row["loser_round"] = cfg["roundnames"]["second"]
        elif match_row["round"] == cfg["roundnames"]["third place playoff"]:
            match_row["winner_round"] = cfg["roundnames"]["third"]
            match_row["loser_round"] = cfg["roundnames"]["fourth"]
        else:
            match_row["winner_round"] = match_row["round"]
            match_row["loser_round"] = match_row["round"]

        return match_row

    def _assign_tid(self):
        def tid_str(grp):
            dates_ordered = sorted(grp["date"].unique())
            numbered = {pd.Timestamp(date): num for num, date in enumerate(dates_ordered, 1)}
            tids = grp["date"].transform(lambda row: "S%sT%02d" % (row.year, numbered[row]))

            return tids
        # TODO verify, groupby gives an unexpected result and need to be transposed
        tid = self.tournaments_df.groupby("year", as_index=False, group_keys=False).apply(tid_str)
        self.tournaments_df["tid"] = tid.transpose()

    def verify_and_normalize(self):
        cols_to_lower = ["round", "category"]
        self.tournaments_df.loc[:, cols_to_lower] = self.tournaments_df.loc[:, cols_to_lower].applymap(
            lambda cell: cell.strip().lower())

        cols_to_title = ["tournament_name", "date", "location", "player_a", "player_b"]
        self.tournaments_df.loc[:, cols_to_title] = self.tournaments_df.loc[:, cols_to_title].applymap(
            lambda cell: unidecode(cell).strip().title())

        self.tournaments_df = self.tournaments_df.astype({"round": "category", "category": "category",
                                                          "location": "category", "tournament_name": "category"})

        self.tournaments_df.date = pd.to_datetime(self.tournaments_df.date)
        self.tournaments_df["year"] = self.tournaments_df.apply(lambda row: row["date"].year, axis="columns")
        self._assign_tid()
        self.tournaments_df = self.tournaments_df.apply(self._process_match, axis="columns")

    def get_players_names(self, tid, category=''):
        """
        Return a sorted list of players that played the tournament

        If category is given, the list of players is filtered by category
        """
        criteria = self.tournaments_df.tid == tid
        if category:
            criteria = criteria & (self.tournaments_df.category == category)

        winner = self.tournaments_df.loc[criteria, "winner"]
        loser = self.tournaments_df.loc[criteria, "loser"]
        all_players = winner.append(loser, ignore_index=True).unique()

        return sorted(list(all_players))

    def compute_best_rounds(self, tid):
        """
        Return a dictionary with the best round for each player and category

        The keys of the dictionary are tuples like: (category, player_name)

        To get a value use: best_rounds[(category, player_name)]
        """
        best_rounds = {}

        for match_id, match_row in self.tournaments_df[self.tournaments_df.tid == tid].iterrows():
            # workaround to avoid promotion entries being considered as matches
            if match_row.promote:
                continue

            # finding best round per category of each player
            for name, played_round in [(match_row.winner, match_row.winner_round),
                                       (match_row.loser, match_row.loser_round)]:

                catname = (match_row.category, name)
                if best_rounds.get(catname):
                    if bonus_rounds_priority[best_rounds.get(catname)] < bonus_rounds_priority[played_round]:
                        best_rounds[catname] = played_round
                else:
                    best_rounds[catname] = played_round

        return best_rounds
