# type: ignore
from dataclasses import dataclass

import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy.orm import declarative_base

from sqlalchemy14 import Sql

Base = declarative_base()


class PersonEntity(Base):
    __tablename__ = "persons"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)


class Person(BaseModel):
    __entity__ = PersonEntity
    id: int
    name: str


@dataclass
class PersonDataClass:
    __entity__ = PersonEntity
    id: int
    name: str


class PersonFilter(BaseModel):
    __entity__ = PersonEntity
    name: str


def test_entity():
    select = Sql(PersonEntity).select()
    insert = Sql(PersonEntity).insert()
    update = Sql(PersonEntity).update()
    delete = Sql(PersonEntity).delete()

    # fmt: off
    assert str(select) == "SELECT persons.id, persons.name \nFROM persons"
    assert str(insert) == "INSERT INTO persons DEFAULT VALUES RETURNING persons.id, persons.name"
    assert str(update) == "UPDATE persons SET  RETURNING persons.id, persons.name"
    assert str(delete) == "DELETE FROM persons RETURNING persons.id"
    # fmt: on


def test_model():
    select = Sql(Person).select()
    insert = Sql(Person).insert()
    update = Sql(Person).update()
    delete = Sql(Person).delete()

    # fmt: off
    assert str(select) == "SELECT persons.id, persons.name \nFROM persons"
    assert str(insert) == "INSERT INTO persons DEFAULT VALUES RETURNING persons.id, persons.name"
    assert str(update) == "UPDATE persons SET  RETURNING persons.id, persons.name"
    assert str(delete) == "DELETE FROM persons RETURNING persons.id"
    # fmt: on


def test_dataclass():
    select = Sql(PersonDataClass).select()
    insert = Sql(PersonDataClass).insert()
    update = Sql(PersonDataClass).update()
    delete = Sql(PersonDataClass).delete()

    # fmt: off
    assert str(select) == "SELECT persons.id, persons.name \nFROM persons"
    assert str(insert) == "INSERT INTO persons DEFAULT VALUES RETURNING persons.id, persons.name"
    assert str(update) == "UPDATE persons SET  RETURNING persons.id, persons.name"
    assert str(delete) == "DELETE FROM persons RETURNING persons.id"
    # fmt: on


def test_model_filter():
    select = Sql(PersonFilter).select()
    insert = Sql(PersonFilter).insert()
    update = Sql(PersonFilter).update()
    delete = Sql(PersonFilter).delete()

    # fmt: off
    assert str(select) == "SELECT persons.name \nFROM persons"
    assert str(insert) == "INSERT INTO persons DEFAULT VALUES RETURNING persons.name"
    assert str(update) == "UPDATE persons SET  RETURNING persons.name"
    assert str(delete) == "DELETE FROM persons RETURNING persons.id"
    # fmt: on
