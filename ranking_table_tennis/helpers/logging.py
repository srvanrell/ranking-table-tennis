import logging
import logging.config
import os

import yaml

root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

with open(os.path.join(root, "config/logging.yaml"), "r") as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)

logger = logging.getLogger("ranking_table_tennis")
