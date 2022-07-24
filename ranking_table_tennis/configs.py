import os
import shutil

import pandas as pd
from omegaconf import OmegaConf

# Loads some names from config.yaml
user_config_path = os.path.join("data_rtt", "config")
print(f"Working directory: {os.path.abspath(os.path.curdir)}")
print(f"Config directory: {os.path.abspath(user_config_path)}")

if not os.path.exists(user_config_path):
    shutil.copytree(os.path.dirname(__file__) + "/config", user_config_path)

base_cfg = OmegaConf.load(user_config_path + "/config.yaml")

if not os.path.exists(base_cfg.io.data_folder):
    os.mkdir(base_cfg.io.data_folder)

# Tables to assign points

# difference, points to winner, points to loser
expected_result_table = pd.read_csv(user_config_path + "/expected_result.csv")

# negative difference, points to winner, points to loser
unexpected_result_table = pd.read_csv(user_config_path + "/unexpected_result.csv")

# points to be assigned by round and by participation
raw_points_per_round_table = pd.read_csv(user_config_path + "/points_per_round.csv")
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
        "best_rounds_points": raw_points_per_round_table.drop(columns="priority").to_dict(),
        "best_rounds_priority": best_rounds_priority.to_dict(),
    }
)

cfg = OmegaConf.merge(base_cfg, extra_cfg)
