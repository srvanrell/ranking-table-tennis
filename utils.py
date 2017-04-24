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
    print(">Reading\t", sheetname, "\tfrom\t", filename)
    wb = load_workbook(filename, read_only=True)
    ws = wb.get_sheet_by_name(sheetname)

    ws.calculate_dimension(force=True)

    list_to_return = []
    for row in ws.rows:
        aux_row = []
        empty_row = True
        for cell in row:
            if cell.value is None:
                aux_row.append("")
            else:
                empty_row = False
                aux_row.append(cell.value)
        if not empty_row:
            list_to_return.append(aux_row[:ws.max_column])
    return list_to_return[first_row:]


def save_sheet_workbook(filename, sheetname, headers, list_to_save, overwrite=False):
    print("<<<Saving\t", sheetname, "\tin\t", filename)
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
    
    for row in list_to_save:
        ws.append(row)

    for col in range(1, ws.max_column+1):
        cell = ws.cell(column=col, row=1)
        cell.font = Font(bold=True)

    wb.save(filename)


def save_ranking_sheet(filename, sheetname, ranking, players, overwrite=False):
    print("<<<Saving\t", sheetname, "\tin\t", filename)
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
    ws.merge_cells('B1:E1')
    ws["A2"] = cfg["labels"]["Date"]
    ws["B2"] = ranking.date
    ws.merge_cells('B2:E2')
    ws["A3"] = cfg["labels"]["Location"]
    ws["B3"] = ranking.location
    ws.merge_cells('B3:E3')

    ws.append(cfg["labels"][key] for key in ["PID", "Rating Points", "Bonus Points",
                                             "Active Player", "Category"])
    #TODO add name but don't read it on loading
    list_to_save = [[e.pid, e.rating, e.bonus, cfg["activeplayer"][e.active],
                     e.category] for e in ranking]

    for row in sorted(list_to_save, key=lambda l: l[1], reverse=True):
        ws.append(row)

    wb.save(filename)


def load_ranking_sheet(filename, sheetname):
    """Load a ranking in a xlxs sheet and return a Ranking object"""
    # TODO check if date is being read properly
    raw_ranking = load_sheet_workbook(filename, sheetname, first_row=0)
    ranking = models.Ranking(raw_ranking[0][1], raw_ranking[1][1], raw_ranking[2][1])
    ranking.load_list([[rr[0], rr[1], rr[2], rr[3] == cfg["activeplayer"][True], rr[4]] for rr in raw_ranking[4:]])

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
            winner_name = cfg["aux"]["flag add bonus"]
            loser_name = player2
        elif int(sets1) > int(sets2):
            winner_name = player1
            loser_name = player2
        elif int(sets1) < int(sets2):
            winner_name = player2
            loser_name = player1
        else:
            print("Failed to process matches, a tie was found between %s and %s" % (player1, player2))
            break
        tournament.add_match(winner_name, loser_name, round_match, category)

    return tournament


def publish_rating_sheet(filename, sheetname, ranking, players, overwrite=False):
    """ Format a ranking to be published into a rating sheet"""
    print("<<<Saving\t", sheetname, "\tin\t", filename)
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
    ws.merge_cells('B1:F1')
    ws["A2"] = cfg["labels"]["Date"]
    ws["B2"] = ranking.date
    ws.merge_cells('B2:F2')
    ws["A3"] = cfg["labels"]["Location"]
    ws["B3"] = ranking.location
    ws.merge_cells('B3:F3')

    ws.append(cfg["labels"][key] for key in ["Rating Points", "Player", "Association",
                                             "City", "Active Player", "Category"])

    list_to_save = [[e.rating, players[e.pid].name, players[e.pid].association,
                     players[e.pid].city, cfg["activeplayer"][e.active], e.category] for e in ranking]

    for row in sorted(list_to_save, key=lambda l: (-l[0]), reverse=False):   # to use Jugador activo
        ws.append(row)

    to_bold = ["A1", "A2", "A3",
               "A4", "B4", "C4", "D4", "E4", "F4"]
    to_center = to_bold + ["B1", "B2", "B3"]

    for colrow in to_bold:
        cell = ws[colrow]
        cell.font = Font(bold=True)
    for colrow in to_center:
        cell = ws[colrow]
        cell.alignment = Alignment(horizontal='center')

    wb.save(filename)


def publish_championship_sheet(filename, sheetname, ranking, players, overwrite=False):
    """ Format a ranking to be published into a rating sheet"""
    print("<<<Saving\t", sheetname, "\tin\t", filename)
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

    ws.append(cfg["labels"][key] for key in ["Position", "Bonus Points", "Player", "Association",
                                             "City", "Active Player", "Category"])

    list_to_save = [[e.bonus, players[e.pid].name, players[e.pid].association,
                     players[e.pid].city, cfg["activeplayer"][e.active], e.category] for e in ranking]
    sorted_list = sorted(list_to_save, key=lambda l: l[0], reverse=True)

    for i, row in enumerate(sorted_list):
        ws.append([i + 1] + row)

    to_bold = ["A1", "A2", "A3",
               "A4", "B4", "C4", "D4", "E4", "F4", "G4"]
    to_center = to_bold + ["B1", "B2", "B3"]

    for colrow in to_bold:
        cell = ws[colrow]
        cell.font = Font(bold=True)
    for colrow in to_center:
        cell = ws[colrow]
        cell.alignment = Alignment(horizontal='center')

    wb.save(filename)


def publish_histories_sheet(filename, sheetname, players, tournament_sheetnames, overwrite=False):
        """ Format histories to be published into a sheet"""
        print("<<<Saving\t", sheetname, "\tin\t", filename)
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

        histories = []
        for player in sorted(players, key=lambda l: l.name):
            histories.append([player.name, "", "", ""])
            old_cat = ""
            for cat, tid, best_round in player.sorted_history:
                if cat == old_cat:
                    cat = ""
                else:
                    old_cat = cat
                histories.append(["", cat, best_round, " ".join(tournament_sheetnames[tid - 1].split()[1:])])

        to_bold = ["A1", "A2", "A3", "A4"]
        to_center = to_bold

        for colrow in to_bold:
            cell = ws[colrow]
            cell.font = Font(bold=True)
        for colrow in to_center:
            cell = ws[colrow]
            cell.alignment = Alignment(horizontal='center')

        save_sheet_workbook(filename, sheetname,
                            [cfg["labels"][key] for key in ["Player", "Category", "Best Round", "Tournament"]],
                            histories,
                            overwrite)

