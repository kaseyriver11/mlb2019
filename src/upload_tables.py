
import json
import sqlalchemy
import pandas as pd

# ----------------------------------------------------------------------------------------------------------------------
# ----- Setup credentials
with open('local/db_creds_rocky.prod', mode='rt') as f:
    db_creds = json.load(f)
# ----- Setup connection
db = sqlalchemy.create_engine('{dialect}://{user}:{password}@{host}:{port}/{dbname}'.format(**db_creds))
conn = db.connect()

# ----------------------------------------------------------------------------------------------------------------------
# ----- Add the team names table
conn.execute("""
    CREATE TABLE team_names(
    id integer PRIMARY KEY,
    abbreviation text,
    city text,
    full_name text,
    short_name text)
""")

tn = pd.read_csv("data/team_names.csv")
for row in tn.iterrows():
    conn.execute("INSERT INTO team_names VALUES (%s, %s, %s, %s, %s)", row[1])

# ----------------------------------------------------------------------------------------------------------------------
# ----- Fill in password as needed
conn.execute("""
    CREATE USER chenrocky WITH PASSWORD '';
""")

# ----- Give Rocky Access
conn.execute("""
    GRANT CONNECT ON DATABASE mlb2019 TO chenrocky;
    GRANT USAGE ON SCHEMA public TO chenrocky;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO chenrocky;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO chenrocky;
""")

# ----------------------------------------------------------------------------------------------------------------------
# ----- Create an ubuntu user
conn.execute("""
    CREATE USER ubuntu WITH PASSWORD 'IAA2017';
""")

# ----- Give ubuntu Access
conn.execute("""
    GRANT CONNECT ON DATABASE mlb2019 TO ubuntu;
    GRANT USAGE ON SCHEMA public TO ubuntu;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ubuntu;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ubuntu;
""")

# ----------------------------------------------------------------------------------------------------------------------
# ----- Create the GAMES table
conn.execute("""
    CREATE TABLE games(
    id text PRIMARY KEY,
    sport text,
    date date,
    game_time time,
    away text,
    home text)
""")

# ----------------------------------------------------------------------------------------------------------------------
# ----- Create the GAME_OUTCOMES table
conn.execute("""
    CREATE TABLE game_outcomes(
    id text PRIMARY KEY,
    away_score integer,
    home_score integer,
    winner text)
""")

# ----------------------------------------------------------------------------------------------------------------------
# ----- mlb_538
conn.execute("""
    CREATE TABLE mlb_538(
    id text PRIMARY KEY,
    away_starting_pitcher text,
    away_team_rating integer,
    away_starting_pitcher_adjustment integer,
    away_travel_adjustment integer,
    away_pregame_rating integer,
    away_chance_winning decimal,
    home_starting_pitcher text,
    home_team_rating integer,
    home_starting_pitcher_adjustment integer,
    home_travel_adjustment integer,
    home_pregame_rating integer,
    home_chance_winning float)
""")

# ----------------------------------------------------------------------------------------------------------------------
# ----- PLACED_BETS
conn.execute("""
    CREATE TABLE placed_bets(
    id text PRIMARY KEY,
    sports_book text,
    bet_on text,
    amount_bet integer,
    odds_bet integer,
    chance_to_win decimal,
    to_win float,
    expected_winnings float)
""")

# ----------------------------------------------------------------------------------------------------------------------
# ----- BET_OUTCOMES
conn.execute("""
    CREATE TABLE bet_outcomes(
    id text PRIMARY KEY,
    amount_won float,
    net_gain float)
""")


# ----------------------------------------------------------------------------------------------------------------------
# ----- Sport Table
conn.execute("""
    CREATE TABLE sport_ids(
    id text PRIMARY KEY,
    sport text)
""")

sports = dict()
sports['01'] = 'MLB'
sports['02'] = 'NBA'

names = ['id', 'sport']
columns = ",".join(names)
values = "VALUES({})".format(",".join(["%s" for _ in names]))
# ----- Create insert statement
insert_stmt = "INSERT INTO {} ({}) {}".format('sport_ids', columns, values)
for sport in sports:
    value = [sport, sports[sport]]
    try:
        conn.execute(insert_stmt, value)
    except sqlalchemy.exc.IntegrityError:
        'nothing'


# Save all tables before we close projection:

# Team Names
query = """ SELECT * 
FROM team_names
"""
team_names = pd.read_sql(query, db)
team_names.to_csv("final_data/team_names.csv")

# Games
query = """ SELECT * 
FROM games
"""
games = pd.read_sql(query, db)
games.to_csv("final_data/games.csv")

# game outcomes
query = """ SELECT * 
FROM game_outcomes
"""
game_outcomes = pd.read_sql(query, db)
game_outcomes.to_csv("final_data/game_outcomes.csv")

# mlb_538
query = """ SELECT * 
FROM mlb_538
"""
mlb_538 = pd.read_sql(query, db)
mlb_538.to_csv("final_data/mlb_538.csv")

# Placed Bets
query = """ SELECT * 
FROM placed_bets
"""
placed_bets = pd.read_sql(query, db)
placed_bets.to_csv("final_data/placed_bets.csv")

# Bet Outcomes
query = """ SELECT * 
FROM bet_outcomes
"""
bet_outcomes = pd.read_sql(query, db)
bet_outcomes.to_csv("final_data/bet_outcomes.csv")

# sport_ids
query = """ SELECT * 
FROM sport_ids
"""
sport_ids = pd.read_sql(query, db)
sport_ids.to_csv("final_data/sport_ids.csv")
