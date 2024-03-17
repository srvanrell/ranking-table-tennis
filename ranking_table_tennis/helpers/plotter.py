# From https://plotly.com/python/line-charts/
import logging
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ranking_table_tennis.configs import ConfigManager

logger = logging.getLogger(__name__)

RENAMER = {
    "tid": "ID Torneo",
    "rating": "Nivel de juego",
    "name": "Nombre",
    "cum_points_cat_1": "Puntos de campeonato",
    "cum_points_cat_2": "Puntos de campeonato",
    "cum_points_cat_3": "Puntos de campeonato",
}


def get_df_complete(max_tid):
    cfg = ConfigManager().current_config
    year = cfg.year
    max_tid_num = int(max_tid[-2:])

    tids = [f"S{yr}T{tt:02d}" for yr in range(year, year + 1) for tt in range(1, max_tid_num + 1)]
    dfs_to_concat = []
    for tid in tids:
        xlsx_filename = os.path.join(cfg.io.data_folder, f"raw_ranking_{tid}.xlsx")
        logger.debug("> Reading raw ranking @ '%s'", xlsx_filename)
        if not os.path.exists(xlsx_filename):
            logger.warning("> Not found raw ranking @ '%s'", xlsx_filename)
            continue
        df_ = pd.read_excel(xlsx_filename)
        dfs_to_concat.append(df_)

    df_complete = pd.concat(dfs_to_concat, ignore_index=True)

    return df_complete


def plot_ratings(tid):
    """Plot and save rating interactive figure"""
    df_complete = get_df_complete(tid)
    # Mascara para filtrado
    mask_active_players_rating = df_complete.iloc[:, 13 : 13 + 4].sum(axis="columns") > 0
    df = df_complete.loc[mask_active_players_rating]

    fig = px.line(
        df,
        x="tid",
        y="rating",
        color="name",
        symbol="name",
        labels=RENAMER,
        category_orders={
            "tid": sorted(df.tid.unique()),
            "name": sorted(df.name.unique()),
        },
        height=400,
        width=400,
    )

    # hide and lock down axes
    # fig.update_xaxes(visible=True, fixedrange=True)
    # fig.update_yaxes(visible=True, fixedrange=True)

    # strip down the rest of the plot
    fig.update_layout(
        showlegend=False,
        plot_bgcolor="white",
        margin=dict(t=10, l=10, b=10, r=10),
        legend=dict(title=None),
        updatemenus=[
            {
                "type": "buttons",
                "x": 0.25,
                "xanchor": "center",
                "y": 0.95,
                "yanchor": "top",
                "borderwidth": 0,
                "direction": "right",
                "buttons": [
                    {
                        "label": "≡",
                        "method": "relayout",
                        "args": ["showlegend", False],
                        "args2": ["showlegend", True],  # NEW attribute !
                    },
                    {
                        "label": "<>",
                        "method": "relayout",
                        "args": ["width", 400],
                        "args2": ["width", 1000],  # NEW attribute !
                    },
                ],
            }
        ],
    )

    # Agrega corte por categoría
    for threshold in [700, 1300]:
        fig.add_trace(
            go.Scatter(
                x=[df["tid"].min(), df["tid"].max()],
                y=[threshold, threshold],
                mode="lines",
                line=go.scatter.Line(color="gray", dash="dot"),
                showlegend=False,
                text="Corte de categorías",
            )
        )

    # fig.show(config=dict(displayModeBar=False))
    # fig.show()

    # Saves a html doc that you can copy paste
    cfg = ConfigManager().current_config
    html_filename = os.path.join(cfg.io.data_folder, f"{tid}/rating{cfg.year}.html")
    logger.info("< Saving figure @ '%s'", html_filename)
    fig.write_html(html_filename, full_html=False, include_plotlyjs="cdn")


def plot_championships(tid):
    """Plot and save interactive figures of all championships."""
    df_complete = get_df_complete(tid)
    # Mascaras para filtrado
    mask_active_players_cat1 = df_complete.iloc[:, 13 : 13 + 1].sum(axis="columns") > 0
    mask_active_players_cat2 = df_complete.iloc[:, 14 : 14 + 1].sum(axis="columns") > 0
    mask_active_players_cat3 = df_complete.iloc[:, 15 : 15 + 1].sum(axis="columns") > 0

    # === Figura campeonato cat# ===
    for mask, col, name in zip(
        [mask_active_players_cat1, mask_active_players_cat2, mask_active_players_cat3],
        ["cum_points_cat_1", "cum_points_cat_2", "cum_points_cat_3"],
        ["Primera", "Segunda", "Tercera"],
    ):

        df = df_complete.loc[mask]

        fig = px.line(
            df,
            x="tid",
            y=col,
            color="name",
            symbol="name",
            labels=RENAMER,
            category_orders={
                "tid": sorted(df.tid.unique()),
                "name": sorted(df.name.unique()),
            },
            height=400,
            width=400,
        )

        # hide and lock down axes
        # fig.update_xaxes(visible=True, fixedrange=True)
        # fig.update_yaxes(visible=True, fixedrange=True)

        # strip down the rest of the plot
        fig.update_layout(
            showlegend=False,
            plot_bgcolor="white",
            margin=dict(t=10, l=10, b=10, r=10),
            legend=dict(title=None),
            updatemenus=[
                {
                    "type": "buttons",
                    "x": 0.25,
                    "xanchor": "center",
                    "y": 0.95,
                    "yanchor": "top",
                    "borderwidth": 0,
                    "direction": "right",
                    "buttons": [
                        {
                            "label": "≡",
                            "method": "relayout",
                            "args": ["showlegend", False],
                            "args2": ["showlegend", True],  # NEW attribute !
                        },
                        {
                            "label": "<>",
                            "method": "relayout",
                            "args": ["width", 400],
                            "args2": ["width", 1000],  # NEW attribute !
                        },
                    ],
                }
            ],
        )

        # fig.show(config=dict(displayModeBar=False))
        # fig.show()

        # Saves a html doc that you can copy paste
        cfg = ConfigManager().current_config
        html_filename = os.path.join(cfg.io.data_folder, f"{tid}/championship{cfg.year}{name}.html")
        logger.info("< Saving figure @ '%s'", html_filename)
        fig.write_html(html_filename, full_html=False, include_plotlyjs="cdn")
