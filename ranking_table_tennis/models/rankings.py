import logging
from typing import List, Tuple

import pandas as pd
from omegaconf import OmegaConf

from ranking_table_tennis.configs import ConfigManager
from ranking_table_tennis.models.tournaments import Tournaments

logger = logging.getLogger(__name__)


class Rankings:
    def __init__(self, ranking_df: pd.DataFrame = None) -> None:
        self.update_config()
        all_columns = [
            "tid",
            "tournament_name",
            "date",
            "location",
            "pid",
            "rating",
            "category",
            "active",
        ]
        all_columns += (
            self.points_cat_columns()
            + self.cum_points_cat_columns()
            + self.participations_cat_columns()
        )
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

    def points_cat_columns(self) -> List[str]:
        return ["points_cat_%d" % d for d, _ in enumerate(self.cfg.categories, 1)]

    def cum_points_cat_columns(self) -> List[str]:
        return ["cum_points_cat_%d" % d for d, _ in enumerate(self.cfg.categories, 1)]

    def cum_tids_cat_columns(self) -> List[str]:
        return ["cum_tids_cat_%d" % d for d, _ in enumerate(self.cfg.categories, 1)]

    def participations_cat_columns(self) -> List[str]:
        return ["participations_cat_%d" % d for d, _ in enumerate(self.cfg.categories, 1)]

    def update_config(self):
        self.cfg = ConfigManager().current_config

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
        ranking_entry_df = ranking_entry.to_frame().T
        self.ranking_df = pd.concat([self.ranking_df, ranking_entry_df], axis="index")
        self.verify_and_normalize()

    def add_new_entry(
        self,
        tid: str,
        pid: int,
        initial_rating: float = -1000.0,
        active: bool = False,
        initial_category: str = "",
    ) -> None:
        new_entry = pd.DataFrame(
            {
                "tid": tid,
                "pid": pid,
                "rating": initial_rating,
                "active": active,
                "category": initial_category,
            },
            index=[-1],
        )
        self.ranking_df = pd.concat([self.ranking_df, new_entry], ignore_index=True, axis="index")
        self.verify_and_normalize()
        self.update_categories(tid)

    def verify_and_normalize(self) -> None:
        duplicated = self.ranking_df.duplicated(["tid", "pid"], keep=False)
        if duplicated.any():
            logger.error("Ranking entries duplicated:\n%s", self.ranking_df[duplicated])

        default_rating = -1000.0
        default_active = False
        default_category = ""
        default_cat_value = 0.0
        default_cum_tid_value = ""

        cat_columns = (
            self.points_cat_columns()
            + self.cum_points_cat_columns()
            + self.participations_cat_columns()
        )
        cum_tid_values = {
            cum_tid_col: default_cum_tid_value for cum_tid_col in self.cum_tids_cat_columns()
        }
        cat_col_values = {cat_col: default_cat_value for cat_col in cat_columns}
        default_values = {
            "rating": default_rating,
            "category": default_category,
            "active": default_active,
            "tournament_name": self.cfg.initial_metadata.tournament_name,
            "date": self.cfg.initial_metadata.date,
            "location": self.cfg.initial_metadata.location,
            **cat_col_values,
            **cum_tid_values,
        }
        self.ranking_df.fillna(value=default_values, inplace=True)
        self.ranking_df.date = pd.to_datetime(self.ranking_df.date)
        self.ranking_df = self.ranking_df.astype({"rating": "float"})  # Force rating to be float

    def initialize_new_ranking(self, new_tid: str, prev_tid: str) -> None:
        entries_indexes = self.ranking_df.tid == prev_tid
        new_ranking = self.ranking_df.loc[entries_indexes].copy()
        new_ranking.loc[:, "tid"] = new_tid
        new_ranking.loc[:, self.points_cat_columns() + self.cum_points_cat_columns()] = 0.0
        new_ranking.loc[:, self.participations_cat_columns()] = 0.0
        new_ranking.loc[:, self.cum_tids_cat_columns()] = ""
        self.ranking_df = pd.concat([self.ranking_df, new_ranking], ignore_index=True)

    def _batch_rating_to_category(self, rating: pd.Series) -> pd.Series:
        # Order reversed to assign first category as last option
        category_names = reversed(
            self.cfg.categories[:-2]
        )  # Last and fan categories are not required
        thresholds = reversed(self.cfg.compute.categories_thresholds)
        # Default to last category that it's not fan
        category = pd.Series(self.cfg.categories[-2], index=rating.index, name="category")
        for cat, th in zip(category_names, thresholds):
            greater_rating = rating >= th
            category.loc[greater_rating] = cat

        return category

    def update_categories(self, tid) -> None:
        """Players are ranked based on rating and given thresholds.

        Players are ordered by rating and then assigned to a category

        Example:
        - rating >= 500        -> first category
        - 500 > rating >= 250  -> second category
        - 250 > rating         -> third category
        """
        # FIXME it is not working for players of the fan category
        tid_entries = self.ranking_df.tid == tid
        self.ranking_df.loc[tid_entries, "category"] = self._batch_rating_to_category(
            self.ranking_df.loc[tid_entries, "rating"]
        )

    def sort_rankings(self):
        """Sort rankings DataFrame by tid ascending, rating descending, pid ascending."""
        self.ranking_df = self.ranking_df.sort_values(
            ["tid", "rating", "pid"], ascending=[True, False, True]
        ).reset_index(drop=True)

    def _points_to_assign(self, rating_winner: float, rating_loser: float) -> Tuple[float, float]:
        """Points to add to winner and to deduce from loser given ratings of winner and loser."""
        rating_diff = rating_winner - rating_loser

        assignation_table = self.cfg.expected_result_table
        if rating_diff < 0:
            rating_diff *= -1.0
            assignation_table = self.cfg.unexpected_result_table

        assignation_table = pd.DataFrame(
            OmegaConf.to_container(assignation_table, resolve=True)
        ).to_numpy()

        # Select first row that is appropiate for given rating_diff
        diff_threshold, points_to_winner, points_to_loser = assignation_table[
            assignation_table[:, 0] > rating_diff
        ][0]

        return points_to_winner, points_to_loser

    def _get_factor(
        self,
        rating_winner: float,
        rating_loser: float,
        category_winner: str,
        category_loser: str,
        not_own_category: bool,
    ) -> float:
        """Returns factor for rating computation. It considers given winner and loser category.
        Players must play their own category"""
        rating_diff = rating_winner - rating_loser
        category_factor = 1.0
        if category_winner != category_loser and not not_own_category:
            category_factor = self.cfg.compute.category_expected_factor
            if rating_diff < 0:
                category_factor = self.cfg.compute.category_unexpected_factor

        factor = self.cfg.compute.rating_factor * category_factor

        return factor

    def _new_ratings_from_match(self, match):
        [to_winner, to_loser] = self._points_to_assign(
            match["winner_rating"], match["loser_rating"]
        )
        factor = self._get_factor(
            match["winner_rating"],
            match["loser_rating"],
            match["winner_category"],
            match["loser_category"],
            match["not_own_category"],
        )

        to_winner, to_loser = factor * to_winner, factor * to_loser
        match["rating_to_winner"], match["rating_to_loser"], match["factor"] = (
            to_winner,
            -to_loser,
            factor,
        )

        return match

    def compute_new_ratings(
        self,
        new_tid: str,
        old_tid: str,
        tournaments: "Tournaments",
        pid_not_own_category: List[int],
    ):
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
        winner_data = ranking_data.rename(
            columns={"category": "winner_category", "rating": "winner_rating"}
        )
        loser_data = ranking_data.rename(
            columns={"category": "loser_category", "rating": "loser_rating"}
        )
        matches = self.merge_preserve_left_index(
            matches, winner_data, left_on="winner_pid", right_on="pid"
        ).drop(columns="pid")
        matches = self.merge_preserve_left_index(
            matches, loser_data, left_on="loser_pid", right_on="pid"
        ).drop(columns="pid")
        matches["not_own_category"] = (
            matches.loc[:, ["winner_pid", "loser_pid"]].isin(pid_not_own_category).any(axis=1)
        )

        # Compute ratings changes per match
        matches_processed = matches.apply(self._new_ratings_from_match, axis="columns")

        # Compute overall rating changes per player
        translations = {
            "rating_to_winner": "rating_change",
            "rating_to_loser": "rating_change",
            "winner_pid": "pid",
            "loser_pid": "pid",
        }
        winner_changes = matches_processed.loc[:, ["winner_pid", "rating_to_winner"]].rename(
            columns=translations
        )
        loser_changes = matches_processed.loc[:, ["loser_pid", "rating_to_loser"]].rename(
            columns=translations
        )
        rating_changes = pd.concat([winner_changes, loser_changes], ignore_index=True)
        rating_changes = rating_changes.groupby("pid").sum()

        # Assign changes to ranking_df and save details
        reordered_changes = self.merge_preserve_left_index(
            self.ranking_df.loc[new_tid_indexes, "pid"], rating_changes, on="pid"
        )
        self.ranking_df.loc[reordered_changes.index, "rating"] += reordered_changes.loc[
            :, "rating_change"
        ]

        self.rating_details_df = pd.concat([self.rating_details_df, matches_processed])
        self.update_categories(new_tid)

    def compute_category_points(self, tid: str, best_rounds: pd.DataFrame):
        best_rounds_points_cfg = OmegaConf.to_container(self.cfg.best_rounds_points, resolve=True)
        best_rounds_points_df = pd.DataFrame(best_rounds_points_cfg).set_index("round_reached")
        col_translations = {"round_reached": "best_round", "level_1": "category", 0: "points"}
        points_assignation_table = (
            best_rounds_points_df.stack().reset_index().rename(columns=col_translations)
        )

        best_rounds_pointed = best_rounds.merge(
            points_assignation_table, on=["category", "best_round"]
        ).sort_values(["category", "points", "pid"], ascending=[True, False, True])
        best_rounds_pointed.insert(0, "tid", tid)

        for cat, points_cat_col in zip(self.cfg.categories, self.points_cat_columns()):
            rows_reordered = self.merge_preserve_left_index(
                self.ranking_df.loc[self.ranking_df.tid == tid, "pid"],
                best_rounds_pointed[best_rounds_pointed.category == cat],
                on="pid",
                how="inner",
            )
            self.ranking_df.loc[rows_reordered.index, points_cat_col] = rows_reordered.loc[
                :, "points"
            ]

        # Save details of assigned points
        self.championship_details_df = pd.concat(
            [self.championship_details_df, best_rounds_pointed], ignore_index=True
        )

    @staticmethod
    def merge_preserve_left_index(left: pd.DataFrame, right: pd.DataFrame, **kwargs):
        return left.reset_index().merge(right, **kwargs).set_index("index").rename_axis(None)

    def compute_championship_points(self, tid: str):
        """
        Compute and save championship points, selected tids, and participations per category
        :return: None
        """
        n_tournaments = self.cfg.compute.masters_N_tournaments_to_consider
        tid_indexes = self.ranking_df.tid == tid
        rankings = self.ranking_df[
            self.ranking_df.tid != self.cfg.initial_metadata.initial_tid
        ]  # Remove initial tid data

        for points_cat_col, cum_points_cat_col, cum_tids_cat_col, n_played_cat_col in zip(
            self.points_cat_columns(),
            self.cum_points_cat_columns(),
            self.cum_tids_cat_columns(),
            self.participations_cat_columns(),
        ):

            # Best n_tournaments, not consider null points data to accelerate processing
            rankings_not_null = rankings[rankings[points_cat_col] > 0].copy()
            n_best = (
                rankings_not_null.sort_values(by=[points_cat_col, "tid"], ascending=[False, False])
                .groupby("pid")
                .head(n_tournaments)
            )

            # Cumulated points of the best n_tournaments
            cum_points_cat_values = (
                n_best.groupby("pid")[points_cat_col].sum().rename(cum_points_cat_col)
            )
            rows_reordered = self.merge_preserve_left_index(
                self.ranking_df.loc[tid_indexes, "pid"],
                cum_points_cat_values,
                on="pid",
                how="inner",
            )
            self.ranking_df.loc[rows_reordered.index, cum_points_cat_col] = rows_reordered.loc[
                :, cum_points_cat_col
            ]

            # Details of cumulated points, formatted as POINTS (TID) + POINTS(TID) + ...
            n_best[cum_tids_cat_col] = (
                n_best[points_cat_col].astype(int).astype(str) + " (" + n_best["tid"] + ") + "
            )
            selected_tids_cat_values = (
                n_best.groupby("pid")[cum_tids_cat_col].sum().str.slice(stop=-3)
            )
            rows_reordered = self.merge_preserve_left_index(
                self.ranking_df.loc[tid_indexes, "pid"],
                selected_tids_cat_values,
                on="pid",
                how="inner",
            )
            self.ranking_df.loc[rows_reordered.index, cum_tids_cat_col] = rows_reordered.loc[
                :, cum_tids_cat_col
            ]

            # Total number of participations
            n_played_cat_values = rankings_not_null.groupby(["pid"])[points_cat_col].count()
            n_played_cat_values.rename(n_played_cat_col, inplace=True)
            rows_reordered = self.merge_preserve_left_index(
                self.ranking_df.loc[tid_indexes, "pid"], n_played_cat_values, on="pid", how="inner"
            )
            self.ranking_df.loc[rows_reordered.index, n_played_cat_col] = rows_reordered.loc[
                :, n_played_cat_col
            ]

    def _activate_or_inactivate_player(
        self,
        ranking_entry,
        tids_list,
        active_window_tids,
        inactive_window_tids,
        players,
        initial_active_pids,
    ):
        # Avoid activate or inactivate players after the first tournament.
        # activate_window = cfg.compute.tournament window to activate"]
        tourns_to_activate = self.cfg.compute.tournaments_to_activate
        inactivate_window = self.cfg.compute.tournament_window_to_inactivate

        played_tids = players.played_tournaments(ranking_entry.pid)

        if not ranking_entry.active:
            last_tourns = [p_tid for p_tid in played_tids if p_tid in active_window_tids]
            # activate if he has played at least tourns_to_activate tournaments
            active = len(last_tourns) >= tourns_to_activate
        else:
            last_tourns = [p_tid for p_tid in played_tids if p_tid in inactive_window_tids]
            # don't inactivate during tournaments window if it is an initial active player
            if (
                tids_list.index(ranking_entry.tid) + 1 < inactivate_window
                and ranking_entry.pid in initial_active_pids
            ):
                active = True
            else:
                active = len(last_tourns) > 0

        return active

    def update_active_players(self, tid: str, players, initial_tid: str):
        # Avoid activate or inactivate players after the first tournament.
        activate_window = self.cfg.compute.tournament_window_to_activate
        inactivate_window = self.cfg.compute.tournament_window_to_inactivate

        indexes = (self.ranking_df.tid == initial_tid) & self.ranking_df.active
        initial_active_players = list(self.ranking_df.loc[indexes, "pid"].unique())

        tids_list = self._get_tids_list()
        active_window_tids = tids_list[
            max(0, tids_list.index(tid) - activate_window + 1) : tids_list.index(tid) + 1  # noqa
        ]
        inactive_window_tids = tids_list[
            max(0, tids_list.index(tid) - inactivate_window + 1) : tids_list.index(tid) + 1  # noqa
        ]

        tid_criteria = self.ranking_df.tid == tid

        self.ranking_df.loc[tid_criteria, "active"] = self.ranking_df[tid_criteria].apply(
            self._activate_or_inactivate_player,
            axis="columns",
            args=(
                tids_list,
                active_window_tids,
                inactive_window_tids,
                players,
                initial_active_players,
            ),
        )

    def _get_tids_list(self) -> List[str]:
        return sorted(list(self.ranking_df.tid.unique()))

    def promote_players(self, tid: str, tournaments: "Tournaments") -> None:
        tournament_df = tournaments[tid]
        for match_index, match in tournament_df[tournament_df.promote].iterrows():
            self[tid, match.winner_pid, "category"] = match.category
            logger.debug("%s promoted to %s", match.winner, match.category)

    def apply_sanction(self, tid: str, tournaments: "Tournaments") -> None:
        tournament_df = tournaments[tid]
        for match_index, match in tournament_df[tournament_df.sanction].iterrows():
            for cat_col in self.points_cat_columns():
                self[tid, match.loser_pid, cat_col] *= self.cfg.compute.sanction_factor
            logger.debug(
                "Apply sanction factor %s on: %s", self.cfg.compute.sanction_factor, match.winner
            )

    def get_rating_details(self, tid: str) -> pd.DataFrame:
        return self.rating_details_df.loc[self.rating_details_df.tid == tid].copy()

    def get_championship_details(self, tid: str) -> pd.DataFrame:
        return self.championship_details_df.loc[self.championship_details_df.tid == tid].copy()

    @staticmethod
    def _count_unique_pids(df: pd.DataFrame, points_columns):
        any_cat_participations = (df.loc[:, points_columns] > 0).any(axis="columns")
        pid_count = df.loc[any_cat_participations, "pid"].nunique()

        return pid_count

    def get_statistics(self, tid) -> pd.DataFrame:
        """
        Return a DataFrame that summarizes total and in each category participations:
        - the number of players that have participated up to tournament(tid)
        - the number of players that have participated in tournament(tid)

        tid: ID of max tournament to consider
        """
        # TIDs to consider in statistic computation
        tids_to_consider = self.ranking_df.tid <= tid

        # stats by category
        columns = ["tid"] + self.cum_points_cat_columns() + self.points_cat_columns()
        stats_cat = (
            self.ranking_df.loc[tids_to_consider, columns]
            .groupby("tid")
            .apply(lambda df: (df > 0).sum(axis=0), include_groups=False)
            .rename(lambda col: col.replace("points", "participation"), axis="columns")
        )

        # total stats cumulated. multi category players on a tournament are counted once
        columns = ["tid", "pid"] + self.cum_points_cat_columns()
        cum_participation_total = (
            self.ranking_df.loc[tids_to_consider, columns]
            .groupby("tid")
            .apply(self._count_unique_pids, self.cum_points_cat_columns(), include_groups=False)
            .rename("cum_participation_total")
        )

        # total stats. multi category players on a tournament are counted once
        columns = ["tid", "pid"] + self.points_cat_columns()
        participation_total = (
            self.ranking_df.loc[:, columns]
            .groupby("tid")
            .apply(self._count_unique_pids, self.points_cat_columns(), include_groups=False)
            .rename("participation_total")
        )

        # Join results in a single table
        stats = stats_cat.join([participation_total, cum_participation_total]).sort_index(
            axis="columns"
        )
        stats.drop(self.cfg.initial_metadata.initial_tid, inplace=True)

        return stats
