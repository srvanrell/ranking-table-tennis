__author__ = 'sebastian'

import csv

def save_csv(filename, headers, list_to_save):
    with open(filename, 'w') as outcsv:
        writer = csv.writer(outcsv)
        writer.writerow(headers)
        writer.writerows(list_to_save)


def load_csv(filename):
    with open(filename, 'r') as incsv:
        reader = csv.reader(incsv)
        aux = [row for row in reader]
        header = aux[0]
        list_to_return = []
        for row in aux[1:]:
            aux_row = []
            for item in row:
                if item.isdigit():
                    aux_row.append(int(item))
                else:
                    aux_row.append(item)
            list_to_return.append(aux_row)
        return list_to_return

##############################
# Tables to assign points
##############################

# Expected result table
# TODO, falta chequear
# difference, points to winner, points to loser
expected_result = load_csv("expected_result.csv")


# TODO, falta chequear
# difference (should be negative), points to winner, points to loser
unexpected_result = load_csv("unexpected_result.csv")

# points to be assigned by round
aux_round_points = load_csv("points_per_round.csv")
round_points = {}
for reached_round, points in aux_round_points:
    print reached_round, points
    round_points[reached_round] = points


def points_to_assign(rating_winner, rating_loser):
    """Return points to assign to each player given"""
    rating_diff = rating_winner - rating_loser

    assignation_table = expected_result
    if rating_diff < 0:
        rating_diff *= -1.0
        assignation_table = unexpected_result

    i = 0
    while rating_diff > assignation_table[i][0]:
        i += 1

    points_to_winner = assignation_table[i][1]
    points_to_loser = assignation_table[i][2]
    #print "diff:%d, to_winner:%d, to_loser:%d" % (rating_diff, points_to_winner, points_to_loser)

    return [points_to_winner, points_to_loser]


# TODO ranking model, get_rating, update_rating
def get_rating(player_id, ranking):
    return ranking[player_id]


def get_new_ranking(old_ranking, matches_list):
    # TODO make a better way to copy a list, maybe the db saves me
    new_ranking = [list(item) for item in old_ranking]
    # TODO add new players

    for winner, loser, unused in matches_list:
        # TODO change the way to read old ratings
        [to_winner, to_loser] = points_to_assign(old_ranking[winner][1], old_ranking[loser][1])
        # TODO change the way to read new ratings
        new_ranking[winner][1] += to_winner
        new_ranking[loser][1] -= to_loser

    # TODO add points per best round reached
    best_round_to_assign = {}

    for winner, loser, round_match in matches_list:
        if best_round_to_assign.get(winner):
            if best_round_to_assign.get(winner) < round_points[round_match]:
                best_round_to_assign[winner] = round_points[round_match]
        else:
            best_round_to_assign[winner] = round_points[round_match]
        if best_round_to_assign.get(loser):
            if best_round_to_assign.get(loser) < round_points[round_match]:
                best_round_to_assign[loser] = round_points[round_match]
        else:
            best_round_to_assign[loser] = round_points[round_match]

    for player_id in best_round_to_assign:
        new_ranking[player_id][1] += best_round_to_assign[player_id]

    return new_ranking
