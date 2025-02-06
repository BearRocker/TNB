from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert, update
from DataBases.DAO.base import BaseDAO
from DataBases.models import Users, Matches, Tournaments, Games

class UserDAO(BaseDAO):
    model = Users

    @classmethod
    async def get_users(cls, session: AsyncSession):
        query = select(cls.model)
        result = await session.execute(query)
        records = result.scalars().all()
        return records

    @classmethod
    async def get_user_by_id(cls, session: AsyncSession, id: int):
        query = select(cls.model).where(Users.ChatID == id)
        result = await session.execute(query)
        records = result.scalars().all()
        return records

    @classmethod
    async def get_user_tournaments(cls, session: AsyncSession, id: int):
        query = select(cls.model.TournamentsID).where(Users.ChatID == id)
        result = await session.execute(query)
        records = result.scalars().all()
        return records

    @classmethod
    async def update_user_tournaments(cls, session: AsyncSession, id: int, tournamentsid: str):
        user = await session.get(Users, id)
        if user:
            user.TournamentsID = tournamentsid
            await session.commit()
            return user
        return None


class MatchesDAO(BaseDAO):
    model = Matches

    @classmethod
    async def get_match_by_id(cls, session: AsyncSession, id: int):
        query = select(cls.model).where(Matches.TournamentsID == id)
        result = await session.execute(query)
        records = result.scalars().all()
        return records

    @classmethod
    async def get_matches(cls, session: AsyncSession):
        query = select(cls.model.TournamentsID, cls.model.Time)
        result = await session.execute(query)
        records = result.scalars().all()
        return records

    @classmethod
    async def get_match_id(cls, session: AsyncSession):
        query = select(cls.model.MatchID)
        result = await session.execute(query)
        records = result.scalars().all()
        return records

    @classmethod
    async def delete_match(cls, session: AsyncSession, id: int):
        query = delete(cls.model).where(Matches.TournamentsID == id)
        result = await session.execute(query)
        return result

    @classmethod
    async def update_match(cls, session: AsyncSession, tournamentid: int, gameid: int, time: str):
        query = update(cls.model).where(Matches.TournamentsID == tournamentid).where(Matches.GamesID == gameid).values(Time=time)
        result = await session.execute(query)
        return result


class TournamentsDAO(BaseDAO):
    model = Tournaments

    @classmethod
    async def get_tournaments_id(cls, session: AsyncSession, name: str):
        query = select(cls.model).where(Tournaments.Name == name)
        result = await session.execute(query)
        records = result.scalars().all()
        return records

    @classmethod
    async def get_tournaments_name(cls, session: AsyncSession, id: int):
        query = select(cls.model.Name).where(Tournaments.TournamentID == id)
        result = await session.execute(query)
        record = result.scalars().all()
        return record

    @classmethod
    async def get_tournaments(cls, session: AsyncSession):
        query = select(cls.model)
        result = await session.execute(query)
        record = result.scalars().all()
        return record

    @classmethod
    async def delete_tournament(cls, session: AsyncSession, name: str):
        query = delete(cls.model).where(Tournaments.Name == name)
        result = await session.execute(query)
        return result


class GamesDAO(BaseDAO):
    model = Games

    @classmethod
    async def get_game(cls, session: AsyncSession, name: str):
        query = select(cls.model).where(Games.Name == name)
        result = await session.execute(query)
        record = result.scalars().all()
        return record
