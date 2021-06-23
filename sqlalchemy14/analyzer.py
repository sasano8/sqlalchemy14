from dataclasses import is_dataclass
from functools import lru_cache
from inspect import isclass
from typing import List, Type, Union, get_args

from pydantic import BaseModel
from sqlalchemy import delete, insert, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.inspection import inspect


@lru_cache
def analyze(cls):
    entity = get_entity(cls)
    primary_keys = get_primary_keys(entity)
    columns = get_columns(cls)
    returning = get_returning(entity, columns)
    return entity, returning, primary_keys


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
        return [entity]
    else:
        return [getattr(entity, x) for x in columns]


@lru_cache
def get_insert(cls):
    entity, returning, primary_keys = analyze(cls)
    stmt = insert(entity).returning(*returning)
    return stmt


@lru_cache
def get_update(cls):
    entity, returning, primary_keys = analyze(cls)
    stmt = update(entity).returning(*returning)
    return stmt


@lru_cache
def get_select(cls):
    entity, returning, primary_keys = analyze(cls)
    stmt = select(*returning)
    return stmt


@lru_cache
def get_delete(cls):
    entity, returning, primary_keys = analyze(cls)
    stmt = delete(entity).returning(*primary_keys)
    return stmt


@lru_cache
def get_upsert(cls):
    entity, returning = analyze(cls)
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
