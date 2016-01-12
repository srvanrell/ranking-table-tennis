__author__ = 'sebastian'

import utils

# Fake list of players (0 to 9)
players_list = [utils.Player(i, "Player%i" % i, rating=100+20*i) for i in range(10)]

# Fake list of matches in a single tournament (big number player wins)
# winner, loser, stage
matches_list = [[i, j, 'unused'] for i in range(10) for j in range(i)]

# printing the list of players
for player in players_list:
    print player

# printing the list of
for winner, loser, stage in matches_list:
    print winner, loser

    utils.points_to_assign(winner, loser, players_list)

