
import json
import sqlalchemy
import pandas as pd

# ----------------------------------------------------------------------------------------------------------------------
# ----- Setup credentials
with open('local/db_creds.prod', mode='rt') as f:
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
    a_starting_pitcher text,
    a_team_rating integer,
    a_starting_pitcher_adjustment integer,
    a_travel_adjustment integer,
    a_pregame_rating integer,
    a_chance_winning decimal,
    h_starting_pitcher text,
    h_team_rating integer,
    h_starting_pitcher_adjustment integer,
    h_travel_adjustment integer,
    h_pregame_rating integer,
    h_chance_winning float)
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
    to_win float)
""")

# ----------------------------------------------------------------------------------------------------------------------
# ----- BET_OUTCOMES
conn.execute("""
    CREATE TABLE bet_outcomes(
    id text PRIMARY KEY,
    amount_bet integer,
    amount_won float)
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

# ----------------------------------------------------------------------------------------------------------------------
# ----- Test the code
query = """
    SELECT *
    FROM mlb_538
    """
pd.read_sql(query, db)
