import os

import matplotlib.pyplot as plt
import pandas as pd

from ranking_table_tennis.configs import cfg


def publish_sheet_as_markdown(df, headers, sheet_name, tid, index=False):
    # Create folder to publish markdowns
    os.makedirs(f"{cfg.io.data_folder}{tid}", exist_ok=True)
    markdown_filename = f"{cfg.io.data_folder}{tid}/{sheet_name.replace(' ', '_')}.md"
    print("<<<Saving", sheet_name, "in", markdown_filename, sep="\t")
    df.to_markdown(
        markdown_filename, index=index, headers=headers, stralign="center", numalign="center"
    )


def publish_stat_plot(stats_df, headers, tid, fig_filename):
    stats_df.columns = headers
    stats_plot = stats_df.plot(
        title=fig_filename.replace(cfg.sheetname.statistics_key, ""),
        kind="bar",
        xlabel=cfg.labels.tid,
        ylabel=cfg.sheetname.players,
        stacked=True,
        rot=0,
    )
    for container in stats_plot.containers:
        stats_plot.bar_label(container, label_type="center")
    plt.tight_layout()
    stats_plot.get_figure().savefig(
        f"{cfg.io.data_folder}{tid}/{fig_filename.replace(' ', '_')}.png"
    )


def publish_tournament_metadata_as_markdown(tid, tournament_tid: pd.DataFrame) -> None:
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
        cfg.io.tournament_metadata_md,
        tid,
    )
