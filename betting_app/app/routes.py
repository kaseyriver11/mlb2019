from flask import render_template
from app import application, db
from pandas import read_sql
import datetime as dt


def make_dashboard():
    q = """
        SELECT *
        FROM bet_outcomes as bo
        INNER JOIN placed_bets as pb
        on bo.id = pb.id
        """
    outcomes = read_sql(q, db.engine)

    bets = outcomes.shape[0]
    net = '$ ' + str(round(outcomes.net_gain.sum(), 2))
    total_bet = outcomes.amount_bet.sum()
    return_on_investment = str(round((outcomes.amount_bet.sum() + outcomes.net_gain.sum()) /
                                     outcomes.amount_bet.sum(), 4) * 100) + "%"

    return bets, net, total_bet, return_on_investment


def make_games():
    t = dt.date.today()

    q = """
        SELECT date, game_time, away, home
        FROM games
        WHERE date = %(date)s
        """
    games = read_sql(q, db.engine, params={'date': t})
    games.columns = ['Date', 'Game Time', 'Away', 'Home']

    return games


def make_bets():
    today = dt.date.today()
    query = """
        SELECT away, home, bet_on, odds_bet, chance_to_win, to_win, expected_winnings
        FROM placed_bets as pb
        INNER JOIN games as g
        on g.id = pb.id
        WHERE g.date = %(date)s
        """
    bets = read_sql(query, db.engine, params={'date': today})
    bets.columns = ['Away', 'Home', 'Bet On:', 'Odds', 'Win Percentage', 'To Win', 'Expected Winnings']

    return bets


def make_outcomes():
    yesterday = dt.date.today() - dt.timedelta(days=1)

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

    return outcomes


@application.route('/', methods=['GET'])
@application.route('/index', methods=['GET'])
def index():
    values = make_dashboard()
    return render_template('index.html',
                           bets=values[0],
                           net=values[1],
                           total_bet=values[2],
                           roi=values[3])


@application.route('/todays_games', methods=['GET'])
def todays_games():
    return render_template('todays_games.html',
                           games=[make_games().to_html(classes='data', index=False)])


@application.route('/todays_bets', methods=['GET'])
def todays_bets():
    return render_template('todays_bets.html',
                           bets=[make_bets().to_html(classes='data', index=False)])


@application.route('/recent_outcomes', methods=['GET'])
def recent_outcomes():
    return render_template('recent_outcomes.html',
                           outcomes=[make_outcomes().to_html(classes='data', index=False)])
