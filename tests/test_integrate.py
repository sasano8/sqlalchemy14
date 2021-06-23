import os

import pytest
import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy14 import Crud

Base = declarative_base()


class Persons(Base, Crud):
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
def db_engine(db_config):
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


async def db_init(engine, create_session):
    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.drop_all)
        except:
            pass
        await conn.run_sync(Base.metadata.create_all)


INITIALIZED = False


@pytest.fixture(scope="function")
async def db(db_engine):
    engine, create_session = db_engine
    global INITIALIZED
    if not INITIALIZED:
        await db_init(engine, create_session)
        INITIALIZED = True

    async with create_session() as session:
        stmt = delete(Persons)
        result = await session.execute(stmt)
        await session.commit()

    async with create_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()


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


@pytest.mark.parametrize("schema", [Persons, Person])
@pytest.mark.docker
@pytest.mark.asyncio
async def test_crud(db, schema):
    crud = schema.crud(db)

    result = await crud.all()
    assert len(result) == 0

    created = await crud.create(name="test_create")
    assert created.name == "test_create"
    assert isinstance(created, schema)

    result = await crud.all()
    assert len(result) == 1
    assert isinstance(result[0], schema)

    updated = await crud.update(id=created.id, name="test_update")
    assert updated.name == "test_update"
    assert isinstance(updated, schema)

    result = await crud.all()
    assert len(result) == 1
    assert isinstance(result[0], schema)

    deleted = await crud.delete(id=updated.id)
    assert deleted is None

    result = await crud.all()
    assert len(result) == 0
