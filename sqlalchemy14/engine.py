import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


def create_engine(connection_string: str, class_=AsyncSession):
    assert issubclass(class_, AsyncSession)
    engine = create_async_engine(connection_string)
    create_session = sa.orm.sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=AsyncSession,
        future=True,
    )
    return engine, create_session
