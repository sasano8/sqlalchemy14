from sqlalchemy import Column, Integer, String
from sqlalchemy import select, update
from .config import Base

# from functools import lru_cache


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    author = Column(String, nullable=False)
    release_year = Column(Integer, nullable=False)

    async def create(self, db):
        db.add(self)
        await db.flush()
        await db.refresh(self)
        return self

    async def update(self, db, **kwargs):
        q = update(self.__class__).where(self.__class__.id == self.id)
        q = q.values(**kwargs).execution_options(synchronize_session="fetch")
        result = await db.execute(q).one()
        await db.refresh(self)

    async def delete(self, db):
        return await db.delete(self)

    # python3.9ならpropertyにできる
    @classmethod
    def query(cls):
        return select(cls)

    @classmethod
    def where(cls, *criterion):
        return cls.query().where(*criterion)
