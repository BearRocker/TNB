from DataBases.dao import UserDAO, MatchesDAO
from DataBases.DataBase import connection_db
from sqlalchemy.ext.asyncio import AsyncSession

@connection_db
async def update_matches(tournamentid: int, gameid: int, time: str, session: AsyncSession):
    return await MatchesDAO.update_match(session, tournamentid, gameid, time)

@connection_db
async def update_user_tournaments(id: int, tournamentsid: str, session: AsyncSession):
    return await UserDAO.update_user_tournaments(session, id, tournamentsid)