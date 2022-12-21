from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import InterfaceError, SQLAlchemyError

from _socket import gaierror
from contextlib import asynccontextmanager

from app.config import settings
from app.errors import NoDBConnection, DBError

engine = create_async_engine(
    settings.db_connection_string,
    echo=settings.debug,
)

async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

Base = declarative_base()


@asynccontextmanager
async def db_session() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except (gaierror, InterfaceError):
            await session.rollback()
            raise NoDBConnection(settings.db_connection_string)
        except SQLAlchemyError:
            await session.rollback()
            raise DBError()
        except:
            await session.rollback()
            raise
