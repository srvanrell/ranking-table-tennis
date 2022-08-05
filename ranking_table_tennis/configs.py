import os

import hydra
import pandas as pd
from omegaconf import OmegaConf

_cfg = None


def get_cfg(date=None):
    """First cfg valid for date"""
    global _cfg

    if _cfg:
        return _cfg

    print("\n## Loading config\n")

    # Loads some names from config.yaml
    user_config_path = os.path.join(os.path.dirname(__file__), "config")
    print(f"Working directory: {os.path.abspath(os.path.curdir)}")
    print(f"Config directory: {os.path.abspath(user_config_path)}")

    _cfg = Configuration(user_config_path).get_config()

    if not os.path.exists(_cfg.io.data_folder):
        os.mkdir(_cfg.io.data_folder)

    return _cfg


class Configuration:
    def __init__(self, config_path: str = "") -> None:
        self.dict_cfg = None
        self.start_valid_date = None
        self.end_valid_date = None
        self._config_path = config_path

    def get_config(self):
        """Load config from the config_path."""
        if self.dict_cfg is None:
            base_cfg = self._load_base_config()
            tables_cfg = self._load_tables_config()
            self.dict_cfg = OmegaConf.merge(base_cfg, tables_cfg)

        return self.dict_cfg

    def _load_base_config(self):
        config_dir = os.path.abspath(self._config_path)
        with hydra.initialize_config_dir(
            version_base=None, config_dir=config_dir, job_name="rtt_app"
        ):
            return hydra.compose(config_name="config")

    def _load_tables_config(self):
        """Load dict_cfg with tables to assign championship and rating points"""

        # Tables to assign points

        # difference, points to winner, points to loser
        expected_result_table = pd.read_csv(os.path.join(self._config_path, "expected_result.csv"))

        # negative difference, points to winner, points to loser
        unexpected_result_table = pd.read_csv(
            os.path.join(self._config_path, "unexpected_result.csv")
        )

        # points to be assigned by round and by participation
        raw_points_per_round_table = pd.read_csv(
            os.path.join(self._config_path, "points_per_round.csv")
        )
        best_rounds_points = raw_points_per_round_table.drop(columns="priority")

        # Priority of rounds in a tournament
        best_rounds_priority = raw_points_per_round_table.set_index("round_reached")["priority"]

        # List of categories
        categories = raw_points_per_round_table.columns[2:]

        # Convert to simpler types so they can be configs
        extra_cfg = OmegaConf.create(
            {
                "expected_result_table": expected_result_table.to_dict(),
                "unexpected_result_table": unexpected_result_table.to_dict(),
                "categories": list(categories),
                "best_rounds_points": best_rounds_points.to_dict(),
                "best_rounds_priority": best_rounds_priority.to_dict(),
            }
        )

        return extra_cfg
