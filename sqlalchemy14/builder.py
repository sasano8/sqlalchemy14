from functools import lru_cache
from inspect import _empty as Undefined
from typing import TYPE_CHECKING, Any, Generic, List, Literal, Type, TypeVar, get_args

from pydantic import BaseModel
from sqlalchemy.orm import Session

from .analyzer import analyze, get_entity
from .sql import Sql

T = TypeVar("T")
S = TypeVar("S")
OWN = TypeVar("OWN")


def get_own_or_generics(target_cls, expected_cls: Type[T]):
    """対象クラスからジェネリックを抽出するか、ノンジェネリックの場合は自分自身を返す"""
    modelclassess = [
        generic_alias
        for generic_alias in target_cls.__orig_bases__
        if hasattr(generic_alias, "__origin__")
        and issubclass(generic_alias.__origin__, expected_cls)
    ]
    if len(modelclassess) == 0:
        return target_cls
    elif len(modelclassess) == 1:
        types = get_args(modelclassess[0])
        return types[0]
    else:
        raise Exception()


def split_keys_values(cls: "DynamimcAsyncCrud", kwargs):
    keys = {}
    for key in (x.name for x in cls.get_primary_keys()):
        val = kwargs.pop(key, Undefined)
        if not val is Undefined:
            keys[key] = val
    return keys, kwargs


def split_where_values(cls: "DynamimcAsyncCrud", kwargs):
    conditions = [x == kwargs[x.name] for x in cls.get_primary_keys()]
    for key in cls.get_primary_keys():
        kwargs.pop(key.name)
    return conditions, kwargs


class Crud(Generic[T]):
    __entity__: Type[T]  # declarative_base
    sql: Sql

    if TYPE_CHECKING:

        @classmethod
        def crud(cls: Type[OWN], db) -> "DynamimcAsyncCrud[OWN]":
            ...

    def __init_subclass__(cls, *args, **kwargs):
        own_or_generic = get_own_or_generics(cls, Crud)

        # declarative_base(cls=Crud)のような抽象クラスは処理しない
        if str(own_or_generic.__module__) == "sqlalchemy.orm.decl_api":
            return

        assert get_entity(own_or_generic)

        cls.__entity__ = own_or_generic
        cls.sql = Sql(cls)
        cls.crud = DynamimcAsyncCrud._create_class(cls)  # type: ignore


class DynamimcAsyncCrud(Generic[T]):
    sql: Sql
    __schema__: Type[T]
    __entity__ = None

    @classmethod
    def _create_class(
        cls: Type["DynamimcAsyncCrud"], schema: Type
    ) -> "DynamimcAsyncCrud[S]":
        class DynamicCrud(cls[schema]):  # type: ignore
            ...

        return DynamicCrud  # type: ignore

    def __init_subclass__(cls, *args, **kwargs):
        own_or_generic = get_own_or_generics(cls, DynamimcAsyncCrud)
        assert get_entity(own_or_generic)

        cls.__schema__ = own_or_generic
        cls.__entity__ = get_entity(own_or_generic)
        cls.sql = Sql(cls.__schema__)
        schema = cls.__schema__

        def output(row):
            return schema(**row)

        cls.output = staticmethod(output)  # type: ignore

    @classmethod
    @lru_cache
    def get_primary_keys(cls):
        # __init_subclass__で実行すると、sqlalchemyが初期化されていないのでカラムを取得できない
        entity, returning, primary_keys = analyze(cls.__schema__)
        return primary_keys

    @classmethod
    @lru_cache
    def get_returnings(cls):
        # __init_subclass__で実行すると、sqlalchemyが初期化されていないのでカラムを取得できない
        entity, returning, primary_keys = analyze(cls.__schema__)
        return returning

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def output(row):
        return row

    async def get(self, obj: BaseModel = None, /, **kwargs):
        if obj:
            assert not kwargs
            kwargs = obj.dict()

        conditions, kwargs = split_where_values(self.__class__, kwargs)
        stmt = self.sql.select().where(*conditions)
        result = await self.db.execute(stmt)
        return self.output(result.fetchone())

    async def create(self, obj: BaseModel = None, /, **kwargs):
        if obj:
            assert not kwargs
            kwargs = obj.dict()

        keys, values = split_keys_values(self.__class__, kwargs)
        stmt = self.sql.insert(**values)
        result = await self.db.execute(stmt)
        return self.output(result.fetchone())

    async def update(self, obj: BaseModel = None, /, **kwargs):
        if obj:
            assert not kwargs
            kwargs = obj.dict(exclude_unset=True)

        conditions, kwargs = split_where_values(self.__class__, kwargs)
        stmt = self.sql.update(**kwargs).where(*conditions)
        result = await self.db.execute(stmt)
        return self.output(result.fetchone())

    async def delete(self, obj: BaseModel = None, /, **kwargs):
        if obj:
            assert not kwargs
            kwargs = obj.dict()

        conditions, kwargs = split_where_values(self.__class__, kwargs)
        stmt = self.sql.delete().where(*conditions)
        result = await self.db.execute(stmt)
        count = result.count()
        if not count:
            raise Exception()

    async def __iter__(self, query_builder=lambda stmt: stmt):
        stmt = query_builder(self.sql.select())
        rows = await self.db.execute(stmt)
        return (self.output(x) for x in rows)

    async def all(self, query_builder=lambda stmt: stmt):
        rows = await self.__iter__(query_builder)
        return list(rows)
