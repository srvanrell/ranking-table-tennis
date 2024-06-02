import glob
import logging
import os

import hydra
import pandas as pd
from omegaconf import OmegaConf

USER_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config")
AVAILABLE_CONFIGS = glob.glob(os.path.join(USER_CONFIG_PATH, "config_*_*.yaml"))

logger = logging.getLogger(__name__)


class ConfigManager:
    _current_config = None
    _available_configs = None

    def __init__(self) -> None:
        pass

    def initialize(self):
        if ConfigManager._available_configs is None:
            self.set_available_configs()

    def set_available_configs(self):
        ConfigManager._available_configs = []
        for path in sorted(AVAILABLE_CONFIGS, reverse=True):
            ConfigManager._available_configs.append(Configuration(path))
            logger.debug("~ Available %s", ConfigManager._available_configs[-1])

    def get_valid_config(self, date):
        self.initialize()
        for conf in ConfigManager._available_configs:
            if conf.start_valid_date <= date <= conf.end_valid_date:
                return conf.get_config()

    @property
    def current_config(self):
        return ConfigManager._current_config

    def set_current_config(self, date):
        ConfigManager._current_config = self.get_valid_config(date)
        if not os.path.exists(ConfigManager._current_config.io.data_folder):
            os.mkdir(ConfigManager._current_config.io.data_folder)


class Configuration:
    def __init__(self, config_path: str = "") -> None:
        self.dict_cfg = None
        self.start_valid_date = None
        self.end_valid_date = None
        self._config_path, basename = os.path.split(config_path)
        self._config_name, _ = os.path.splitext(basename)

        self._set_dates()

    def __str__(self) -> str:
        return f"Configuration(start={self.start_valid_date}, end={self.end_valid_date})"

    def _set_dates(self):
        if "_" in self._config_name:
            _, start_date, end_date = self._config_name.split("_")
            self.start_valid_date = start_date
            self.end_valid_date = end_date

    def get_config(self):
        """Load config from the config_path."""
        if self.dict_cfg is None:
            logger.debug("~ Config directory: '%s'", os.path.abspath(self._config_path))

            base_cfg = self._load_base_config()
            tables_cfg = self._load_tables_config()
            self.dict_cfg = OmegaConf.merge(base_cfg, tables_cfg)

        return self.dict_cfg

    def _load_base_config(self):
        config_dir = os.path.abspath(self._config_path)
        with hydra.initialize_config_dir(
            version_base=None, config_dir=config_dir, job_name="rtt_app"
        ):
            logger.debug("~ Loading '%s' @ '%s'", self._config_name, config_dir)
            return hydra.compose(config_name=self._config_name)

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
