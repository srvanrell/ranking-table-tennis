import csv
import os
from ranking_table_tennis import models
from ranking_table_tennis.models import cfg
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment
import pandas as pd
import pickle

import gspread
from oauth2client.service_account import ServiceAccountCredentials

__author__ = 'sebastian'


def get_tournament_sheetnames_by_date():
    tournaments_xlsx = cfg["io"]["data_folder"] + cfg["io"]["tournaments_filename"]
    wb = load_workbook(tournaments_xlsx, read_only=True)
    filter_key = cfg["sheetname"]["tournaments_key"]
    sheetnames = [s for s in wb.sheetnames if filter_key in s]
    namesdates = [(name, load_tournament_xlsx(name).date) for name in sheetnames]
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


def _wb_ws_to_save(filename, sheetname, overwrite=True):
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

    return wb, ws


def _bold_and_center(ws, to_bold, to_center):
    """Bold and center cells in given worksheet (ws)"""
    for colrow in to_bold:
        cell = ws[colrow]
        cell.font = Font(bold=True)
    for colrow in to_center:
        cell = ws[colrow]
        cell.alignment = Alignment(horizontal='center')


def save_sheet_workbook(filename, sheetname, headers, list_to_save, overwrite=True):
    wb, ws = _wb_ws_to_save(filename, sheetname, overwrite)

    if headers:
        ws.append(headers)
    
    for row in list_to_save:
        ws.append(row)

    if headers:
        for col in range(1, ws.max_column+1):
            cell = ws.cell(column=col, row=1)
            cell.font = Font(bold=True)

    wb.save(filename)


def _format_ranking_header_and_list(ranking, players):
    headers = [cfg["labels"][key] for key in ["PID", "Rating Points", "Bonus Points",
                                              "Active Player", "Category", "Player"]]
    list_to_save = [[e.pid, e.rating, e.bonus, cfg["activeplayer"][e.active],
                     e.category, players[e.pid].name] for e in ranking]
    list_to_save.sort(key=lambda l: l[1], reverse=True)

    return headers, list_to_save


def save_ranking_sheet(sheetname, ranking, players, overwrite=True, upload=False):
    if sheetname == cfg["sheetname"]["initial_ranking"]:
        filename = cfg["io"]["data_folder"] + cfg["io"]["tournaments_filename"]
    else:
        filename = cfg["io"]["data_folder"] + cfg["io"]["rankings_filename"]
        sheetname = sheetname.replace(cfg["sheetname"]["tournaments_key"], cfg["sheetname"]["rankings_key"])

    wb, ws = _wb_ws_to_save(filename, sheetname, overwrite)
    headers, list_to_save = _format_ranking_header_and_list(ranking, players)

    ws["A1"] = cfg["labels"]["Tournament name"]
    ws["B1"] = ranking.tournament_name
    ws["A2"] = cfg["labels"]["Date"]
    ws["B2"] = ranking.date
    ws["A3"] = cfg["labels"]["Location"]
    ws["B3"] = ranking.location
    ws["A4"] = cfg["labels"]["tid"]
    ws["B4"] = ranking.tid

    ws.append(headers)

    for row in list_to_save:
        ws.append(row)

    wb.save(filename)

    if upload:
        upload_ranking_sheet(cfg["sheetname"]["initial_ranking"], ranking, players)


def save_players_sheet(players, upload=False):
    headers = [cfg["labels"][key] for key in ["PID", "Player", "Association", "City",
                                              "Last Tournament", "Participations"]]
    list_to_save = sorted(players.to_list(), key=lambda l: l[1])

    save_sheet_workbook(cfg["io"]["data_folder"] + cfg["io"]["tournaments_filename"],
                        cfg["sheetname"]["players"],
                        headers,
                        list_to_save)
    if upload:
        upload_sheet(cfg["io"]["tournaments_spreadsheet_id"],
                     cfg["sheetname"]["players"],
                     headers,
                     list_to_save)


def load_players_sheet():
    return load_sheet_workbook(cfg["io"]["data_folder"] + cfg["io"]["tournaments_filename"],
                               cfg["sheetname"]["players"])


