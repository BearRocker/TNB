from sqlalchemy.util import await_only
from DataBases.dao import MatchesDAO, TournamentsDAO
from DataBases.DataBase import connection_db
from asyncio import run
from sqlalchemy.ext.asyncio import AsyncSession

@connection_db
async def delete_match(id, session):
    return await MatchesDAO.delete_match(session, id)

@connection_db
async def delete_tournament(name, session):
    return await TournamentsDAO.delete_tournament(session, name)