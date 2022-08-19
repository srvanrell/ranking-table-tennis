from typing import Iterator, List

import pandas as pd
from omegaconf import OmegaConf
from unidecode import unidecode

from ranking_table_tennis.configs import ConfigManager
from ranking_table_tennis.models import Players


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
        )
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

        cfg = ConfigManager().current_config

        # changing labels of finals round match
        if match_row["round"] == cfg.roundnames.final:
            match_row["winner_round"] = cfg.roundnames.champion
            match_row["loser_round"] = cfg.roundnames.second
        elif match_row["round"] == cfg.roundnames.third_place_playoff:
            match_row["winner_round"] = cfg.roundnames.third
            match_row["loser_round"] = cfg.roundnames.fourth
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
        self.tournaments_df.loc[:, cols_to_lower] = self.tournaments_df.loc[
            :, cols_to_lower
        ].applymap(lambda cell: cell.strip().lower())

        cols_to_title = ["tournament_name", "date", "location", "player_a", "player_b"]
        self.tournaments_df.loc[:, cols_to_title] = self.tournaments_df.loc[
            :, cols_to_title
        ].applymap(lambda cell: unidecode(cell).strip().title())

        self.tournaments_df = self.tournaments_df.astype(
            {
                "round": "category",
                "category": "category",
                "location": "category",
                "tournament_name": "category",
            }
        )

        self.tournaments_df.date = pd.to_datetime(self.tournaments_df.date)
        self.tournaments_df["year"] = self.tournaments_df.apply(
            lambda row: row["date"].year, axis="columns"
        )
        self._assign_tid()
        self.tournaments_df = self.tournaments_df.apply(self._process_match, axis="columns")

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
        cfg = ConfigManager().current_config
        rounds_data["round_priority"] = rounds_data.loc[:, "best_round"].map(
            OmegaConf.to_container(cfg.best_rounds_priority, resolve=True)
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
        self.tournaments_df["winner_pid"] = self.tournaments_df["winner"].apply(
            lambda name: name2pid.get(name)
        )
        self.tournaments_df["loser_pid"] = self.tournaments_df["loser"].apply(
            lambda name: name2pid.get(name)
        )

    def get_matches(
        self, tid: str, exclude_fan_category: bool = True, to_exclude: List[str] = None
    ) -> pd.DataFrame:
        cfg = ConfigManager().current_config
        if to_exclude is None:
            to_exclude = ["sanction", "promote", "bonus"]
        entries_indexes = self.tournaments_df.loc[:, "tid"] == tid
        if exclude_fan_category:
            entries_indexes &= ~(self.tournaments_df.loc[:, "category"] == cfg.categories[-1])
        entries_indexes &= ~self.tournaments_df.loc[:, to_exclude].any(axis="columns")

        return self.tournaments_df[entries_indexes]