def load_ranking_sheet(sheetname):
    """Load a ranking from a xlsx sheet and return a Ranking object

    :param sheetname: tournament sheetname (will be replaced with ranking sheetname by default)
    Except that sheetname match with initial ranking name.

    :return: Ranking object
    """
    if sheetname == cfg["sheetname"]["initial_ranking"]:
        filename = cfg["io"]["data_folder"] + cfg["io"]["tournaments_filename"]
    else:
        filename = cfg["io"]["data_folder"] + cfg["io"]["rankings_filename"]
        sheetname = sheetname.replace(cfg["sheetname"]["tournaments_key"], cfg["sheetname"]["rankings_key"])

    raw_ranking = load_sheet_workbook(filename, sheetname, first_row=0)
    name = raw_ranking[0][1]
    date = str(raw_ranking[1][1])
    location = raw_ranking[2][1]
    tid = raw_ranking[3][1]
    ranking = models.Ranking(name, date, location, tid)
    ranking.load_list([[rr[0], rr[1], rr[2], rr[3] == cfg["activeplayer"][True], rr[4]] for rr in raw_ranking[5:]])

    return ranking


def load_tournament_csv(filename):
    """Load a tournament csv and return a Tournament object"""
    with open(filename, 'r') as incsv:
        reader = csv.reader(incsv)
        tournament_list = [row for row in reader]
        return load_tournament_list(tournament_list)


def load_tournament_xlsx(sheet_name):
    """Load a tournament xlsx sheet and return a Tournament object

    tournaments xlsx database is defined in config.yaml
    """
    tournaments_xlsx = cfg["io"]["data_folder"] + cfg["io"]["tournaments_filename"]

    return load_tournament_list(load_sheet_workbook(tournaments_xlsx, sheet_name, 0))


def load_tournament_list(tournament_list):
    """Load a tournament list sheet and return a Tournament object
    name = cell(B1)
    date = cell(B2)
    location = cell(B3)
    matches should be from sixth row containing:
    player1, player2, sets1, sets2, match_round, category
    """
    name = tournament_list[0][1]
    date = str(tournament_list[1][1])
    location = tournament_list[2][1]

    tournament = models.Tournament(name, date, location)

    # Reformated list of matches
    for player1, player2, sets1, sets2, round_match, category in tournament_list[5:]:
        # workaround to add extra bonus points from match list
        if int(sets1) >= 10 and int(sets2) >= 10:
            winner_name = cfg["aux"]["flag promotion"]
            loser_name = player2
        elif int(sets1) <= -10 and int(sets2) <= -10:
            winner_name = cfg["aux"]["flag bonus sanction"]
            loser_name = player2
        elif int(sets1) < 0 and int(sets2) < 0:
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


def _format_diff(diff):
    """Return a formated str that indicates +##, -## or ="""
    diff_str = str(diff)
    if diff > 0:
        diff_str = "+" + diff_str
    elif diff == 0:
        diff_str = "="
    return diff_str


def _publish_tournament_metadata(ws, ranking):
    ws["A1"] = cfg["labels"]["Tournament name"]
    ws["B1"] = ranking.tournament_name
    ws.merge_cells('B1:F1')
    ws["A2"] = cfg["labels"]["Date"]
    ws["B2"] = ranking.date
    ws.merge_cells('B2:F2')
    ws["A3"] = cfg["labels"]["Location"]
    ws["B3"] = ranking.location
    ws.merge_cells('B3:F3')


