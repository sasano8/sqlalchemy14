from fastapi import FastAPI, Depends
from sqlalchemy14.config import async_session, engine
from sqlalchemy.ext.asyncio import AsyncSession as Session
from sqlalchemy14.models import Book
from .models import Base
import traceback
import logging

logger = logging.getLogger(__name__)

app = FastAPI()


async def get_db():
    async with async_session() as session:
        async with session.begin():
            try:
                yield session
            except Exception as e:
                logger.critical(traceback.format_exc())
                raise


async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@app.post("/books")
async def create_book(
    db: Session = Depends(get_db), *, name: str, author: str, release_year: int
):
    obj = Book(name=name, author=author, release_year=release_year)
    return await obj.create(db)


@app.on_event("startup")
async def startup():
    await setup_db()
    # await engine.connect()


@app.on_event("shutdown")
async def shutdown():
    pass
    # await engine.dispose()
