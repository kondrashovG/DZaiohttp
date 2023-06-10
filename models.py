from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, func


PG_DSN='postgresql+asyncpg://app:secret@127.0.0.1:5431/app'

engine = create_async_engine(PG_DSN)
Base = declarative_base()
Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=True)


class User(Base):

    __tablename__ = 'app_user'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    creation_time = Column(DateTime, server_default=func.now())