def publish_rating_sheet(sheetname, ranking, players, old_ranking, upload=False):
    """ Format a ranking to be published into a rating sheet
    """
    sheetname = sheetname.replace(cfg["sheetname"]["tournaments_key"], cfg["labels"]["Rating Points"])

    filename = cfg["io"]["data_folder"] + cfg["io"]["publish_filename"]
    filename = filename.replace("NN", "%d" % ranking.tid)

    # initialize the worksheet
    wb, ws = _wb_ws_to_save(filename, sheetname)

    # publish and format tournament metadata
    _publish_tournament_metadata(ws, ranking)

    # headers
    ws.append(cfg["labels"][key] for key in ["Category", "Rating Points", "Player", "City",
                                             "Association", "Active Player"])

    list_to_save = [[e.category, (e.rating, old_ranking[e.pid].rating, e.bonus), players[e.pid].name,
                     players[e.pid].city, players[e.pid].association, cfg["activeplayer"][e.active]] for e in ranking
                    if e.bonus > 0 or ranking.tid < 6]  # Exclude players that didn't played for a long time

    for row in list_to_save:
        # Do not publish ratings of fans category
        if row[0] == models.categories[-1]:
            # Bonus points are used for fans. Negative values keep fans category at the end
            row[1] = (row[1][2]-100000, -1)

    for row in sorted(list_to_save, key=lambda l: l[1][0], reverse=True):
        if row[1][0] < 0:
            row[1] = "NA"  # FIXME should read the value from config
        else:
            # Save difference with previous rating
            diff = row[1][0] - row[1][1]
            row[1] = "%d (%s)" % (row[1][0], _format_diff(diff))
        ws.append(row)

    to_bold = ["A1", "A2", "A3",
               "A4", "B4", "C4", "D4", "E4", "F4"]
    to_center = to_bold + ["B1", "B2", "B3"]

    _bold_and_center(ws, to_bold, to_center)

    wb.save(filename)

    if upload:
        load_and_upload_sheet(filename, sheetname, cfg["io"]["temporal_spreadsheet_id"])


def publish_championship_sheet(sheetname, ranking, players, old_ranking, upload=False):
    """ Format a ranking to be published into a rating sheet"""
    sheetname = sheetname.replace(cfg["sheetname"]["tournaments_key"], cfg["sheetname"]["championship_key"])

    filename = cfg["io"]["data_folder"] + cfg["io"]["publish_filename"]
    filename = filename.replace("NN", "%d" % ranking.tid)

    # initialize the worksheet
    wb, ws = _wb_ws_to_save(filename, sheetname)

    # publish and format tournament metadata
    _publish_tournament_metadata(ws, ranking)

    # headers
    ws.append(cfg["labels"][key] for key in ["Position", "Bonus Points", "Player", "City",
                                             "Association", "Active Player", "Category"])

    list_to_save = [[(e.bonus, old_ranking[e.pid].bonus), players[e.pid].name, players[e.pid].city,
                     players[e.pid].association, cfg["activeplayer"][e.active], e.category] for e in ranking
                    if e.bonus > 0 or ranking.tid < 6]  # Exclude players that didn't played for a long time
    sorted_list = sorted(list_to_save, key=lambda l: l[0][0], reverse=True)

    for i, row in enumerate(sorted_list):
        # Save difference with previous bonus
        diff = row[0][0] - row[0][1]
        row[0] = "%d (%s)" % (row[0][0], _format_diff(diff))
        ws.append([i + 1] + row)

    to_bold = ["A1", "A2", "A3",
               "A4", "B4", "C4", "D4", "E4", "F4", "G4"]
    to_center = to_bold + ["B1", "B2", "B3"]

    _bold_and_center(ws, to_bold, to_center)

    wb.save(filename)

    if upload:
        load_and_upload_sheet(filename, sheetname, cfg["io"]["temporal_spreadsheet_id"])


def publish_histories_sheet(ranking, players, tournament_sheetnames, upload=False):
    """ Format histories to be published into a sheet"""
    output_xlsx = cfg["io"]["data_folder"] + cfg["io"]["publish_filename"]
    output_xlsx = output_xlsx.replace("NN", "%d" % ranking.tid)

    histories = []
    for player in sorted(players, key=lambda l: l.name):
        if len(player.sorted_history) > 0:
            histories.append([player.name, "", "", ""])
            old_cat = ""
            for cat, tid, best_round in player.sorted_history:
                if cat == old_cat:
                    cat = ""
                else:
                    old_cat = cat
                histories.append(["", cat, best_round, " ".join(tournament_sheetnames[tid - 1].split()[1:])])

    save_sheet_workbook(output_xlsx,
                        cfg["sheetname"]["histories"],
                        [cfg["labels"][key] for key in ["Player", "Category", "Best Round", "Tournament"]],
                        histories)

    if upload:
        load_and_upload_sheet(output_xlsx, cfg["sheetname"]["histories"], cfg["io"]["temporal_spreadsheet_id"])


