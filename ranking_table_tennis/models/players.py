import logging
from typing import List

import pandas as pd
from unidecode import unidecode

logger = logging.getLogger(__name__)


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
            logger.error("Players entries duplicated:\n%s", self.players_df[duplicated])

        self.players_df.fillna("", inplace=True)

        # cols_to_upper = ["affiliation"]
        # self.players_df.loc[:, cols_to_upper] = self.players_df.loc[:, cols_to_upper].map(
        #     lambda cell: cell.strip().upper())

        cols_to_title = ["name", "city"]
        self.players_df.loc[:, cols_to_title] = self.players_df.loc[:, cols_to_title].map(
            lambda cell: unidecode(cell).strip().title()
        )

    def get_pid(self, name: str) -> int:
        uname = unidecode(name).title()
        pid = self.players_df[self.players_df.name == uname].first_valid_index()
        if pid is None:
            logger.warn("WARNING: Unknown player: %s", uname)

        return pid

    def get_name2pid(self) -> pd.Series:
        name2pid = self.players_df.loc[:, "name"].copy()
        name2pid = name2pid.reset_index()
        name2pid.set_index("name", inplace=True)

        return name2pid.loc[:, "pid"]

    @property
    def pid2name_mapper(self) -> pd.Series:
        """Map a pid to corresponding name"""
        return self.players_df["name"]

    def add_player(self, player: pd.Series) -> None:
        self.players_df = pd.concat([self.players_df, player], axis="index")
        self.verify_and_normalize()

    def add_new_player(self, name: str, affiliation: str = "", city: str = "") -> None:
        pid = self.players_df.index.max() + 1
        self.players_df.loc[pid] = {"name": name, "affiliation": affiliation, "city": city}
        self.verify_and_normalize()

    def update_histories(self, tid: str, best_rounds: pd.DataFrame) -> None:
        """Save player's best rounds into their histories.

        Each history is a string that can be read as a dict with (category, tournament_id) as key.
        """
        to_update = best_rounds.loc[:, ["pid", "category", "best_round"]]
        to_update.insert(0, "tid", tid)
        self.history_df = (
            pd.concat([self.history_df, to_update])
            .drop_duplicates(ignore_index=True)
            .infer_objects()
        )

    def played_tournaments(self, pid: int) -> List[str]:
        """Return sorted list of played tournaments. Empty history will result in an empty list."""
        tids = self.history_df.loc[self.history_df.pid == float(pid), "tid"]
        if not tids.empty:
            return sorted(set(tids))
        return []
