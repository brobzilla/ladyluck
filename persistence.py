from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from UniqueMixin import UniqueMixin
from myapp import db_connector


__author__ = 'lhayhurst'

import datetime
from marshmallow import Schema, fields
from decl_enum import DeclEnum
from sqlalchemy import Column, Integer, String, DateTime, Table, desc, Float, asc
from sqlalchemy import ForeignKey


#TABLES

game_roll_table = "game_roll"
game_players_table = "game_players"
game_winner_table = "game_winner"
game_roll_table = 'game_roll_type'
player_table = "player"
dice_table = 'dice'
game_table = "game"
dice_throw_table = "dice_throw"
dice_throw_result_table = "dice_throw_result"
dice_throw_adjustment_table = "dice_throw_adjustment"

Base = db_connector.get_base()

GamePlayers = Table(game_players_table, Base.metadata,
                    Column('game_id', Integer, ForeignKey('{0}.id'.format(game_table))),
                    Column('player_id', Integer, ForeignKey('{0}.id'.format(player_table)))
)

GameWinner = Table(game_winner_table, Base.metadata,
                   Column('game_id', Integer, ForeignKey('{0}.id'.format(game_table))),
                   Column('player_id', Integer, ForeignKey('{0}.id'.format(player_table)))
)


class DiceType(DeclEnum):
    RED = 'R', "RED"
    GREEN = 'G', "GREEN"


class DiceFace(DeclEnum):
    HIT = 'H', "HIT"
    CRIT = "C", "CRIT"
    FOCUS = "F", "FOCUS"
    BLANK = "B", "BLANK"
    EVADE = "E", "EVADE"


class DiceThrowType(DeclEnum):
    ATTACK = 'A', 'ATTACK'
    DEFEND = 'D', 'DEFEND'

#TODO: add turned enum to database
# ALTER TABLE `sozin$ladyluck`.`dice_throw_adjustment`
# CHANGE COLUMN `adjustment_type` `adjustment_type` ENUM('C', 'R', 'N', 'T') NULL DEFAULT NULL ;
class DiceThrowAdjustmentType(DeclEnum):
    REROLL = 'R', 'REROLL'
    CONVERT = 'C', 'CONVERT'
    NONE = 'N', 'NONE'
    TURNED = 'T', 'TURNED'
    CANCELLED = 'X', 'CANCELLED'

class LuckMeasure(DeclEnum):
    DOZIN = 'D', 'DOZIN',
    BINOMIAL_DISTRIBUTION = 'B', 'BINOMIAL_DISTRIBUTION'


class Player(UniqueMixin, Base):
    __tablename__ = player_table
    id = Column(Integer, primary_key=True )
    name = Column(String(64), unique=True)

    def __repr__(self):
        return "<Player(id={0}name={1}".format(self.id, self.name)

    def __init__(self, name):
        self.name =  name

    @classmethod
    def unique_hash(cls, name):
        return name

    @classmethod
    def unique_filter(cls, query, name):
        return query.filter(Player.name == name)



class Dice(Base):
    __tablename__ = dice_table
    id = Column(Integer, primary_key=True)
    dice_type = Column(DiceType.db_type())
    dice_face = Column(DiceFace.db_type())
    dice_origination = Column(String(8))


    #sources for dice origination.  note, I'm not making these enums because they are too @#^#ing annoying
    ROLLED = "ROLLED"
    ADDED  = "ADDED"

    def was_rolled(self):
        return self.dice_origination == Dice.ROLLED

    def was_added(self):
        return self.dice_origination == Dice.ADDED

    def is_hit(self):
        return self.dice_face == DiceFace.HIT

    def is_crit(self):
        return self.dice_face == DiceFace.CRIT

    def is_focus(self):
        return self.dice_face == DiceFace.FOCUS

    def is_blank(self):
        return self.dice_face == DiceFace.BLANK

    def is_evade(self):
        return self.dice_face == DiceFace.EVADE

    def is_attack(self):
        return self.dice_type == DiceType.RED

    def is_defense(self):
        return self.dice_type == DiceType.GREEN


class DiceThrowAdjustment(Base):
    __tablename__ = dice_throw_adjustment_table
    id = Column(Integer, primary_key=True)
    base_result_id = Column(Integer, ForeignKey('{0}.id'.format(dice_throw_result_table)))
    from_dice_id = Column(Integer, ForeignKey('{0}.id'.format(dice_table)))
    to_dice_id = Column(Integer, ForeignKey('{0}.id'.format(dice_table)))
    adjustment_type = Column(DiceThrowAdjustmentType.db_type())
    from_dice = relationship(Dice.__name__, foreign_keys='DiceThrowAdjustment.from_dice_id')
    to_dice = relationship(Dice.__name__, foreign_keys='DiceThrowAdjustment.to_dice_id')


class DiceThrowResult(Base):
    __tablename__ = dice_throw_result_table
    id = Column(Integer, primary_key=True)
    dice_throw_id = Column(Integer, ForeignKey('{0}.id'.format(dice_throw_table)))  #parent
    dice_num = Column(Integer)
    dice_result_id = Column(Integer, ForeignKey('{0}.id'.format(dice_table)))
    final_dice_result_id = Column(Integer, ForeignKey('{0}.id'.format(dice_table)))
    dice = relationship(Dice.__name__, foreign_keys='DiceThrowResult.dice_result_id', uselist=False)
    final_dice = relationship(Dice.__name__, foreign_keys='DiceThrowResult.final_dice_result_id', uselist=False)
    adjustments = relationship(DiceThrowAdjustment.__name__)

    def was_cancelled(self):
        if len(self.adjustments) == 0:
            return False
        last_adjustment = self.adjustments[-1]
        if last_adjustment.adjustment_type == DiceThrowAdjustmentType.CANCELLED:
            return True