def publish_details_sheets(sheetname, ranking, upload=False):
    """ Copy details from log and output details of given tournament"""
    output_xlsx = cfg["io"]["data_folder"] + cfg["io"]["publish_filename"]
    output_xlsx = output_xlsx.replace("NN", "%d" % ranking.tid)

    log_xlsx = cfg["io"]["data_folder"] + cfg["io"]["log_filename"]

    # Saving points assigned in each match
    rating_details_sheetname = sheetname.replace(cfg["sheetname"]["tournaments_key"],
                                                 cfg["sheetname"]["rating_details_key"])
    rating_log_saved = load_sheet_workbook(log_xlsx, rating_details_sheetname, first_row=0)
    save_sheet_workbook(output_xlsx, rating_details_sheetname, rating_log_saved[0], rating_log_saved[1:])

    # Saving points assigned per best round reached and for participation
    bonus_details_sheetname = sheetname.replace(cfg["sheetname"]["tournaments_key"],
                                                cfg["sheetname"]["bonus_details_key"])
    bonus_log_saved = load_sheet_workbook(log_xlsx, bonus_details_sheetname, first_row=0)
    save_sheet_workbook(output_xlsx, bonus_details_sheetname, bonus_log_saved[0], bonus_log_saved[1:])

    if upload:
        load_and_upload_sheet(output_xlsx, rating_details_sheetname, cfg["io"]["temporal_spreadsheet_id"])
        load_and_upload_sheet(output_xlsx, bonus_details_sheetname, cfg["io"]["temporal_spreadsheet_id"])


def publish_statistics_sheet(sheetname, ranking, upload=False):
    """ Copy details from log and output details of given tournament"""
    output_xlsx = cfg["io"]["data_folder"] + cfg["io"]["publish_filename"]
    output_xlsx = output_xlsx.replace("NN", "%d" % ranking.tid)

    log_xlsx = cfg["io"]["data_folder"] + cfg["io"]["log_filename"]

    # Saving points assigned in each match
    statistics_sheetname = sheetname.replace(cfg["sheetname"]["tournaments_key"],
                                             cfg["sheetname"]["statistics_key"])
    statistics_log_saved = load_sheet_workbook(log_xlsx, statistics_sheetname, first_row=0)
    save_sheet_workbook(output_xlsx, statistics_sheetname, statistics_log_saved[0], statistics_log_saved[1:])

    if upload:
        load_and_upload_sheet(output_xlsx, statistics_sheetname, cfg["io"]["temporal_spreadsheet_id"])


def publish_masters_sheets(sheetname, ranking, upload=False):
    """ Copy details from log and output details of given tournament"""
    output_xlsx = cfg["io"]["data_folder"] + cfg["io"]["publish_filename"]
    output_xlsx = output_xlsx.replace("NN", "%d" % ranking.tid)

    log_xlsx = cfg["io"]["data_folder"] + cfg["io"]["log_filename"]

    for cat in models.categories:
        masters_sheetname = sheetname.replace(cfg["sheetname"]["tournaments_key"], cat)
        sheet_saved = load_sheet_workbook(log_xlsx, masters_sheetname, first_row=0)
        headers = [cfg["labels"]["Position"]] + sheet_saved[0]
        data = [[i + 1] + row for i, row in enumerate(sheet_saved[1:])]
        save_sheet_workbook(output_xlsx, masters_sheetname, headers, data)

        if upload:
            load_and_upload_sheet(output_xlsx, masters_sheetname, cfg["io"]["temporal_spreadsheet_id"])


