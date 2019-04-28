
import datetime as dt
import json
import sqlalchemy



def convert_time(x):
    x = x.replace(' Eastern', '')
    if len(x) > 7:
        in_time = dt.datetime.strptime(x.replace(".", ""), "%I:%M %p").time()
    else:
        in_time = dt.datetime.strptime(x.replace(".", ""), "%I %p").time()
    return in_time


def short_date_to_datetime(x, ref_date):
    month = int(x.text[0:x.text.find('/')])
    day = int(x.text[(x.text.find('/')+1):])

    return dt.date(ref_date.year, month, day)


def make_int(x):
    return int(x.text) if x.text[0] != '–' else int(x.text[1:]) * -1


def setup_db():
    # ----- Setup credentials
    with open('local/db_creds.prod', mode='rt') as f:
        db_creds = json.load(f)
    # ----- Setup connection
    db = sqlalchemy.create_engine('{dialect}://{user}:{password}@{host}:{port}/{dbname}'.format(**db_creds))
    return db


opening_day = dt.date(2019, 3, 28)
day_id = (dt.date.today() - opening_day).days
yesterday = dt.date.today() - dt.timedelta(days=1)
today = dt.date.today()
