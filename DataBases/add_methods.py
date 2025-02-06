from DataBases.dao import MatchesDAO, TournamentsDAO, GamesDAO, UserDAO
from DataBases.DataBase import connection_db
from sqlalchemy.ext.asyncio import AsyncSession


@connection_db
async def add_match(match_data: dict, session: AsyncSession):
    new_match = await MatchesDAO.add(session=session, **match_data)
    return new_match.MatchID

@connection_db
async def add_matches(matches_data: list[dict], session: AsyncSession):
    new_matches = await MatchesDAO.add_many(session=session, instances=matches_data)
    matches_ilds = [match.MatchID for match in new_matches]
    return matches_ilds

@connection_db
async def add_tournament(tournament_data: dict, session: AsyncSession):
    new_tournament = await TournamentsDAO.add(session=session, **tournament_data)
    return new_tournament.TournamentID

@connection_db
async def add_games(games_data: dict, session: AsyncSession):
    new_game = await GamesDAO.add(session=session, **games_data)
    return new_game.GameID

@connection_db
async def add_user(user_data: dict, session: AsyncSession):
    new_user = await UserDAO.add(session=session, **user_data)
    return new_user.UserID