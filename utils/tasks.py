import asyncio
from datetime import datetime
from sqlalchemy import select
from database.db import AsyncSessionLocal, User
from utils.cache import remove_ban

async def check_expired_mutes():
    """
    Periodically checks for expired mutes and updates DB.
    Also ensures bans are synced if needed (though bans are infinite usually).
    """
    while True:
        try:
            async with AsyncSessionLocal() as session:
                now = datetime.utcnow()
                # Find users who are muted AND mute time has passed
                # Actually, our logic in handlers just checks `mute_until > now`. 
                # If `mute_until` is in past, they are effectively unmuted.
                # BUT user requested: "Remove mute flag if time expired".
                # So we set mute_until = None for clean DB.
                
                stmt = select(User).where(User.mute_until < now)
                result = await session.execute(stmt)
                users = result.scalars().all()
                
                for user in users:
                    user.mute_until = None
                
                if users:
                    await session.commit()
                    # print(f"Cleaned up {len(users)} expired mutes.")
                    
        except Exception as e:
            print(f"Error in background task: {e}")
            
        await asyncio.sleep(60) # Check every minute
