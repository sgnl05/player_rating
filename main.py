import sys, getopt, yaml
from flask import Flask, render_template, request
from openskill import *
from collections import OrderedDict
from itertools import combinations

app = Flask(__name__)

# Define default rating
default_mu = 25
default_sigma = 8.333333333333334
default_rating = Rating(mu=default_mu, sigma=default_sigma)
default_ordinal = ordinal(mu=default_mu, sigma=default_sigma)

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

for m_id, m_info in reversed(matches.items()):

    # Define teams and stats
    winning_team = winners = []
    losing_team = losers = []
    draw_team1 = draw_team2 = draw = []
    winning_team_rating = []
    losing_team_rating = []
    draw_team1_rating = draw_team2_rating = []

    for key in m_info:
        for id in m_info[key]:
            if key == 'winning_team':
                draw = False
                winning_team.append(id)
                winning_team_rating.append(players[id]['rating'])
                players[id]['wins']+=1
            elif key == 'losing_team':
                draw = False
                losing_team.append(id)
                losing_team_rating.append(players[id]['rating'])
                players[id]['loss']+=1
            elif key == ('draw_team1'):
                draw = True
                draw_team1.append(id)
                draw_team1_rating.append(players[id]['rating'])
                players[id]['draw']+=1
            elif key == ('draw_team2'):
                draw = True
                draw_team2.append(id)
                draw_team2_rating.append(players[id]['rating'])
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

sorted_players = OrderedDict(sorted(players.items(), key=lambda i: i[1]['ordinal'], reverse=True))


@app.route('/')
def root():
    return render_template('index.html', players=sorted_players)

@app.route("/",methods=['GET','POST'])
def teams():

    selected_players = request.form.getlist('players')
    keepers = []
    total_rating = 0
    player_rating = {}

    for p_id in selected_players:
        player_rating[p_id] = round(players[p_id]['ordinal'] * 100)
        if not 'keeper' in players[p_id]:
            players[p_id]['keeper'] = False
        if players[p_id]['keeper']:
            keepers.append(p_id)

    # Look at all team combinations and find the closest rating difference
    closest_difference = None
    all_players_set = set(player_rating.keys())
    for team_a in combinations(player_rating.keys(), int(len(all_players_set) / 2)):

        # Discard team combinations where at least two keepers are available, but they all end up on the same team
        if len(keepers) >= 2 and set(keepers).issubset(set(team_a)):
            pass # Team A got all keepers
        elif len(keepers) >= 2 and set(keepers).isdisjoint(set(team_a)):
            pass # Team A got no keepers
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
    team_a_with_rating = {}
    team_a_total = str(sum([player_rating[x] for x in best_team_a]))
    for player in best_team_a:
      team_a_with_rating[player] = round(players[player]['ordinal'] * 100)
    team_a_sorted = OrderedDict(sorted(team_a_with_rating.items(), key=lambda i: i[1], reverse=True))

    # Store details for Team B
    team_b_with_rating = {}
    team_b_total = str(sum([player_rating[x] for x in best_team_b]))
    for player in best_team_b:
      team_b_with_rating[player] = round(players[player]['ordinal'] * 100)
    team_b_sorted = OrderedDict(sorted(team_b_with_rating.items(), key=lambda i: i[1], reverse=True))

    # Return teams
    return render_template('index.html', players=sorted_players,selected_players=selected_players,keepers=keepers,team_a=team_a_sorted,team_a_total=team_a_total,team_b=team_b_sorted,team_b_total=team_b_total)

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