def save_statistics(sheetname, tournament, ranking):
    # Testing statistics of tournament and ranking
    log_xlsx = cfg["io"]["data_folder"] + cfg["io"]["log_filename"]

    stats_sheetname = sheetname.replace(cfg["sheetname"]["tournaments_key"],
                                        cfg["sheetname"]["statistics_key"])

    t_stats = tournament.get_statistics()
    r_stats = ranking.get_statistics()

    labels = ['total'] + models.categories
    headers = ["tid", "description"] + labels
    data_to_save = [[ranking.tid, "tournament participation"] + [t_stats[k] for k in labels],
                    [ranking.tid, "ranked players"] + [r_stats['all'][k] for k in labels],
                    [ranking.tid, "ranked active"] + [r_stats['active'][k] for k in labels],
                    [ranking.tid, "ranked inactive"] + [r_stats['inactive'][k] for k in labels]]

    save_sheet_workbook(log_xlsx,
                        stats_sheetname,
                        headers,
                        data_to_save)


def _get_gc():
    # Drive authorization
    scope = ['https://spreadsheets.google.com/feeds']
    key_filename = models.user_config_path + "/key-for-gspread.json"
    gc = None
    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(key_filename, scope)
        gc = gspread.authorize(credentials)
    except FileNotFoundError:
        print("The .json key file has not been configured. Upload will fail.")
    except OSError:
        print("Connection failure. Upload will fail.")
    return gc


def _wb_ws_to_upload(spreadsheet_id, sheetname, num_rows, num_cols):
    print("<<<Saving\t", sheetname, "\tin\t", spreadsheet_id)
    wb, ws = None, None
    gc = _get_gc()
    # FIXME it should raise an exception to abort uploading
    if gc:
        wb = gc.open_by_key(spreadsheet_id)   

        # Overwrites an existing sheet or creates a new one
        if sheetname in [ws.title for ws in wb.worksheets()]:
            ws = wb.worksheet(sheetname)
            ws.resize(rows=num_rows, cols=num_cols)
        else:
            ws = wb.add_worksheet(title=sheetname, rows=num_rows, cols=num_cols)

    return wb, ws


def upload_sheet(spreadsheet_id, sheetname, headers, rows_to_save):
    """ Saves headers and rows_to_save into given sheet_name.
        If sheet_name does not exist, it will be created. """
    num_rows = len(rows_to_save) + 1  # +1 because of header
    num_cols = len(headers)

    wb, ws = _wb_ws_to_upload(spreadsheet_id, sheetname, num_rows, num_cols)
    if wb is None and ws is None:
        print("Updating has failed. Skipping...")
        return

    # Concatenation of all cells values to be updated in batch mode
    cell_list = ws.range("A1:" + gspread.utils.rowcol_to_a1(row=num_rows, col=num_cols))
    for i, value in enumerate(headers + [v for row in rows_to_save for v in row]):
        cell_list[i].value = value

    ws.update_cells(cell_list)


# FIXME It should allow uploading more than initial ranking
def upload_ranking_sheet(sheetname, ranking, players):
    """ Saves ranking into given sheet_name.
        If sheet_name does not exist, it will be created. """
    if sheetname == cfg["sheetname"]["initial_ranking"]:
        spreadsheet_id = cfg["io"]["tournaments_spreadsheet_id"]
        # else:
        #     spreadsheet_id = cfg["io"]["not_existent_spreadsheet_id"]
        #     sheetname = sheetname.replace(cfg["sheetname"]["tournaments_key"], cfg["sheetname"]["rankings_key"])

        headers, list_to_save = _format_ranking_header_and_list(ranking, players)

        num_cols = len(headers)
        num_rows = len(list_to_save) + 1 + 4  # +1 because of header + 4 because of tournament metadata

        wb, ws = _wb_ws_to_upload(spreadsheet_id, sheetname, num_rows, num_cols)
        if wb is None and ws is None:
            print("Updating has failed. Skipping...")
            return

        ws.update_acell("A1", cfg["labels"]["Tournament name"])
        ws.update_acell("B1", ranking.tournament_name)
        ws.update_acell("A2", cfg["labels"]["Date"])
        ws.update_acell("B2", ranking.date)
        ws.update_acell("A3", cfg["labels"]["Location"])
        ws.update_acell("B3", ranking.location)
        ws.update_acell("A4", cfg["labels"]["tid"])
        ws.update_acell("B4", ranking.tid)

        # Concatenation of all cells values to be updated in batch mode
        cell_list = ws.range("A5:" + gspread.utils.rowcol_to_a1(row=num_rows, col=num_cols))
        for i, value in enumerate(headers + [v for row in list_to_save for v in row]):
            cell_list[i].value = value

        ws.update_cells(cell_list)


