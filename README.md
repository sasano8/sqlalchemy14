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
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel
from dataclasses import dataclass
from sqlalchemy14 import Sql


Base = declarative_base()


class PersonEntity(Base):
    __tablename__ = "persons"

    id = sa.Column(sa.Integer, primary_key=True)
    password = sa.Column(sa.String)
    name = sa.Column(sa.String)


class Person(BaseModel):
    __entity__ = PersonEntity

    id: int
    name: str


Sql(Person).select()
# => SELECT persons.id, persons.name FROM persons

Sql(Person).insert()
# => INSERT INTO persons () VALUES () RETURNING persons.id, persons.name

Sql(Person).update()
# => UPDATE persons SET  RETURNING persons.id, persons.name

Sql(Person).delete()
# => DELETE FROM persons RETURNING persons.id


Person.sql.select()


person1 = await Person.crud(db).create(name="test1")
person1 = await Person.crud(db).copy(name="test1")
person2 = await Person.crud(db).update(id=1, name="test2")
person3 = await Person.crud(db).get(id=person2.id)
count = await Person.crud(db).delete(id=person2.id)

```