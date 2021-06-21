import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy.orm import declarative_base

Base = declarative_base()


count = 0


def new_name():
    global count
    count += 1

    return f"table_{count}"


def to_list(columns):
    return [x.name for x in columns]


class TestInitSubclass:
    def test_inherit_1(self):
        from sqlalchemy14 import Crud

        class Entity_1(Crud, Base):
            __tablename__ = new_name()
            id = sa.Column(sa.Integer, primary_key=True)

        class Entity_2(Base, Crud):
            __tablename__ = new_name()
            id = sa.Column(sa.Integer, primary_key=True)

        assert to_list(Entity_1.crud(None).get_primary_keys()) == ["id"]
        assert to_list(Entity_2.crud(None).get_primary_keys()) == ["id"]

    def test_inherit_2(self):
        from sqlalchemy14 import Crud

        class Entity_3(Base):
            __tablename__ = new_name()
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String)

        class Model_1(BaseModel, Crud[Entity_3]):
            id: int

        class Model_2(Crud[Entity_3], BaseModel):
            id: int

        assert to_list(Model_1.crud(None).get_primary_keys()) == ["id"]
        assert to_list(Model_2.crud(None).get_primary_keys()) == ["id"]

        class Model_3(Model_1):
            name: str

        assert to_list(Model_3.crud(None).get_primary_keys()) == ["id"]

        assert to_list(Model_1.crud(None).get_returnings()) == ["id"]
        assert to_list(Model_2.crud(None).get_returnings()) == ["id"]
        assert to_list(Model_3.crud(None).get_returnings()) == ["id", "name"]

    def test_custom_declarative_base(self):
        from sqlalchemy14 import Crud

        Base2 = declarative_base(cls=Crud)

        class Entity_4(Base2):
            __tablename__ = new_name()
            id = sa.Column(sa.Integer, primary_key=True)

        assert to_list(Entity_4.crud(None).get_primary_keys()) == ["id"]

        class Model_1(BaseModel, Crud[Entity_4]):
            id: int

        assert to_list(Model_1.crud(None).get_primary_keys()) == ["id"]


def test_properties():
    from sqlalchemy14 import Crud, Sql

    class Entity_5(Crud, Base):
        __tablename__ = new_name()
        id = sa.Column(sa.Integer, primary_key=True)

    assert isinstance(Entity_5.crud(None).sql, Sql)
    assert isinstance(Entity_5.sql, Sql)

    Base2 = declarative_base(cls=Crud)

    class Entity_6(Base2):
        __tablename__ = new_name()
        id = sa.Column(sa.Integer, primary_key=True)

    assert isinstance(Entity_6.crud(None).sql, Sql)
    assert isinstance(Entity_6.sql, Sql)
