import csv
import models
import os
import yaml
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment

__author__ = 'sebastian'

# Loads some names from config.yaml
with open("config.yaml", 'r') as cfgyaml:
    try:
        cfg = yaml.load(cfgyaml)
    except yaml.YAMLError as exc:
        print(exc)


def get_sheetnames_by_date(filename, filter_key=""):
    wb = load_workbook(filename, read_only=True)
    sheetnames = [s for s in wb.sheetnames if filter_key in s]
    namesdates = [(name, load_tournament_xlsx(filename, name).date) for name in sheetnames]
    namesdates.sort(key=lambda p: p[1])

    return [name for name, date in namesdates]


def load_sheet_workbook(filename, sheetname, first_row=1):
    wb = load_workbook(filename, read_only=True)
    ws = wb.get_sheet_by_name(sheetname)

    ws.calculate_dimension(force=True)
    # print(ws.dimensions)

    list_to_return = []
    max_column = 0
    for row in ws.rows:
        aux_row = []
        empty_row = True
        for cell in row:
            if cell.column:
                if cell.column > max_column:
                    max_column = cell.column
            if cell.value is None:
                aux_row.append("")
                # print(cell.column)
            else:
                empty_row = False
                aux_row.append(cell.value)
        if not empty_row:
            list_to_return.append(aux_row[:max_column])
    return list_to_return[first_row:]


def save_sheet_workbook(filename, sheetname, headers, list_to_save, overwrite=False):
    if os.path.isfile(filename):
        wb = load_workbook(filename)
        if overwrite and sheetname in wb:
            wb.remove_sheet(wb.get_sheet_by_name(sheetname))
        if sheetname in wb:
            ws = wb.get_sheet_by_name(sheetname)
        else:
            ws = wb.create_sheet()
    else:
        wb = Workbook()
        ws = wb.active

    ws.title = sheetname

    ws.append(headers)
    for col in range(1, ws.max_column+1):
        cell = ws.cell(column=col, row=1)
        cell.font = Font(bold=True)

    for row in list_to_save:
        ws.append(row)

    # # Automatically adjust width of columns to its content
    # # TODO add width adaptation, now it breaks on datetime
    # dims = {}
    # for row in ws.rows:
    #     for cell in row:
    #         if cell.value:
    #             dims[cell.column] = max((dims.get(cell.column, 0), len(str(cell.value))))
    # for col, value in dims.items():
    #     ws.column_dimensions[col].width = value

    wb.save(filename)


def save_ranking_sheet(filename, sheetname, ranking, players, overwrite=False):
    if os.path.isfile(filename):
        wb = load_workbook(filename)
        if overwrite and sheetname in wb:
            wb.remove_sheet(wb.get_sheet_by_name(sheetname))
        if sheetname in wb:
            ws = wb.get_sheet_by_name(sheetname)
        else:
            ws = wb.create_sheet()
    else:
        wb = Workbook()
        ws = wb.active

    ws.title = sheetname

    ws["A1"] = cfg["labels"]["Tournament name"]
    ws["B1"] = ranking.tournament_name
    ws.merge_cells('B1:G1')
    ws["A2"] = cfg["labels"]["Date"]
    ws["B2"] = ranking.date
    ws.merge_cells('B2:G2')
    ws["A3"] = cfg["labels"]["Location"]
    ws["B3"] = ranking.location
    ws.merge_cells('B3:G3')

    ws.append(cfg["labels"][key] for key in ["PID", "Total Points", "Rating Points", "Bonus Points",
                                             "Player", "Association", "City", "Active Player"])

    to_bold = ["A1", "A2", "A3",
               "A4", "B4", "C4", "D4", "E4", "F4", "G4", "H4"]
    to_center = to_bold + ["B1", "B2", "B3"]

    for colrow in to_bold:
        cell = ws.cell(colrow)
        cell.font = Font(bold=True)
    for colrow in to_center:
        cell = ws.cell(colrow)
        cell.alignment = Alignment(horizontal='center')

    list_to_save = [[e.pid, e.get_total(), e.rating, e.bonus, players[e.pid].name, players[e.pid].association,
                     players[e.pid].city, str(ranking.tid - players[e.pid].last_tournament < 2)] for e in ranking]

    # for row in sorted(list_to_save, key=lambda l: (l[-1], l[1]), reverse=True):  # to use Jugador activo
    for row in sorted(list_to_save, key=lambda l: l[1], reverse=True):
        ws.append(row)

    wb.save(filename)


def load_ranking_sheet(filename, sheetname):
    """Load a ranking in a xlxs sheet and return a Ranking object"""
    # TODO check if date is being read properly
    raw_ranking = load_sheet_workbook(filename, sheetname, first_row=0)
    ranking = models.Ranking(raw_ranking[0][1], raw_ranking[1][1], raw_ranking[2][1])
    ranking.load_list([[rr[0], rr[2], rr[3]] for rr in raw_ranking[4:]])
    return ranking


def load_tournament_csv(filename):
    """Load a tournament csv and return a Tournament object"""
    with open(filename, 'r') as incsv:
        reader = csv.reader(incsv)
        tournament_list = [row for row in reader]
        return load_tournament_list(tournament_list)


def load_tournament_xlsx(filename, sheet_name):
    """Load a tournament xlsx sheet and return a Tournament object"""
    return load_tournament_list(load_sheet_workbook(filename, sheet_name, 0))


def load_tournament_list(tournament_list):
    """Load a tournament list sheet and return a Tournament object
    name = cell(B1)
    date = cell(B2)
    location = cell(B3)
    matches should be from sixth row containing:
    player1, player2, sets1, sets2, match_round, category
    """
    name = tournament_list[0][1]
    date = tournament_list[1][1]
    location = tournament_list[2][1]

    tournament = models.Tournament(name, date, location)

    # Reformated list of matches
    for player1, player2, sets1, sets2, round_match, category in tournament_list[5:]:
        # workaround to add extra bonus points from match list
        if int(sets1) < 0 and int(sets2) < 0:
            winner_name = "to_add_bonus_points"
            loser_name = player2
        elif int(sets1) > int(sets2):
            winner_name = player1
            loser_name = player2
        elif int(sets1) < int(sets2):
            winner_name = player2
            loser_name = player1
        else:
            print("Error al procesar los partidos, se encontró un empate entre %s y %s" % (player1, player2))
            break
        tournament.add_match(winner_name, loser_name, round_match, category)

    return tournament