def load_and_upload_sheet(filename, sheetname, spreadsheet_id):
    raw_sheet = load_sheet_workbook(filename, sheetname, first_row=0)
    headers = raw_sheet[0]
    list_to_save = raw_sheet[1:]

    upload_sheet(spreadsheet_id, sheetname, headers, list_to_save)


def create_n_tour_sheet(spreadsheet_id, n_tour):
    """
    Create sheet corresponding to n_tour tournament by duplication of the first-tournament sheet.
    A new sheeet is created in given spreadsheet_id as follows:
    1- first-tournament sheet is duplicated
    2- Two replacements are performed in the new sheet, considering n_tour.
       For example, if n_tour=4, value of A1 cell and sheet title will change 'Tournament 01'->'Tournament 04'
    :param spreadsheet_id: spreadsheet where duplication will be performed
    :param n_tour: tournament to create
    :return: None
    """
    first_key = cfg["labels"]["Tournament"] + " 01"
    replacement_key = "%s %02d" % (cfg["labels"]["Tournament"], n_tour)
    gc = _get_gc()
    if gc:
        wb = gc.open_by_key(spreadsheet_id)
        sheetname_listed = [ws.title for ws in wb.worksheets() if first_key in ws.title]
        if sheetname_listed:
            sheetname = sheetname_listed[0]
            new_sheetname = sheetname.replace(first_key, replacement_key)
            if new_sheetname in [ws.title for ws in wb.worksheets()]:
                out_ws = wb.worksheet(new_sheetname)
                wb.del_worksheet(out_ws)
            ws = wb.worksheet(sheetname)
            dup_ws = wb.duplicate_sheet(ws.id, new_sheet_name=new_sheetname)
            dup_cell_value = dup_ws.acell('A1', value_render_option='FORMULA').value
            dup_ws.update_acell('A1', dup_cell_value.replace(first_key, replacement_key))
            print("<<<Creating\t", new_sheetname, "\tfrom\t", sheetname, "\tin\t", spreadsheet_id)
        else:
            print("FAILED TO DUPLICATE\t", first_key, "\t not exist in\t", spreadsheet_id)


def publish_to_web(ranking, show_on_web=False):
    if show_on_web:
        for spreadsheet_id in cfg["io"]["published_on_web_spreadsheets_id"]:
            create_n_tour_sheet(spreadsheet_id, ranking.tid)


def load_temp_players_ranking():
    """returns players_temp, ranking_temp"""
    # Loading temp ranking and players. It shuould be deleted after a successful preprocessing
    players_temp_file = cfg["io"]["players_temp_file"]
    ranking_temp_file = cfg["io"]["ranking_temp_file"]
    if os.path.exists(players_temp_file):
        with open(players_temp_file, 'rb') as f:
            print(">Reading\tTemp player list\tResume preprocessing from", players_temp_file)
            players_temp = pickle.load(f)
    else:
        players_temp = models.PlayersList()
    if os.path.exists(ranking_temp_file):
        with open(ranking_temp_file, 'rb') as f:
            print(">Reading\tTemp ranking list\tResume preprocessing from", ranking_temp_file)
            ranking_temp = pickle.load(f)
    else:
        ranking_temp = models.Ranking()

    return players_temp, ranking_temp


