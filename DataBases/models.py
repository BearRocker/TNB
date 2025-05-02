from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey
from DataBases.DataBase import uniq_id, Base

class Users(Base):
    __tablename__ = "Users"

    ChatID: Mapped[uniq_id]
    TournamentsID: Mapped[str]
    Settings: Mapped[str]

class Tournaments(Base):
    __tablename__ = "Tournaments"

    TournamentID: Mapped[uniq_id]
    Prize: Mapped[str]
    TeamsCount: Mapped[str]
    Tier: Mapped[str]
    GameID: Mapped[int] = mapped_column(ForeignKey('Games.GameID'))
    Name: Mapped[str]
    Date: Mapped[str]
    Location: Mapped[str]

class Games(Base):
    __tablename__ = "Games"

    GameID: Mapped[uniq_id]
    Name: Mapped[str]

class Matches(Base):
    __tablename__ = "Matches"

    MatchID: Mapped[uniq_id]
    TournamentsID: Mapped[int] = mapped_column(ForeignKey('Tournaments.TournamentID'))
    GamesID: Mapped[int] = mapped_column(ForeignKey("Games.GameID"))
    Time: Mapped[str]