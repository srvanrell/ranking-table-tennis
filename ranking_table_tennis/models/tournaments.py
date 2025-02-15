import logging
from typing import Iterator, List

import pandas as pd
from omegaconf import OmegaConf
from unidecode import unidecode

from ranking_table_tennis.configs import ConfigManager
from ranking_table_tennis.models import Players

logger = logging.getLogger(__name__)


class Tournaments:
    def __init__(self, tournaments_df: pd.DataFrame = None) -> None:
        """
        Create a tournaments database from given tournaments DataFrame.
        Verification and normalization is performed on loading.

        There are workarounds available to promote, sanction, or provide championship points

        :param tournaments_df: DataFrame with columns: tournament_name, date, location,
               player_a, player_b, sets_a, sets_b, round, category
        """
        self.tournaments_df = pd.DataFrame(
            tournaments_df,
            columns=[
                "tid",
                "sheet_name",
                "tournament_name",
                "date",
                "location",
                "player_a",
                "player_b",
                "sets_a",
                "sets_b",
                "round",
                "category",
            ],
        ).assign(
            winner=None,
            winner_round=None,
            loser=None,
            loser_round=None,
            promote=False,
            sanction=False,
            bonus=False,
            winner_pid=None,
            loser_pid=None,
        )
        self.tournaments_df.insert(4, "year", None)

        self.update_config()

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

    def update_config(self):
        self.cfg = ConfigManager().current_config

    def _batch_process_matches(self, matches: pd.DataFrame) -> pd.DataFrame:
        # workaround to add extra bonus points from match list
        matches["winner"] = matches["player_b"]
        matches["loser"] = matches["player_b"]
        # Promotions
        matches["promote"] = (matches["sets_a"] >= 10) & (matches["sets_b"] >= 10)
        # Sanctions
        matches["sanction"] = (matches["sets_a"] <= -10) & (matches["sets_b"] <= -10)
        # Bonus points
        matches["bonus"] = (
            (matches["sets_a"] < 0) & (matches["sets_b"] < 0) & (~matches["sanction"])
        )

        # Real matches
        real_matches = ~(matches["bonus"] | matches["sanction"] | matches["promote"])
        # Win player A
        win_a = (matches["sets_a"] > matches["sets_b"]) & real_matches
        matches.loc[win_a, "winner"] = matches.loc[win_a, "player_a"]
        matches.loc[win_a, "loser"] = matches.loc[win_a, "player_b"]
        # Win player B
        win_b = (matches["sets_a"] < matches["sets_b"]) & real_matches
        matches.loc[win_b, "winner"] = matches.loc[win_b, "player_b"]
        matches.loc[win_b, "loser"] = matches.loc[win_b, "player_a"]
        # Unexpected ties
        tied_matches = (matches["sets_a"] == matches["sets_b"]) & real_matches
        if tied_matches.any():
            logger.error(
                "Failed to process matches, ties were found at:\n%s", matches.loc[tied_matches]
            )
            raise ImportError

        # Do not change other rounds
        matches["winner_round"] = matches["round"]
        matches["loser_round"] = matches["round"]
        # Modify labels of finals round match
        final_matches = matches["round"] == self.cfg.roundnames.final
        matches.loc[final_matches, "winner_round"] = self.cfg.roundnames.champion
        matches.loc[final_matches, "loser_round"] = self.cfg.roundnames.second
        # Modify labels of third_place_playoff round match
        third_place_matches = matches["round"] == self.cfg.roundnames.third_place_playoff
        matches.loc[third_place_matches, "winner_round"] = self.cfg.roundnames.third
        matches.loc[third_place_matches, "loser_round"] = self.cfg.roundnames.fourth

        return matches

    @staticmethod
    def tid_str(year_grp):
        tids = year_grp["date"].dt.strftime("S%Y").rename("tid")
        dates_ordered = sorted(year_grp["date"].unique())
        for num, date in enumerate(dates_ordered, 1):
            filtered_rows = year_grp["date"] == date
            tids.loc[filtered_rows] += "T%02d" % num

        return tids

    def verify_and_normalize(self) -> None:
        self.tournaments_df = (
            self.tournaments_df.assign(
                # Columns to lower
                round=lambda df: df["round"].str.strip().str.lower(),
                category=lambda df: df.category.str.strip().str.lower(),
                # Columns to title
                tournament_name=lambda df: df.tournament_name.str.strip().str.title(),
                date=lambda df: pd.to_datetime(df.date.str.strip().str.title()),
                location=lambda df: df.location.str.strip().str.title(),
                player_a=lambda df: df.player_a.apply(unidecode).str.strip().str.title(),
                player_b=lambda df: df.player_b.apply(unidecode).str.strip().str.title(),
                year=lambda df: df.date.dt.year.astype(int),
                tid=lambda df: self.tid_str(df),
            )
            .astype(
                {
                    "sets_a": int,
                    "sets_b": int,
                    # "round": "category",
                    # "category": "category",
                    # "location": "category",
                    # "tournament_name": "category",
                }
            )
            .pipe(self._batch_process_matches)
        )

    def get_players_names(self, tid: str, category: str = "") -> List[str]:
        """
        Return a sorted list of players that played the tournament

        If category is given, the list of players is filtered by category
        """
        criteria = self.tournaments_df.tid == tid
        if category:
            criteria = criteria & (self.tournaments_df.category == category)

        winner = self.tournaments_df.loc[criteria, "winner"]
        loser = self.tournaments_df.loc[criteria, "loser"]
        all_players = pd.concat([winner, loser], ignore_index=True).unique()

        return sorted(list(all_players))

    def get_players_pids(self, tid: str, category: str = "") -> List[int]:
        """
        Return a list of pid players that played the tournament

        If category is given, the list of players is filtered by category
        """
        criteria = self.tournaments_df.tid == tid
        if category:
            criteria = criteria & (self.tournaments_df.category == category)

        winner = self.tournaments_df.loc[criteria, "winner_pid"]
        loser = self.tournaments_df.loc[criteria, "loser_pid"]
        all_players = pd.concat([winner, loser], ignore_index=True).unique()

        return sorted(list(all_players))

    def compute_best_rounds(self, tid: str, players: Players) -> pd.DataFrame:
        """
        Return a DataFrame with the best round for each player and category.

        pid is assigned from players
        """
        matches = self.get_matches(
            tid, exclude_fan_category=False, to_exclude=["sanction", "promote"]
        )

        # Filter matches to process so best rounds can be computed
        translations = {
            "winner": "name",
            "loser": "name",
            "winner_pid": "pid",
            "loser_pid": "pid",
            "winner_round": "best_round",
            "loser_round": "best_round",
        }
        winner_data = matches.loc[:, ["winner", "winner_pid", "category", "winner_round"]].rename(
            columns=translations
        )
        loser_data = matches.loc[:, ["loser", "loser_pid", "category", "loser_round"]].rename(
            columns=translations
        )
        rounds_data = pd.concat([winner_data, loser_data], ignore_index=True)

        # Assign priority to matches
        rounds_data["round_priority"] = rounds_data.loc[:, "best_round"].map(
            OmegaConf.to_container(self.cfg.best_rounds_priority, resolve=True)
        )

        # Get best one for each player and category
        rounds_data.sort_values(by="round_priority", ascending=False, inplace=True)
        best_rounds = (
            rounds_data.groupby(by=["category", "pid"]).head(1).drop(columns="round_priority")
        )
        best_rounds = best_rounds.sort_values(by=["category", "pid"]).reset_index(drop=True)

        return best_rounds

    def assign_pid_from_players(self, players: Players) -> None:
        name2pid = players.get_name2pid()
        self.tournaments_df["winner_pid"] = self.tournaments_df["winner"].map(name2pid)
        self.tournaments_df["loser_pid"] = self.tournaments_df["loser"].map(name2pid)

    def get_matches(
        self, tid: str, exclude_fan_category: bool = True, to_exclude: List[str] = None
    ) -> pd.DataFrame:
        if to_exclude is None:
            to_exclude = ["sanction", "promote", "bonus"]
        entries_indexes = self.tournaments_df.loc[:, "tid"] == tid
        if exclude_fan_category:
            entries_indexes &= ~(self.tournaments_df.loc[:, "category"] == self.cfg.categories[-1])
        entries_indexes &= ~self.tournaments_df.loc[:, to_exclude].any(axis="columns")

        return self.tournaments_df[entries_indexes]
