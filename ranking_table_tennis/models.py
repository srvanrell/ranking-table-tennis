import os
from typing import List, Tuple, Dict, Iterator

import yaml
from unidecode import unidecode
import shutil
import pandas as pd


# Loads some names from config.yaml
user_config_path = os.path.join("data_rtt", "config")

if not os.path.exists(user_config_path):
    shutil.copytree(os.path.dirname(__file__) + "/config", user_config_path)

with open(user_config_path + "/config.yaml", 'r') as cfgyaml:
    try:
        cfg = yaml.safe_load(cfgyaml)
    except yaml.YAMLError as exc:
        print(exc)

if not os.path.exists(cfg["io"]["data_folder"]):
    os.mkdir(cfg["io"]["data_folder"])

# Tables to assign points

# difference, points to winner, points to loser
expected_result_table = pd.read_csv(user_config_path + "/expected_result.csv").to_numpy()

# negative difference, points to winner, points to loser
unexpected_result_table = pd.read_csv(user_config_path + "/unexpected_result.csv").to_numpy()

# points to be assigned by round and by participation
raw_points_per_round_table = pd.read_csv(user_config_path + "/points_per_round.csv")
best_rounds_priority = raw_points_per_round_table.loc[:, ["priority", "round_reached"]].set_index("round_reached")
best_rounds_priority = best_rounds_priority.squeeze()
best_rounds_points = raw_points_per_round_table.drop(columns="priority").set_index("round_reached")
categories = list(best_rounds_points.columns)


class Players:
    def __init__(self, players_df: pd.DataFrame = None, history_df: pd.DataFrame = None) -> None:
        """
        Create a players database from given players DataFrame
        :param players_df: DataFrame with columns: pid, name, affiliation, city, and history
        """
        self.players_df = pd.DataFrame(players_df, columns=["pid", "name", "affiliation", "city"])
        self.players_df.set_index("pid", drop=True, verify_integrity=True, inplace=True)

        self.history_df = pd.DataFrame(history_df, columns=["tid", "pid", "category", "best_round"])

        self.verify_and_normalize()

    def __len__(self) -> int:
        return len(self.players_df)

    def __str__(self) -> str:
        return str(self.players_df)

    def __getitem__(self, pid: int) -> pd.Series:
        return self.players_df.loc[pid]

    def verify_and_normalize(self) -> None:
        duplicated = self.players_df.index.duplicated(keep=False)
        if duplicated.any():
            print("Players entries duplicated")
            print(self.players_df[duplicated])

        self.players_df.fillna("", inplace=True)

        # cols_to_upper = ["affiliation"]
        # self.players_df.loc[:, cols_to_upper] = self.players_df.loc[:, cols_to_upper].applymap(
        #     lambda cell: cell.strip().upper())

        cols_to_title = ["name", "city"]
        self.players_df.loc[:, cols_to_title] = self.players_df.loc[:, cols_to_title].applymap(
            lambda cell: unidecode(cell).strip().title())

    def get_pid(self, name: str) -> int:
        uname = unidecode(name).title()
        pid = self.players_df[self.players_df.name == uname].first_valid_index()
        if pid is None:
            print("WARNING: Unknown player:", uname)

        return pid

    def get_name2pid(self) -> pd.Series:
        name2pid = self.players_df.loc[:, 'name'].copy()
        name2pid = name2pid.reset_index()
        name2pid.set_index("name", inplace=True)

        return name2pid.loc[:, "pid"]

    def add_player(self, player: pd.Series) -> None:
        self.players_df = self.players_df.append(player)
        self.verify_and_normalize()

    def add_new_player(self, name: str, affiliation: str = "", city: str = "") -> None:
        pid = self.players_df.index.max() + 1
        self.players_df.loc[pid] = {"name": name, "affiliation": affiliation, "city": city}
        self.verify_and_normalize()

    def update_histories(self, tid: str, best_rounds: pd.DataFrame) -> None:
        """ Save player's best rounds into their histories.

        Each history is a string that can be read as a dict with (category, tournament_id) as key.
        """
        to_update = [{"tid": tid, "pid": row.pid, "category": row.category, "best_round": row.best_round}
                     for row_id, row in best_rounds.iterrows()]
        self.history_df = self.history_df.append(to_update, ignore_index=True)

    def played_tournaments(self, pid: int) -> List[str]:
        """ Return sorted list of played tournaments. Empty history will result in an empty list. """
        tids = self.history_df.loc[self.history_df.pid == float(pid), "tid"]
        if not tids.empty:
            return sorted(set(tids))
        return []


