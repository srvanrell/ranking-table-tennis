import logging
import os

from ranking_table_tennis.helpers.gspread import days_since_last_update

logger = logging.getLogger(__name__)


def no_updates_stop_workflow(spreadsheet_id, max_days_since_last_update=1):
    """If spreasheet_id has not been modified recently GITHUB_OUTPUT env var will stop workflow"""

    days_since_update = days_since_last_update(spreadsheet_id)
    stop_workflow = days_since_update > max_days_since_last_update
    logger.info(
        "%s days since last update. Should stop workflow? %s", days_since_update, stop_workflow
    )

    GITHUB_OUTPUT_VAR_NAME = "GITHUB_OUTPUT"
    var_value = f"stop_workflow={str(stop_workflow).lower()}"  # true or false

    logger.debug("Set env var '%s': '%s'", GITHUB_OUTPUT_VAR_NAME, var_value)
    os.environ[GITHUB_OUTPUT_VAR_NAME] = var_value

    if stop_workflow:
        exit(0)
