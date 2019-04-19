
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
# ----- Add a table to the database
conn.execute("""
    CREATE TABLE team_names(
    id integer PRIMARY KEY,
    abbreviation text,
    city text,
    full_name text,
    short_name text)
""")

# ----------------------------------------------------------------------------------------------------------------------
# ----- Read the table names
tn = pd.read_csv("data/team_names.csv")
for row in tn.iterrows():
    conn.execute("INSERT INTO team_names VALUES (%s, %s, %s, %s, %s)", row[1])

# ---- Did it work?
query = '''
        SELECT *
        FROM team_names
        '''
# ----- Run query
teams = pd.read_sql(query, db)

# ----------------------------------------------------------------------------------------------------------------------
# ----- Read the table names: fill in password
conn.execute("""
    CREATE USER chenrocky WITH PASSWORD '';
""")

# ----- Give Rocky Access
conn.execute("""
    GRANT CONNECT ON DATABASE mlb2019 TO chenrocky;
    GRANT SELECT ON team_names TO chenrocky;
""")

# ----------------------------------------------------------------------------------------------------------------------
# ----- GAMES
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
    h_chance_winning decimal)
""")

# ----------------------------------------------------------------------------------------------------------------------
# ----- PLACED_BETS
conn.execute("""
    CREATE TABLE placed_bets(
    id text PRIMARY KEY,
    amount integer,
    team text,
    odds integer,
    outcome)
""")


# ----------------------------------------------------------------------------------------------------------------------
# ----- GAME_OUTCOMES
conn.execute("""
    CREATE TABLE game_outcome(
    id text PRIMARY KEY,
    away text,
    home text,
    away_score integer,
    home_score integer,
    winner text)
""")
