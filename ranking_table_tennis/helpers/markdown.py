import logging
import os

import matplotlib.pyplot as plt
import pandas as pd

from ranking_table_tennis.configs import ConfigManager

logger = logging.getLogger(__name__)


def publish_sheet_as_markdown(df, headers, sheet_name, tid, index=False):
    cfg = ConfigManager().current_config
    # Create folder to publish markdowns
    os.makedirs(f"{cfg.io.data_folder}{tid}", exist_ok=True)
    markdown_filename = f"{cfg.io.data_folder}{tid}/{sheet_name.replace(' ', '_')}.md"
    logger.info("< Saving '%s' @ '%s'", sheet_name, markdown_filename)
    df.to_markdown(
        markdown_filename, index=index, headers=headers, stralign="center", numalign="center"
    )


def publish_stat_plot(stats_df, headers, tid, fig_filename):
    cfg = ConfigManager().current_config
    stats_df.columns = headers
    stats_plot = (
        stats_df.copy()
        .set_index(pd.Index(stats_df.index.str.slice(start=5)))
        .plot(
            title=f"{fig_filename.replace(cfg.sheetname.statistics_key, '')} {tid[1:-3]}",
            kind="bar",
            xlabel=cfg.labels.tid,
            ylabel=cfg.sheetname.players,
            stacked=True,
            rot=0,
        )
    )
    for container in stats_plot.containers:
        stats_plot.bar_label(container, label_type="center")
    plt.tight_layout()
    stats_plot.get_figure().savefig(
        f"{cfg.io.data_folder}{tid}/{fig_filename.replace(' ', '_')}.png"
    )


def publish_tournament_metadata_as_markdown(tid, tournament_tid: pd.DataFrame) -> None:
    cfg = ConfigManager().current_config
    df_metadata = pd.DataFrame(
        {
            cfg.labels.Tournament_name: [tournament_tid["tournament_name"].iloc[0]],
            cfg.labels.Date: [tournament_tid["date"].iloc[0].strftime("%Y %m %d")],
            cfg.labels.Location: [tournament_tid["location"].iloc[0]],
        }
    )
    publish_sheet_as_markdown(
        df_metadata,
        df_metadata.columns,
        cfg.io.md.tournament_metadata,
        tid,
    )
