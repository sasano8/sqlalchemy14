from dataclasses import is_dataclass
from functools import lru_cache
from inspect import isclass
from typing import List, Type, Union, get_args

from pydantic import BaseModel
from sqlalchemy import bindparam, delete, func, insert, update
from sqlalchemy.future import select

# from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import (
    ColumnProperty,
    CompositeProperty,
    RelationshipProperty,
    SynonymProperty,
    joinedload,
)


@lru_cache
def analyze(cls):
    entity = get_entity(cls)
    primary_keys = get_primary_keys(entity)
    columns = get_columns(cls)
    table_columns, load_strategies = get_returning(entity, columns)
    return entity, table_columns, primary_keys, load_strategies


def get_entity(cls):
    assert isclass(cls)

    if hasattr(cls, "_sa_registry"):
        return cls
    elif hasattr(cls, "__entity__"):
        return get_entity(cls.__entity__)
    else:
        return None


def get_primary_keys(cls):
    assert isclass(cls)
    assert hasattr(cls, "_sa_registry")

    return [getattr(cls, key.key) for key in inspect(cls).primary_key]


def get_columns(cls) -> Union[List[str], None]:
    assert isclass(cls)

    if hasattr(cls, "_sa_registry"):
        return None
    elif issubclass(cls, BaseModel):
        return get_columns_for_pydantic(cls)
    elif is_dataclass(cls):
        return get_columns_for_dataclass(cls)
    else:
        raise NotImplementedError(cls)


def get_returning(entity, columns: Union[List[str], None]):
    assert isclass(entity)
    assert hasattr(entity, "_sa_registry")

    if columns is None:
        attrs = [getattr(entity, x.key) for x in inspect(entity).attrs]
    else:
        attrs = [getattr(entity, x) for x in columns]

    table_columns = []
    relations = []

    for x in attrs:
        if isinstance(x.property, ColumnProperty):
            table_columns.append(x)
        elif isinstance(x.property, RelationshipProperty):
            relations.append(x)
        else:
            raise NotImplementedError()

    if columns is None:
        return table_columns, []  # ORMモデルの場合はリレーションの取得はデフォルトに任せる
    else:
        return table_columns, relations


execution_options = dict(
    synchronize_session=False,  # セッションを同期しない
    # synchronize_session="fetch",  # update, deleteでセッションを同期する。returningを使う場合は使用できない模様
    # synchronize_session="evaluate",  # fetchがサポートされていない場合は、状況によって効率的なことがある
)


# ORMオブジェクトを返すにはselectにORMモデルを指定する必要がある
# returningにORMオブジェクトやrelationshipのカラムは指定できない
# relationshipが含まれなければreturningを使うことができる
# 解析で取得されるreturningはrelationshipなどの結合プロパティは含まれない


@lru_cache
def get_insert(cls):
    entity, returning, primary_keys, load_strategies = analyze(cls)
    stmt = insert(entity).returning(*returning)
    return stmt


@lru_cache
def get_update(cls):
    entity, returning, primary_keys, load_strategies = analyze(cls)
    stmt = update(entity)
    return stmt


@lru_cache
def get_select(cls):
    entity, returning, primary_keys, load_strategies = analyze(cls)
    stmt = select(entity)
    return stmt


@lru_cache
def get_get(cls):
    entity, returning, primary_keys, load_strategies = analyze(cls)
    bind_primary_keys = []
    options = None

    for pk in primary_keys:
        bind_primary_keys.append(pk == bindparam(pk.key))

    for strategy in load_strategies:
        if options is None:
            options = joinedload(strategy, innerjoin=strategy.property.innerjoin)
        else:
            options.joinedload(strategy, innerjoin=strategy.property.innerjoin)

    # TODO: ネストしたリレーションシップに対応するには次のようなことをしなければいけない
    # joinedload(Parent.children).subqueryload(Child.elements)
    stmt = select(entity).where(*bind_primary_keys)
    if options:
        stmt = stmt.options(options)

    # コンパイルできるか確認
    stmt.compile()
    return stmt


@lru_cache
def get_delete(cls):
    entity, returning, primary_keys, load_strategies = analyze(cls)
    stmt = delete(entity)
    return stmt


@lru_cache
def get_upsert(cls):
    entity, returning, primary_keys, load_strategies = analyze(cls)
    on_conflict_do_update = insert(entity).returning(*returning).on_conflict_do_update
    primary_keys = [key.name for key in inspect(entity).primary_key]

    def upsert(**values):
        # キーと更新キーを分ける必要あり
        return on_conflict_do_update(index_elements=primary_keys, set_=values).values(
            **values
        )

    return upsert


def get_columns_for_pydantic(cls: Type[BaseModel]) -> List[str]:
    return [x.name for x in cls.__fields__.values()]


def get_columns_for_dataclass(cls) -> List[str]:
    return [x.name for x in cls.__dataclass_fields__.values()]
