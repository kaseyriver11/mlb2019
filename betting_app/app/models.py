from app import db


class Games(db.Model):
    __table__ = db.Model.metadata.tables['games']

    def __repr__(self):
        return self.id


class bets(db.Model):
    __table__ = db.Model.metadata.tables['placed_bets']

    def __repr__(self):
        return self.id