def save_temp_players_ranking(players_temp, ranking_temp):
    """returns players_temp, ranking_temp"""
    # Loading temp ranking and players. It shuould be deleted after a successful preprocessing
    players_temp_file = cfg["io"]["players_temp_file"]
    ranking_temp_file = cfg["io"]["ranking_temp_file"]
    print("<Saving\tTemps to resume preprocessing (if necessary)", ranking_temp_file, players_temp_file)
    with open(players_temp_file, 'wb') as ptf, open(ranking_temp_file, 'wb') as rtf:
        # Pickle the 'data' dictionary using the highest protocol available.
        pickle.dump(players_temp, ptf, pickle.HIGHEST_PROTOCOL)
        pickle.dump(ranking_temp, rtf, pickle.HIGHEST_PROTOCOL)


def remove_temp_players_ranking():
    players_temp_file = cfg["io"]["players_temp_file"]
    ranking_temp_file = cfg["io"]["ranking_temp_file"]
    print("Removing temp files created to resume preprocessing", players_temp_file, ranking_temp_file)
    if os.path.exists(players_temp_file):
        os.remove(players_temp_file)
    if os.path.exists(ranking_temp_file):
        os.remove(ranking_temp_file)


def save_masters_cup():
    """
    Compute and save masters cup up into log
    :return: None
    """
    n_tournaments = cfg["aux"]["masters N tournaments to consider"]
    n_classified = cfg["aux"]["masters N classified to list"]
    log_xlsx = cfg["io"]["data_folder"] + cfg["io"]["log_filename"]

    # Labels of columns, just to simplify notation
    player_col = cfg["labels"]["Player"]
    category_col = cfg["labels"]["Category"]
    points_col = cfg["labels"]["Bonus Points"]
    participations_col = cfg["labels"]["Participations"]

    # Will compute all rankings from the beginning by default
    tournament_sheetnames = get_tournament_sheetnames_by_date()
    tids = range(1, len(tournament_sheetnames)+1)

    df = pd.DataFrame()

    for tid in tids:
        tournament_sheetname = tournament_sheetnames[tid - 1]
        bonus_log = load_sheet_workbook(log_xlsx,
                                        tournament_sheetname.replace(cfg["sheetname"]["tournaments_key"],
                                                                     cfg["sheetname"]["bonus_details_key"]),
                                        first_row=1)
        temp_df = pd.DataFrame([[tid] + j for j in bonus_log],
                               columns=[cfg["labels"][key] for key in ["Tournament", "Player", "Bonus Points",
                                                                       "Best Round", "Category"]]
                               )
        temp_df = temp_df[temp_df[category_col] != ""]
        df = df.append(temp_df, ignore_index=True)

        pl_cat_best_n_tour = df[[player_col, category_col, points_col]]
        if tid > 1:
            pl_cat_best_n_tour = df.groupby([player_col, category_col])[points_col].nlargest(n_tournaments)
        pl_cat_cumul = pl_cat_best_n_tour.groupby([player_col, category_col]).sum().reset_index()
        pl_cat_count = df.groupby([player_col, category_col])[points_col].count().reset_index().rename(
            columns={points_col: participations_col})

        pl_cat = pd.merge(pl_cat_cumul, pl_cat_count).sort_values(points_col, ascending=False)

        # sort_by_point = pl_cat.groupby(category_col, as_index=False).apply(
        #     lambda x: pd.DataFrame.nlargest(x, n=n_classified, columns=points_col))
        # sort_by_count = pl_cat.groupby(category_col, as_index=False).apply(
        #     lambda x: pd.DataFrame.nlargest(x, n=n_classified, columns=participations_col))
        sort_by_point = pl_cat.groupby(category_col, as_index=False).apply(
            lambda x: x.sort_values([points_col, participations_col], ascending=(False, True)))

        filename = cfg["io"]["data_folder"] + cfg["io"]["log_filename"]
        tournament_sheetname = tournament_sheetnames[tid - 1]

        for cat in models.categories:
            df_cat_by_point = sort_by_point[sort_by_point[category_col] == cat]
            df_cat_by_point = df_cat_by_point.drop(category_col, axis=1)

            save_sheet_workbook(filename,
                                tournament_sheetname.replace(cfg["sheetname"]["tournaments_key"], cat),
                                df_cat_by_point.columns.tolist(),
                                df_cat_by_point.values.tolist())
