
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

