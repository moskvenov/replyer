from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from .models import Base, User
from datetime import datetime

DATABASE_URL = "sqlite+aiosqlite:///bot.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_user(session: AsyncSession, user_id: int):
    result = await session.execute(select(User).where(User.user_id == user_id))
    return result.scalars().first()

async def add_user(session: AsyncSession, user_id: int, first_name: str, username: str):
    user = await get_user(session, user_id)
    if not user:
        user = User(user_id=user_id, first_name=first_name, username=username)
        session.add(user)
        await session.commit()
    return user

async def get_all_users_count(session: AsyncSession):
    result = await session.execute(select(User))
    return len(result.scalars().all())

async def get_banned_users_count(session: AsyncSession):
    result = await session.execute(select(User).where(User.is_banned == True))
    return len(result.scalars().all())

async def get_muted_users_count(session: AsyncSession):
    now = datetime.utcnow()
    result = await session.execute(select(User).where(User.mute_until > now))
    return len(result.scalars().all())

async def get_users_paginated(session: AsyncSession, page: int, limit: int = 10):
    offset = (page - 1) * limit
    result = await session.execute(select(User).offset(offset).limit(limit))
    return result.scalars().all()

async def get_banned_paginated(session: AsyncSession, page: int, limit: int = 10):
    offset = (page - 1) * limit
    result = await session.execute(select(User).where(User.is_banned == True).offset(offset).limit(limit))
    return result.scalars().all()

async def get_muted_paginated(session: AsyncSession, page: int, limit: int = 10):
    offset = (page - 1) * limit
    now = datetime.utcnow()
    result = await session.execute(select(User).where(User.mute_until > now).offset(offset).limit(limit))
    return result.scalars().all()

async def get_new_users_period(session: AsyncSession, delta: timedelta):
    since = datetime.utcnow() - delta
    result = await session.execute(select(User).where(User.joined_at >= since))
    return len(result.scalars().all())