class Rankings:
    def __init__(self, ranking_df: pd.DataFrame = None) -> None:
        all_columns = ["tid", "tournament_name", "date", "location", "pid", "rating", "category", "active"]
        all_columns += self.points_cat_columns() + self.cum_points_cat_columns() + self.participations_cat_columns()
        all_columns += self.cum_tids_cat_columns()
        self.ranking_df = pd.DataFrame(ranking_df, columns=all_columns)
        self.rating_details_df = pd.DataFrame()
        self.championship_details_df = pd.DataFrame()
        self.verify_and_normalize()

    def __len__(self) -> int:
        return len(self.ranking_df)

    def __str__(self) -> str:
        return str(self.ranking_df)

    def __getitem__(self, tidpidcol):
        if isinstance(tidpidcol, str):
            return self.get_entries(tidpidcol)
        else:
            return self.get_entries(*tidpidcol)

    def __setitem__(self, tidpidcol: Tuple[str, int, str], value):
        tid, pid, col = tidpidcol
        entries_indexes = (self.ranking_df.tid == tid) & (self.ranking_df.pid == pid)
        self.ranking_df.loc[entries_indexes, col] = value
        self.verify_and_normalize()

    @staticmethod
    def points_cat_columns() -> List[str]:
        return ["points_cat_%d" % d for d, _ in enumerate(categories, 1)]

    @staticmethod
    def cum_points_cat_columns() -> List[str]:
        return ["cum_points_cat_%d" % d for d, _ in enumerate(categories, 1)]

    @staticmethod
    def cum_tids_cat_columns() -> List[str]:
        return ["cum_tids_cat_%d" % d for d, _ in enumerate(categories, 1)]

    @staticmethod
    def participations_cat_columns() -> List[str]:
        return ["participations_cat_%d" % d for d, _ in enumerate(categories, 1)]

    def get_entries(self, tid: str, pid: int = None, col: str = None):
        entries_indexes = self.ranking_df.tid == tid

        if pid:
            pid_indexes = self.ranking_df.pid == pid
            entries_indexes = entries_indexes & pid_indexes
            if not col and entries_indexes.any():
                return self.ranking_df.loc[entries_indexes].iloc[0]

        if col:
            at_index = self.ranking_df.loc[entries_indexes].first_valid_index()
            return self.ranking_df.at[at_index, col]

        if entries_indexes.any():
            return self.ranking_df.loc[entries_indexes]

    def add_entry(self, ranking_entry: pd.Series) -> None:
        self.ranking_df = self.ranking_df.append(ranking_entry)
        self.verify_and_normalize()

    def add_new_entry(self, tid: str, pid: int, initial_rating: float = -1000, active: bool = False,
                      initial_category: str = "") -> None:
        self.ranking_df = self.ranking_df.append({"tid": tid, "pid": pid,  "rating": initial_rating, "active": active,
                                                  "category": initial_category}, ignore_index=True)
        self.verify_and_normalize()
        self.update_categories()

    def verify_and_normalize(self) -> None:
        duplicated = self.ranking_df.duplicated(["tid", "pid"], keep=False)
        if duplicated.any():
            print("Ranking entries duplicated")
            print(self.ranking_df[duplicated])

        default_rating = -1000
        default_active = False
        default_category = ""
        default_cat_value = 0
        default_cum_tid_value = ""

        cat_columns = self.points_cat_columns() + self.cum_points_cat_columns() + self.participations_cat_columns()
        cum_tid_values = {cum_tid_col: default_cum_tid_value for cum_tid_col in self.cum_tids_cat_columns()}
        cat_col_values = {cat_col: default_cat_value for cat_col in cat_columns}
        default_values = {"rating": default_rating, "category": default_category, "active": default_active,
                          "tournament_name": cfg["default"]["tournament_name"], "date": cfg["default"]["date"],
                          "location": cfg["default"]["location"],
                          **cat_col_values, **cum_tid_values}
        self.ranking_df.fillna(value=default_values, inplace=True)
        self.ranking_df.date = pd.to_datetime(self.ranking_df.date)

    def initialize_new_ranking(self, new_tid: str, prev_tid: str) -> None:
        entries_indexes = self.ranking_df.tid == prev_tid
        new_ranking = self.ranking_df.loc[entries_indexes].copy()
        new_ranking.loc[:, "tid"] = new_tid
        new_ranking.loc[:, self.points_cat_columns() + self.cum_points_cat_columns()] = 0
        new_ranking.loc[:, self.participations_cat_columns()] = 0
        new_ranking.loc[:, self.cum_tids_cat_columns()] = ""
        self.ranking_df = self.ranking_df.append(new_ranking, ignore_index=True)

    @staticmethod
    def _rating_to_category(rating: float) -> str:
        thresholds = cfg["aux"]["categories thresholds"]
        category = categories[-2]  # Last category that it's not fan
        for j, th in enumerate(thresholds):
            if rating >= th:
                category = categories[j]
                break
        return category

    def update_categories(self) -> None:
        """ Players are ranked based on rating and given thresholds.

        Players are ordered by rating and then assigned to a category

        Example:
        - rating >= 500        -> first category
        - 500 > rating >= 250  -> second category
        - 250 > rating         -> third category
        """
        # FIXME it is not working for players of the fan category
        self.ranking_df.loc[:, "category"] = self.ranking_df.loc[:, "rating"].apply(self._rating_to_category)

    @staticmethod
    def _points_to_assign(rating_winner: float, rating_loser: float) -> Tuple[float, float]:
        """Returns points to add to winner and to deduce from loser, given ratings of winner and loser."""
        rating_diff = rating_winner - rating_loser

        assignation_table = expected_result_table
        if rating_diff < 0:
            rating_diff *= -1.0
            assignation_table = unexpected_result_table

        # Select first row that is appropiate for given rating_diff
        diff_threshold, points_to_winner, points_to_loser = assignation_table[assignation_table[:, 0] > rating_diff][0]

        return points_to_winner, points_to_loser

    @staticmethod
    def _get_factor(rating_winner: float, rating_loser: float, category_winner: str, category_loser: str,
                    not_own_category: bool) -> float:
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

    def _new_ratings_from_match(self, match):
        [to_winner, to_loser] = self._points_to_assign(match["winner_rating"], match["loser_rating"])
        factor = self._get_factor(match["winner_rating"], match["loser_rating"],
                                  match["winner_category"], match["loser_category"],
                                  match["not_own_category"])

        to_winner, to_loser = factor * to_winner, factor * to_loser
        match["rating_to_winner"], match["rating_to_loser"], match["factor"] = to_winner, -to_loser, factor

        return match

    def compute_new_ratings(self, new_tid: str, old_tid: str, tournaments: "Tournaments",
                            pid_not_own_category: List[int]):
        """Compute ratings(new_tid) based on matches(new_tid) and ratings(old_tid).
        Details of rating changes per match are stored in rating_details_df.
        """
        new_tid_indexes = self.ranking_df.tid == new_tid
        old_tid_indexes = self.ranking_df.tid == old_tid

        # Get tid matches data from tournaments
        matches = tournaments.get_matches(new_tid).copy()
        matches.insert(len(matches.columns), "rating_to_winner", None)
        matches.insert(len(matches.columns), "rating_to_loser", None)

        # Assign ranking data to matches, such as category and rating of players
        ranking_data = self.ranking_df.loc[old_tid_indexes, ["pid", "category", "rating"]].copy()
        winner_data = ranking_data.rename(columns={"category": "winner_category", "rating": "winner_rating"})
        loser_data = ranking_data.rename(columns={"category": "loser_category", "rating": "loser_rating"})
        matches = self.merge_preserve_left_index(matches, winner_data, left_on="winner_pid", right_on="pid").drop(
            columns="pid")
        matches = self.merge_preserve_left_index(matches, loser_data, left_on="loser_pid", right_on="pid").drop(
            columns="pid")
        matches["not_own_category"] = matches.loc[:, ["winner_pid", "loser_pid"]].isin(pid_not_own_category).any(axis=1)

        # Compute ratings changes per match
        matches_processed = matches.apply(self._new_ratings_from_match, axis="columns")

        # Compute overall rating changes per player
        translations = {"rating_to_winner": "rating_change", "rating_to_loser": "rating_change",
                        "winner_pid": "pid", "loser_pid": "pid"}
        winner_changes = matches_processed.loc[:, ["winner_pid", "rating_to_winner"]].rename(columns=translations)
        loser_changes = matches_processed.loc[:, ["loser_pid", "rating_to_loser"]].rename(columns=translations)
        rating_changes = pd.concat([winner_changes, loser_changes], ignore_index=True)
        rating_changes = rating_changes.groupby("pid").sum()

        # Assign changes to ranking_df and save details
        reordered_changes = self.merge_preserve_left_index(self.ranking_df.loc[new_tid_indexes, "pid"],
                                                           rating_changes, on="pid")
        self.ranking_df.loc[reordered_changes.index, "rating"] += reordered_changes.loc[:, "rating_change"]

        self.rating_details_df = self.rating_details_df.append(matches_processed)
        self.update_categories()

    def compute_category_points(self, tid: str, best_rounds: pd.DataFrame):
        col_translations = {"round_reached": "best_round", "level_1": "category", 0: "points"}
        points_assignation_table = best_rounds_points.stack().reset_index().rename(columns=col_translations)

        best_rounds_pointed = best_rounds.merge(points_assignation_table, on=["category", "best_round"])
        best_rounds_pointed.insert(0, "tid", tid)

        for cat, points_cat_col in zip(categories, self.points_cat_columns()):
            rows_reordered = self.merge_preserve_left_index(self.ranking_df.loc[self.ranking_df.tid == tid, "pid"],
                                                            best_rounds_pointed[best_rounds_pointed.category == cat],
                                                            on="pid", how="inner")
            self.ranking_df.loc[rows_reordered.index, points_cat_col] = rows_reordered.loc[:, "points"]

        # Save details of assigned points
        self.championship_details_df = self.championship_details_df.append(best_rounds_pointed, ignore_index=True)

    @staticmethod
    def merge_preserve_left_index(left: pd.DataFrame, right: pd.DataFrame, **kwargs):
        return left.reset_index().merge(right, **kwargs).set_index('index').rename_axis(None)

    def compute_championship_points(self, tid: str):
        """
        Compute and save championship points, selected tids, and participations per category
        :return: None
        """
        n_tournaments = cfg["aux"]["masters N tournaments to consider"]
        tid_indexes = self.ranking_df.tid == tid
        rankings = self.ranking_df[self.ranking_df.tid != cfg["aux"]["initial tid"]]  # Remove initial tid data

        for points_cat_col, cum_points_cat_col, cum_tids_cat_col, n_played_cat_col in zip(
                self.points_cat_columns(), self.cum_points_cat_columns(), self.cum_tids_cat_columns(),
                self.participations_cat_columns()):

            # Best n_tournaments, not consider null points data to accelerate processing
            rankings_not_null = rankings[rankings[points_cat_col] > 0].copy()
            n_best = rankings_not_null.sort_values(by=[points_cat_col], ascending=False).groupby("pid").head(
                n_tournaments)

            # Cumulated points of the best n_tournaments
            cum_points_cat_values = n_best.groupby("pid")[points_cat_col].sum().rename(cum_points_cat_col)
            rows_reordered = self.merge_preserve_left_index(self.ranking_df.loc[tid_indexes, "pid"],
                                                            cum_points_cat_values, on="pid", how="inner")
            self.ranking_df.loc[rows_reordered.index, cum_points_cat_col] = rows_reordered.loc[:, cum_points_cat_col]

            # Details of cumulated points, formatted as POINTS (TID) + POINTS(TID) + ...
            n_best[cum_tids_cat_col] = n_best[points_cat_col].astype(int).astype(str) + " (" + n_best['tid'] + ") + "
            selected_tids_cat_values = n_best.groupby("pid")[cum_tids_cat_col].sum().apply(lambda x: x[:-3])
            rows_reordered = self.merge_preserve_left_index(self.ranking_df.loc[tid_indexes, "pid"],
                                                            selected_tids_cat_values, on="pid", how="inner")
            self.ranking_df.loc[rows_reordered.index, cum_tids_cat_col] = rows_reordered.loc[:, cum_tids_cat_col]

            # Total number of participations
            n_played_cat_values = rankings_not_null.groupby(["pid"])[points_cat_col].count()
            n_played_cat_values.rename(n_played_cat_col, inplace=True)
            rows_reordered = self.merge_preserve_left_index(self.ranking_df.loc[tid_indexes, "pid"],
                                                            n_played_cat_values, on="pid", how="inner")
            self.ranking_df.loc[rows_reordered.index, n_played_cat_col] = rows_reordered.loc[:, n_played_cat_col]

    @staticmethod
    def _activate_or_inactivate_player(ranking_entry, tids_list, active_window_tids, inactive_window_tids,
                                       players, initial_active_pids):
        # Avoid activate or inactivate players after the first tournament.
        activate_window = cfg["aux"]["tournament window to activate"]
        tourns_to_activate = cfg["aux"]["tournaments to activate"]
        inactivate_window = cfg["aux"]["tournament window to inactivate"]

        played_tids = players.played_tournaments(ranking_entry.pid)

        if not ranking_entry.active:
            last_tourns = [p_tid for p_tid in played_tids if p_tid in active_window_tids]
            # activate if he has played at least tourns_to_activate tournaments
            active = len(last_tourns) >= tourns_to_activate
        else:
            last_tourns = [p_tid for p_tid in played_tids if p_tid in inactive_window_tids]
            # don't inactivate during tournaments window if it is an initial active player
            if tids_list.index(ranking_entry.tid) + 1 < inactivate_window and ranking_entry.pid in initial_active_pids:
                active = True
            else:
                active = len(last_tourns) > 0

        return active

    def update_active_players(self, tid: str, players, initial_tid: str):
        # Avoid activate or inactivate players after the first tournament.
        activate_window = cfg["aux"]["tournament window to activate"]
        inactivate_window = cfg["aux"]["tournament window to inactivate"]

        indexes = (self.ranking_df.tid == initial_tid) & self.ranking_df.active
        initial_active_players = list(self.ranking_df.loc[indexes, "pid"].unique())

        tids_list = self._get_tids_list()
        active_window_tids = tids_list[max(0, tids_list.index(tid) - activate_window + 1):tids_list.index(tid) + 1]
        inactive_window_tids = tids_list[max(0, tids_list.index(tid) - inactivate_window + 1):tids_list.index(tid) + 1]

        tid_criteria = self.ranking_df.tid == tid

        self.ranking_df.loc[tid_criteria, "active"] = self.ranking_df[tid_criteria].apply(
            self._activate_or_inactivate_player, axis="columns",
            args=(tids_list, active_window_tids, inactive_window_tids, players, initial_active_players))

    def _get_tids_list(self) -> List[str]:
        return sorted(list(self.ranking_df.tid.unique()))

    def promote_players(self, tid: str, tournaments: "Tournaments") -> None:
        tournament_df = tournaments[tid]
        for match_index, match in tournament_df[tournament_df.promote].iterrows():
            self[tid, match.winner_pid, "category"] = match.category
            print(match.winner, "promoted to", match.category)

    def apply_sanction(self, tid: str, tournaments: "Tournaments") -> None:
        tournament_df = tournaments[tid]
        for match_index, match in tournament_df[tournament_df.sanction].iterrows():
            for cat_col in self.points_cat_columns():
                self[tid, match.loser_pid, cat_col] *= cfg["aux"]["sanction factor"]
            print("Apply sanction factor", cfg["aux"]["sanction factor"], "on:", match.winner)

    def get_rating_details(self, tid: str) -> pd.DataFrame:
        return self.rating_details_df.loc[self.rating_details_df.tid == tid].copy()

    def get_championship_details(self, tid: str) -> pd.DataFrame:
        return self.championship_details_df.loc[self.championship_details_df.tid == tid].copy()

    @staticmethod
    def _count_unique_pids(df: pd.DataFrame, points_columns):
        any_cat_participations = (df.loc[:, points_columns] > 0).any(axis="columns")
        pid_count = df.loc[any_cat_participations, "pid"].nunique()

        return pid_count

    def get_statistics(self) -> pd.DataFrame:
        """
        Return a DataFrame that summarizes total and in each category participations:
        - the number of players that have participated up to tournament(tid)
        - the number of players that have participated in tournament(tid)
        """
        # stats by category
        columns = ["tid"] + self.cum_points_cat_columns() + self.points_cat_columns()
        stats_cat = self.ranking_df.loc[:, columns].groupby("tid").apply(lambda df: (df > 0).sum(axis=0))
        stats_cat.rename(lambda col: col.replace("points", "participation"), axis="columns", inplace=True)

        # total stats cumulated. multi category players on a tournament are counted once
        columns = ["tid", "pid"] + self.cum_points_cat_columns()
        cum_participation_total = self.ranking_df.loc[:, columns].groupby("tid").apply(
            self._count_unique_pids, self.cum_points_cat_columns())
        cum_participation_total.rename("cum_participation_total", inplace=True)

        # total stats. multi category players on a tournament are counted once
        columns = ["tid", "pid"] + self.points_cat_columns()
        participation_total = self.ranking_df.loc[:, columns].groupby("tid").apply(
            self._count_unique_pids, self.points_cat_columns())
        participation_total.rename("participation_total", inplace=True)

        # Join results in a single table
        stats = stats_cat.join([participation_total, cum_participation_total]).sort_index(axis="columns")
        stats.drop(cfg["aux"]["initial tid"], inplace=True)

        return stats


