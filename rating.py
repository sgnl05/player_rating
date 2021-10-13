#!/usr/bin/env python3.9

import sys, getopt, yaml
from openskill import *
from prettytable import PrettyTable
from itertools import combinations


def main(argv):

  list_spesific_players = False
  split_keepers = False
  try:
    opts, args = getopt.getopt(argv,"hp:k",["players="])
  except getopt.GetoptError:
    print('rating.py -p player1,player2')
    sys.exit(2)
  for opt, arg in opts:
    if opt == '-h':
      print('rating.py -p player1,player2')
      sys.exit()
    elif opt in ('-p', '--players'):
      list_spesific_players = True
      spesific_players = arg.split(",")
    elif opt in '-k':
      split_keepers = True


  # Define table and fields
  table = PrettyTable()
  table.field_names = ["Player", "Rating", "Win", "Loss", "Draw"]

  # Define default rating
  default_mu = 25
  default_sigma = 8.333333333333334
  default_rating = Rating()
  default_ordinal = ordinal(mu=25, sigma=8.333333333333334)

  # Read YAML files
  with open("players.yaml", 'r') as stream:
    players = yaml.safe_load(stream)
  with open("matches.yaml", 'r') as stream:
    matches = yaml.safe_load(stream)

  # Store some default numbers for players
  for id in players:
    players[id].update(mu = default_mu)
    players[id].update(sigma = default_sigma)
    players[id].update(rating = default_rating)
    players[id]['ordinal'] = default_ordinal
    players[id].update(wins = 0)
    players[id].update(loss = 0)
    players[id].update(draw = 0)

  for m_id, m_info in matches.items():

    # Define teams and stats
    keepers = []
    winning_team = winners = []
    losing_team = losers = []
    draw_team1 = draw_team2 = draw = []
    winning_team_rating = []
    losing_team_rating = []
    draw_team1_rating = draw_team2_rating = []
    winning_team_player_count = 0
    losing_team_player_count = 0
    draw_team1_player_count = 0
    draw_team2_player_count = 0

    for key in m_info:
      for id in m_info[key]:
        if key == 'winning_team':
          draw = False
          winning_team.append(id)
          winning_team_rating.append(players[id]['rating'])
          winning_team_player_count+=1
          players[id]['wins']+=1
        elif key == 'losing_team':
          draw = False
          losing_team.append(id)
          losing_team_rating.append(players[id]['rating'])
          losing_team_player_count+=1
          players[id]['loss']+=1
        elif key == ('draw_team1'):
          draw = True
          draw_team1.append(id)
          draw_team1_rating.append(players[id]['rating'])
          draw_team1_player_count+=1
          players[id]['draw']+=1
        elif key == ('draw_team2'):
          draw = True
          draw_team2.append(id)
          draw_team2_rating.append(players[id]['rating'])
          draw_team2_player_count+=1
          players[id]['draw']+=1

  # Calculate and store new ranking
    if draw:
      [draw1, draw2] = rate([draw_team1_rating, draw_team2_rating], score=[1] * (len(draw_team1_rating) + len(draw_team2_rating)))
    else:
      [winners, losers] = rate([winning_team_rating, losing_team_rating])

    wi = -1
    for p_id in winning_team:
      wi+=1
      players[p_id]['rating'] = create_rating(winners[wi])
      players[p_id]['mu'] = winners[wi][0]
      players[p_id]['sigma'] = winners[wi][1]
      players[p_id]['ordinal'] = ordinal(mu=players[p_id]['mu'], sigma=players[p_id]['sigma'])
    li = -1
    for p_id in losing_team:
      li+=1
      players[p_id]['rating'] = create_rating(losers[li])
      players[p_id]['mu'] = losers[li][0]
      players[p_id]['sigma'] = losers[li][1]
      players[p_id]['ordinal'] = ordinal(mu=players[p_id]['mu'], sigma=players[p_id]['sigma'])
    d1i = -1
    for p_id in draw_team1:
      d1i+=1
      players[p_id]['rating'] = create_rating(draw1[d1i])
      players[p_id]['mu'] = draw1[d1i][0]
      players[p_id]['sigma'] = draw1[d1i][1]
      players[p_id]['ordinal'] = ordinal(mu=players[p_id]['mu'], sigma=players[p_id]['sigma'])
    d2i = -1
    for p_id in draw_team2:
      d2i+=1
      players[p_id]['rating'] = create_rating(draw2[d2i])
      players[p_id]['mu'] = draw2[d2i][0]
      players[p_id]['sigma'] = draw2[d2i][1]
      players[p_id]['ordinal'] = ordinal(mu=players[p_id]['mu'], sigma=players[p_id]['sigma'])


  for p_id, p_info in players.items():
    if list_spesific_players:
      if p_id in spesific_players:
        table.add_row([players[p_id]['name'], round(players[p_id]['ordinal'] * 100), players[p_id]['wins'], players[p_id]['loss'], players[p_id]['draw']])
    else:
      table.add_row([players[p_id]['name'], round(players[p_id]['ordinal'] * 100), players[p_id]['wins'], players[p_id]['loss'], players[p_id]['draw']])

  print(table.get_string(sortby="Rating", reversesort=True))


  # If -p /--players is set
  if list_spesific_players:
    total_rating = 0
    player_rating = {}
    for p_id in spesific_players:
      player_rating[p_id] = round(players[p_id]['ordinal'] * 100)
      if not 'keeper' in players[p_id]:
        players[p_id]['keeper'] = False
      if players[p_id]['keeper']:
        keepers.append(p_id)

    # Look at all team combinations and find the closest rating difference
    closest_difference = None
    all_players_set = set(player_rating.keys())
    for team_a in combinations(player_rating.keys(), int(len(all_players_set) / 2)):

      # if -k is set
      if split_keepers and set(keepers).issubset(set(team_a)):
        pass # Team A has all keepers
      elif split_keepers and set(keepers).isdisjoint(set(team_a)):
        pass # Team A has no keepers
      else:

        team_a_set = set(team_a)
        team_b_set = all_players_set - team_a_set

        team_a_total = sum([player_rating[x] for x in team_a_set])
        team_b_total = sum([player_rating[x] for x in team_b_set])

        score_difference = abs(team_a_total - team_b_total)

        if not closest_difference or score_difference < closest_difference:
          closest_difference = score_difference
          best_team_a = team_a_set
          best_team_b = team_b_set

    # Store details for Team A
    team_a_count=0
    best_team_a_with_rating = {}
    for player in best_team_a:
      team_a_count+=1
      best_team_a_with_rating[player] = round(players[player]['ordinal'] * 100)

    # Store details for Team B
    team_b_count=0
    best_team_b_with_rating = {}
    for player in best_team_b:
      team_b_count+=1
      best_team_b_with_rating[player] = round(players[player]['ordinal'] * 100)

    # Print the team setup
    print("\n*** Team A (" + str(sum([player_rating[x] for x in best_team_a])) + "/" + str(team_a_count) + ") ***")
    for k, v in sorted(best_team_a_with_rating.items(), key=lambda x: x[1], reverse=True):
      print(k, v)
    print("\n*** Team B (" + str(sum([player_rating[x] for x in best_team_b])) + "/" + str(team_b_count) + ") ***")
    for k, v in sorted(best_team_b_with_rating.items(), key=lambda v: v[1], reverse=True):
      print(k, v)
    print("\n")

if __name__ == "__main__":
   main(sys.argv[1:])

