# sqlalchemy14
sqlalchemyのクエリビルダのショートカットを提供します。
postgresなどreturningが利用可能なDBで利用できます。

# setup
``` shell
poetry install
```

# Getting Started
クラス属性の`__entity__`にSqlalchemyモデルの参照を持たせることで、そのクラスをSqlalchemyモデルのように動作させることができます。

そして、そのクラスのフィールドを返すようにクエリを構築します。
insert・updateの場合はreturningに設定されます。
deleteの場合は、プライマリキーを返します。

一度解析されたモデルのクエリはキャッシュされるので、高速にクエリを構築できます。

``` python
import asyncio
import sqlalchemy as sa
from pydantic import BaseModel
from dataclasses import dataclass
from sqlalchemy14 import Crud, create_engine
from sqlalchemy import or_, and_


registry = sa.orm.registry()
Base = registry.generate_base()

class PersonEntity(Base, Crud):
    __tablename__ = "persons"

    id = sa.Column(sa.Integer, primary_key=True)
    password = sa.Column(sa.String)
    name = sa.Column(sa.String)

class Person(BaseModel, Crud[PersonEntity]):
    class Config:
        orm_mode = True

    id: int
    name: str


async def main():
    engine, create_session = create_engine(f"postgresql+asyncpg://{user}:{pw}@{host}:{port}/{db}")

    async with engine.begin() as conn:
        await conn.run_sync(registry.metadata.drop_all)
        await conn.run_sync(registry.metadata.create_all)

    async with create_session() as db:
        obj1 = await Person.crud(db).create(name="test1", password="pw1")
        obj2 = await Person.crud(db).get(id=obj1.id)
        obj3 = await Person.crud(db).update(id=obj1.id, password="pw2")
        objects = await Person.crud(db).all()
        await Person.crud(db).delete(id=obj1.id)


asyncio.run(main())

```