from functools import lru_cache
from inspect import _empty as Undefined
from typing import TYPE_CHECKING, Any, Generic, List, Literal, Type, TypeVar, get_args

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from .analyzer import analyze, get_columns, get_entity
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


def extract_keys(cls: "DynamimcAsyncCrud", obj) -> dict:
    keys = {}
    for key in (x.name for x in cls.get_primary_keys()):
        keys[key] = getattr(obj, key)

    return keys


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

        if cls.__entity__ is cls.__schema__:
            pass
        else:
            schema = cls.__schema__
            columns: List[str] = get_columns(schema)  # type: ignore

            def output(row):
                return schema.from_orm(row)

            cls.output = staticmethod(output)  # type: ignore

    @classmethod
    @lru_cache
    def get_primary_keys(cls):
        # __init_subclass__で実行すると、sqlalchemyが初期化されていないのでカラムを取得できない
        entity, returning, primary_keys, load_strategies = analyze(cls.__schema__)
        return primary_keys

    @classmethod
    @lru_cache
    def get_returnings(cls):
        # __init_subclass__で実行すると、sqlalchemyが初期化されていないのでカラムを取得できない
        entity, returning, primary_keys, load_strategies = analyze(cls.__schema__)
        return returning

    @classmethod
    @lru_cache
    def get_load_strategies(cls):
        # __init_subclass__で実行すると、sqlalchemyが初期化されていないのでカラムを取得できない
        entity, returning, primary_keys, load_strategies = analyze(cls.__schema__)
        return load_strategies

    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db

    @staticmethod
    def output(row):
        return row

    async def get_or_none(self, *args, **kwargs):
        if args and kwargs:
            raise Exception()

        if args:
            pks = self.get_primary_keys()
            if len(args) != 1:
                raise Exception()

            if len(pks) != 1:
                raise Exception()

            condition = {pks[0].key: args[0]}
        else:
            condition = kwargs

        stmt = self.sql.get()
        cur = await self.db.execute(stmt.params(**condition))
        result = cur.unique().scalar_one_or_none()
        if result is None:
            return None
        else:
            # TODO: session manage
            # セッションに含まれているとローダー戦略が変更された時エラーが生じるのでセッションに含まない
            # ネストしたオブジェクトはおそらくexpungeされない（セッションを参照している）
            self.db.expunge(result)
            return self.output(result)

    async def get(self, *args, **kwargs):
        result = await self.get_or_none(*args, **kwargs)
        if result is None:
            raise KeyError()
        return result

    async def exist(self, *args, **kwargs) -> bool:
        result = await self.get_or_none(*args, **kwargs)
        return True if result else False

    async def create(self, obj: BaseModel = None, /, **kwargs):
        if obj:
            assert not kwargs
            kwargs = obj.dict()

        keys, values = split_keys_values(self.__class__, kwargs)
        obj = self.__entity__(**values)
        self.db.add(obj)
        await self.db.flush()  # flushしないとリフレッシュできない
        # await self.db.refresh(obj)  # リフレッシュしないと後続のselectで取れない　←　そんなことはなさそうだ？？
        self.db.expunge(obj)
        keys = extract_keys(self.__class__, obj)
        return await self.get(**keys)

    async def update_or_pass(self, obj: BaseModel = None, /, **kwargs):
        if obj:
            assert not kwargs
            kwargs = obj.dict(exclude_unset=True)

        keys, values = split_keys_values(self.__class__, kwargs)
        condtions = (getattr(self.__entity__, k) == v for k, v in keys.items())

        if not await self.exist(**keys):
            return None

        stmt = self.sql.update(**values).where(*condtions)
        cur = await self.db.execute(stmt)
        return await self.get_or_none(**keys)

    async def update(self, obj: BaseModel = None, /, **kwargs):
        result = await self.update_or_pass(obj, **kwargs)
        if not result:
            raise KeyError()
        else:
            return result

    async def delete_or_pass(self, obj: BaseModel = None, /, **kwargs):
        if obj:
            assert not kwargs
            kwargs = obj.dict()

        keys, values = split_keys_values(self.__class__, kwargs)
        condtions = (getattr(self.__entity__, k) == v for k, v in keys.items())

        if not await self.exist(**keys):
            return 0

        stmt = self.sql.delete().where(*condtions)
        cur = await self.db.execute(stmt)
        return 1

    async def delete(self, obj: BaseModel = None, /, **kwargs):
        count = await self.delete_or_pass(obj, **kwargs)
        if not count:
            raise KeyError()
        else:
            return 1

    async def __iter__(self, query_builder=lambda stmt: stmt):
        stmt = query_builder(self.sql.select())
        cur = await self.db.execute(stmt)
        return (self.output(x) for x in cur.scalars())

    async def all(self, query_builder=lambda stmt: stmt):
        rows = await self.__iter__(query_builder)
        return list(rows)

    async def split(
        self, query_builder=lambda stmt: stmt, offset: int = 0, limit: int = 50
    ):
        pagenation = lambda stmt: query_builder(stmt).offset(offset).limit(limit)
        result = await self.all(pagenation)
        return {
            "offset": offset,
            "count": len(result),
            "result": result,
        }

    async def pagenate(
        self, query_builder=lambda stmt: stmt, page: int = 1, per_page: int = 50
    ):
        page = max(page, 1)
        offset = max(page, 0) * per_page
        pagenation = lambda stmt: query_builder(stmt).offset(offset).limit(per_page)
        result = await self.all(pagenation)
        return {
            "page": page,
            "count": len(result),
            "result": result,
        }