class DiceThrow(Base):
    __tablename__ = dice_throw_table
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('{0}.id'.format(game_table)))
    player_id = Column(Integer, ForeignKey('{0}.id'.format(player_table)))
    throw_type = Column(DiceThrowType.db_type())
    attack_set_num = Column(Integer)
    player = relationship(Player.__name__, uselist=False)
    results = relationship(DiceThrowResult.__name__)


class DiceThrowSchema(Schema):
    id = fields.Number()
    game_id = fields.Number()
    player_id = fields.Number()
    # throw_type = fields.Str()
    attack_set_num = fields.Number()
    # player = relationship(Player.__name__, uselist=False)
    # results = relationship(DiceThrowResult.__name__)


class Game(Base):
    __tablename__ = game_table
    id = Column(Integer, primary_key=True)
    game_played_time = Column(DateTime)
    game_name = Column(String(128))
    game_players = relationship(Player.__name__, secondary=GamePlayers)
    game_throws = relationship(DiceThrow.__name__)
    game_winner = relationship(Player.__name__, secondary=GameWinner, uselist=False)

    def __init__(self, session, players, winner=None):
        self.game_played_time = datetime.datetime.now()
        for player in players:
            self.game_players.append(Player.as_unique(session, name=player))
        self.game_name = "{0} v {1} ({2}".format(self.game_players[0].name, self.game_players[1].name,
                                                 self.game_played_time)
        if winner is not None:
            self.game_winner = winner

        self.game_tape = None


    def id_str(self):
        return str(self.id)

    def get_player_by_name(self, name):
        for p in self.game_players:
            if p.name == name:
                return p
        return None

    def get_player_by_id(self, pid):
        for p in self.game_players:
            if p.id == pid:
                return p
        return None


    def display_text(self):
        return "{0} v {1} at {2}".format(self.game_players[0].name, self.game_players[1].name, self.game_played_time)


class GameSchema(Schema):
    id = fields.Number()
    game_played_time = fields.DateTime()
    game_name = fields.Str()
    # game_players = relationship(Player.__name__, secondary=GamePlayers)
    # game_throws = fields.List(fields.Nested(DiceThrowSchema()))
    # game_winner = relationship(Player.__name__, secondary=GameWinner, uselist=False)

luck_result_table = "luck_result"
class LuckResult(Base):
    __tablename__        = luck_result_table
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('{0}.id'.format(player_table)))
    player               = relationship(Player.__name__, uselist=False)
    game_id = Column(Integer, ForeignKey('{0}.id'.format(game_table)))
    game                 = relationship(Game.__name__, uselist=False)
    measure              = Column(LuckMeasure.db_type())
    initial_attack_luck  = Column(Float)
    initial_defense_luck = Column(Float)
    final_attack_luck    = Column(Float)
    final_defense_luck   = Column(Float)




class PersistenceManager:

    db_connector = None

    def __init__(self, db_connector):
        self.db_connector = db_connector

    def create_schema(self):
        self.db_connector.get_base().metadata.create_all(self.db_connector.get_engine())

    def drop_schema(self):
        self.db_connector.get_base().metadata.drop_all(self.db_connector.get_engine())


    def populate_reference_tables(self):
        #return True
        session = self.db_connector.get_session()
        session.add_all([
            Dice(dice_type=DiceType.RED, dice_face=DiceFace.HIT),
            Dice(dice_type=DiceType.RED, dice_face=DiceFace.CRIT),
            Dice(dice_type=DiceType.RED, dice_face=DiceFace.FOCUS),
            Dice(dice_type=DiceType.RED, dice_face=DiceFace.BLANK),
            Dice(dice_type=DiceType.GREEN, dice_face=DiceFace.EVADE),
            Dice(dice_type=DiceType.GREEN, dice_face=DiceFace.FOCUS),
            Dice(dice_type=DiceType.GREEN, dice_face=DiceFace.BLANK)])

    def get_games(self, session):
        return session.query(Game).order_by(desc(Game.game_played_time)).all()

    def delete_all_luck_results(self, session):
        session.query(LuckResult).delete()
        session.commit()

    def get_worst_green_luck_scores(self, session):
        return session.query(LuckResult).order_by(asc(LuckResult.initial_defense_luck))

    def get_worst_red_luck_scores(self, session):
        return session.query(LuckResult).order_by(asc(LuckResult.initial_attack_luck))

    def get_luck_score(self, session, game_id):
        return session.query(LuckResult).filter_by(game_id=game_id).first()

    def get_best_green_luck_scores(self, session):
        return session.query(LuckResult).order_by(desc(LuckResult.initial_defense_luck))

    def get_best_red_luck_scores(self, session):
        return session.query(LuckResult).order_by(desc(LuckResult.initial_attack_luck))

    def get_game(self, session, game_id):
        return session.query(Game).filter_by(id=game_id).first()

    def get_dice(self, session, dice_type, dice_face):
        return session.query(Dice).filter_by(dice_type=dice_type, dice_face=dice_face).first()

    def get_player(self, session, player):
        return session.query(Player).filter_by(name=player.name).first()





