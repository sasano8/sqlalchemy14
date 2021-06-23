import os

import pytest
import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy import delete

from sqlalchemy14 import Crud

Base = sa.ext.declarative.declarative_base()


class Persons(Base):
    __tablename__ = "persons"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)


class Person(BaseModel, Crud[Persons]):
    id: int = None
    name: str = None


@pytest.fixture(scope="session")
def db_config():
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    db = os.getenv("POSTGRES_DB", "postgres")
    user = os.getenv("POSTGRES_USER", "postgres")
    pw = os.getenv("POSTGRES_PASSWORD", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")

    return host, db, user, pw, port


@pytest.fixture(scope="session")
def db_init_engine(db_config):
    import sqlalchemy as sa
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

    host, db, user, pw, port = db_config
    connection_string = f"postgresql+asyncpg://{user}:{pw}@{host}:{port}/{db}"
    engine = create_async_engine(connection_string)
    create_session = sa.orm.sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    return engine, create_session


@pytest.fixture(scope="session")
async def db_engine(db_init_engine):
    engine, create_session = db_init_engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.meta.drop_all)
        await conn.run_sync(Base.meta.create_all)
    return engine, create_session


@pytest.fixture(scope="function")
async def db(db_engine):
    engine, create_session = db_engine

    async with create_session() as session:
        stmt = delete(Persons)
        result = await session.execute(stmt)
        session.commit()

    async with create_session() as session:
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()


@pytest.mark.docker
def test_integrate(request, db_config):
    env = request.config.getoption("--env")
    assert env != "local"

    host, db, user, pw, port = db_config

    assert host
    assert db
    assert user
    assert pw
    assert port


@pytest.mark.docker
async def test_select(db):
    result = await Person.crud(db).all()
    assert len(result) == 0