class Tournaments:
    def __init__(self, tournaments_df: pd.DataFrame = None) -> None:
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
        self.tournaments_df.insert(len(self.tournaments_df.columns), "winner_pid", None)
        self.tournaments_df.insert(len(self.tournaments_df.columns), "loser_pid", None)

        self.verify_and_normalize()

    def __len__(self) -> int:
        return len(self.tournaments_df)

    def __str__(self) -> str:
        return str(self.tournaments_df)

    def __iter__(self) -> Iterator[str]:
        grouped = self.tournaments_df.groupby("tid").groups.keys()
        return iter(grouped)

    def __getitem__(self, tid: str) -> pd.DataFrame:
        criteria = self.tournaments_df.tid == tid
        return self.tournaments_df.loc[criteria].copy()

    @staticmethod
    def _process_match(match_row: pd.Series) -> pd.Series:
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

    def _assign_tid(self) -> None:
        def tid_str(grp):
            dates_ordered = sorted(grp["date"].unique())
            numbered = {pd.Timestamp(date): num for num, date in enumerate(dates_ordered, 1)}
            tids = grp["date"].transform(lambda row: "S%sT%02d" % (row.year, numbered[row]))

            return tids
        # TODO verify, groupby gives an unexpected result and need to be transposed
        tid = self.tournaments_df.groupby("year", as_index=False, group_keys=False).apply(tid_str)
        self.tournaments_df["tid"] = tid.transpose()

    def verify_and_normalize(self) -> None:
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

    def get_players_names(self, tid: str, category: str = '') -> List[str]:
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

    def get_players_pids(self, tid: str, category: str = '') -> List[int]:
        """
        Return a list of pid players that played the tournament

        If category is given, the list of players is filtered by category
        """
        criteria = self.tournaments_df.tid == tid
        if category:
            criteria = criteria & (self.tournaments_df.category == category)

        winner = self.tournaments_df.loc[criteria, "winner_pid"]
        loser = self.tournaments_df.loc[criteria, "loser_pid"]
        all_players = winner.append(loser, ignore_index=True).unique()

        return sorted(list(all_players))

    def compute_best_rounds(self, tid: str, players: Players) -> pd.DataFrame:
        """
        Return a DataFramey with the best round for each player and category. pid is assigned from players
        """
        matches = self.get_matches(tid, exclude_fan_category=False, to_exclude=["sanction", "promote"])

        # Filter matches to process so best rounds can be computed
        translations = {"winner": "name", "loser": "name", "winner_pid": "pid", "loser_pid": "pid",
                        "winner_round": "best_round", "loser_round": "best_round"}
        winner_data = matches.loc[:, ["winner", "winner_pid", "category", "winner_round"]].rename(columns=translations)
        loser_data = matches.loc[:, ["loser", "loser_pid", "category", "loser_round"]].rename(columns=translations)
        rounds_data = pd.concat([winner_data, loser_data], ignore_index=True)

        # Assign priority to matches
        rounds_data["round_priority"] = rounds_data.loc[:, "best_round"].map(best_rounds_priority.to_dict())

        # Get best one for each player and category
        rounds_data.sort_values(by="round_priority", ascending=False, inplace=True)
        best_rounds = rounds_data.groupby(by=["category", "pid"]).head(1).drop(columns="round_priority")
        best_rounds = best_rounds.sort_values(by=["category", "pid"]).reset_index(drop=True)

        return best_rounds

    def assign_pid_from_players(self, players: Players) -> None:
        name2pid = players.get_name2pid()
        self.tournaments_df["winner_pid"] = self.tournaments_df["winner"].apply(lambda name: name2pid[name])
        self.tournaments_df["loser_pid"] = self.tournaments_df["loser"].apply(lambda name: name2pid[name])

    def get_matches(self, tid: str, exclude_fan_category: bool = True, to_exclude: List[str] = None) -> pd.DataFrame:
        if to_exclude is None:
            to_exclude = ["sanction", "promote", "bonus"]
        entries_indexes = (self.tournaments_df.loc[:, "tid"] == tid)
        if exclude_fan_category:
            entries_indexes &= ~(self.tournaments_df.loc[:, "category"] == categories[-1])
        entries_indexes &= ~self.tournaments_df.loc[:, to_exclude].any(axis="columns")

        return self.tournaments_df[entries_indexes]
