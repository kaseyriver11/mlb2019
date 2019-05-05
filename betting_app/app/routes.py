from flask import render_template
from app import application, db, today, yesterday
from pandas import read_sql

query = """
    SELECT date, game_time, away, home
    FROM games
    WHERE date = %(date)s
    """
games = read_sql(query, db.engine, params={'date': today})
games.columns = ['Date', 'Game Time', 'Away', 'Home']


query = """
    SELECT away, home, bet_on, odds_bet, chance_to_win, to_win, expected_winnings
    FROM placed_bets as pb
    INNER JOIN games as g
    on g.id = pb.id
    WHERE g.date = %(date)s
    """
bets = read_sql(query, db.engine, params={'date': today})
bets.columns = ['Away', 'Home', 'Bet On:', 'Odds', 'Win Percentage', 'To Win', 'Expected Winnings']


query = """
    SELECT g.away, g.home, bet_on, amount_won, net_gain
    FROM bet_outcomes as bo
    INNER JOIN games as g
        on g.id = bo.id
    INNER JOIN placed_bets as pb
        on pb.id = bo.id
    WHERE g.date = %(date)s
    """
outcomes = read_sql(query, db.engine, params={'date': yesterday})
outcomes.columns = ['Away', 'Home', 'Bet On', 'Amount Won', 'Net Gain']

@application.route('/', methods=['GET'])
@application.route('/index', methods=['GET'])
def index():
    return render_template('index.html')


@application.route('/todays_games', methods=['GET'])
def todays_games():
    return render_template('todays_games.html',
                           games=[games.to_html(classes='data', index=False)])


@application.route('/todays_bets', methods=['GET'])
def todays_bets():
    return render_template('todays_bets.html',
                           bets=[bets.to_html(classes='data', index=False)])


@application.route('/recent_outcomes', methods=['GET'])
def recent_outcomes():
    return render_template('recent_outcomes.html',
                           outcomes=[outcomes.to_html(classes='data', index=False)])
