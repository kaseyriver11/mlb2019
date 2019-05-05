from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import json
import datetime as dt

today = dt.date.today()
yesterday = dt.date.today() - dt.timedelta(days=1)

with open('db_creds.prod', mode='rt') as f:
    db_creds = json.load(f)


application = Flask(__name__)
application.config['SQLALCHEMY_DATABASE_URI'] =\
    '{dialect}://{user}:{password}@{host}:{port}/{dbname}'.format(**db_creds)
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # silence the deprecation warning

db = SQLAlchemy(application)
# db.Model.metadata.reflect(db.engine)


import routes

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=80)
