__author__ = 'sebastian'


class Player:
    """
    Model for a player
    """

    def __init__(self, nid, name, rating=0.0):
        self.nid = nid
        self.name = name
        self.email = "user@host.com"
        self.rating = rating
        self.association = "Association"

    def __str__(self):
        return "Player nid={0:d}, name={1:s}, rating={2:d}".format(self.nid, self.name, self.rating)

    def __repr__(self):
        return "<Player nid={0:d}, name={1:s}, rating={2:d}>".format(self.nid, self.name, self.rating)


class Match:
    """
    Model for a match, were there is a winner and a loser player
    """
    def __init__(self):
        self.winner = -1
        self.looser = -1


def points_to_assign(nid_winner, nid_loser, players_table):
    """Return points to assign to each player given """
    points_diff = players_table[nid_winner].rating - players_table[nid_loser].rating

    # tables to assign points

    # Expected result table
    # difference, points to winner, points to loser
    expected_result = [[24, 9, 9],
                       [49, 8, 8],
                       [99, 7, 7],
                       [149, 6, 6],
                       [199, 5, 5],
                       [299, 4, 4],
                       [399, 3, 3],
                       [499, 2, 2],
                       [999, 1, 1]]

    # difference, points to winner, points to loser
    unexpected_result = [[24, 10, 9],
                         [49, 11, 10],
                         [99, 13, 11],
                         [149, 15, 12],
                         [199, 18, 14],
                         [299, 21, 16],
                         [399, 24, 18],
                         [499, 28, 21],
                         [999, 32, 25]]

    assignation_table = expected_result
    if points_diff < 0:
        print "expected result"
        assignation_table = unexpected_result
    # else:
    #     print "unexpected result"

    i = 0
    while points_diff > assignation_table[i][0]:
        i += 1

    points_to_winner = assignation_table[i][1]
    points_to_loser = assignation_table[i][2]
    print "diff:%d, to_winner:%d, to_loser:%d" % (points_diff, points_to_winner, points_to_loser)


def get_new_ranking(old_ranking, matches_list):
    new_ranking = old_ranking + new_players

    for match in matches_list:

        [points_to_winner, points_to_loser] = points_to_assign(winner_rating, loser_rating)
        new_ranking.update_points(winner, points_to_winner)
        new_ranking.update_points(loser, points_to_loser)

