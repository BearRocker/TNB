from DataBases.dao import MatchesDAO, TournamentsDAO, GamesDAO, UserDAO
from DataBases.DataBase import connection_db
from sqlalchemy.ext.asyncio import AsyncSession


@connection_db
async def select_all_matches(session: AsyncSession):
    return await MatchesDAO.get_matches(session)

@connection_db
async def select_matches_by_id(id: int, session: AsyncSession):
    return await MatchesDAO.get_match_by_id(session, id)

@connection_db
async def select_tournament_by_name(name: str, session: AsyncSession):
    return await TournamentsDAO.get_tournaments_id(session, name)

@connection_db
async def select_tournaments(session: AsyncSession):
    return await TournamentsDAO.get_tournaments(session)

@connection_db
async def select_tournaments_by_id(id: int, session: AsyncSession):
    return await TournamentsDAO.get_tournaments_name(session, id)

@connection_db
async def select_games(name:str, session: AsyncSession):
    return await GamesDAO.get_game(session, name)

@connection_db
async def select_user_by_id(id: int, session: AsyncSession):
    return await UserDAO.get_user_by_id(session, id)

@connection_db
async def select_user_tournaments(id: int, session: AsyncSession):
    return await UserDAO.get_user_tournaments(session, id)

@connection_db
async def select_users(session: AsyncSession):
    return await UserDAO.get_users(session)

@connection_db
async def select_game_by_id(id: int, session: AsyncSession):
    return await GamesDAO.get_game_by_id(session, id)