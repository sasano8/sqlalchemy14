import os

import pytest
import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy.orm import relationship

from sqlalchemy14 import Crud

R = sa.orm.registry()
Base = R.generate_base()


class Persons(Base, Crud):
    __tablename__ = "persons"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)


class Person(BaseModel, Crud[Persons]):
    class Config:
        orm_mode = True

    id: int = None
    name: str = None


class Parents(Base, Crud):
    __tablename__ = "parents"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    children = relationship("Children")

    def abcd(self):
        pass


class Children(Base, Crud):
    __tablename__ = "children"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    parent_id = sa.Column(
        sa.Integer, sa.ForeignKey("parents.id", onupdate="CASCADE", ondelete="CASCADE")
    )


class ChildrenSchema(BaseModel, Crud[Children]):
    class Config:
        orm_mode = True

    id: int
    name: str
    parent_id: int


class ParentSchema(BaseModel, Crud[Parents]):
    class Config:
        orm_mode = True

    id: int
    name: str
    children: list[ChildrenSchema]


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
    host, db, user, pw, port = db_config
    connection_string = f"postgresql+asyncpg://{user}:{pw}@{host}:{port}/{db}"
    from sqlalchemy14 import create_engine

    engine, create_session = create_engine(connection_string)
    return engine, create_session


async def db_init(engine, create_session):
    async with engine.begin() as conn:
        await conn.run_sync(R.metadata.drop_all)
        await conn.run_sync(R.metadata.create_all)


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


INITIALIZED = False


@pytest.fixture(scope="function")
async def db(db_engine):
    engine, create_session = db_engine
    global INITIALIZED
    if not INITIALIZED:
        await db_init(engine, create_session)
        INITIALIZED = True

    async with create_session() as session:
        for table in {Persons, Parents, Children}:
            stmt = delete(Persons)
            result = await session.execute(stmt)
        await session.commit()

    async with create_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()


@pytest.mark.parametrize("schema", [Persons, Person])
@pytest.mark.docker
@pytest.mark.asyncio
async def test_crud(db, schema: Crud):
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
    assert deleted == 1

    result = await crud.all()
    assert len(result) == 0


# @pytest.mark.parametrize("schema", [Persons, Person])
@pytest.mark.docker
@pytest.mark.asyncio
async def test_foreign_key(db):
    result = await Parents.crud(db).all()
    assert len(result) == 0

    parent = await Parents.crud(db).create(name="parent_1")
    child = await Children.crud(db).create(name="child_1", parent_id=parent.id)

    parent2 = await Parents.crud(db).create(name="parent_2")
    child2 = await Children.crud(db).create(name="child_2", parent_id=parent2.id)

    parent3 = await Parents.crud(db).get(parent2.id)
    assert isinstance(parent3, Parents)
    assert parent3

    parent4 = await ParentSchema.crud(db).get(parent3.id)
    assert parent4
    assert isinstance(parent4, ParentSchema)
    assert parent4.children
