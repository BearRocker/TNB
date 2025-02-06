from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, async_session, AsyncSession
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column, foreign, class_mapper, contains_eager
from Config import DB_password, DB_HOST, DB_NAME, DB_PORT, DB_login

class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    def to_dict(self) -> dict:
        columns = class_mapper(self.__class__).columns
        return {column.key: getattr(self, column.key) for column in columns}



uniq_id = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]

DB_URL = f"postgresql+asyncpg://{DB_login}:{DB_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_async_engine(url=DB_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

def connection_db(method):
    async def wrapper(*args, **kwargs):
        async with async_session_maker() as session:
            try:
                # Явно не открываем транзакции, так как они уже есть в контексте
                return await method(*args, session=session, **kwargs)
            except Exception as e:
                await session.rollback()  # Откатываем сессию при ошибке
                raise e  # Поднимаем исключение дальше
            finally:
                await session.close()  # Закрываем сессию

    return wrapper