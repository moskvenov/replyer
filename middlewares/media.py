from aiogram import BaseMiddleware
from aiogram.types import Message

class MediaSizeMiddleware(BaseMiddleware):
    def __init__(self, limit_mb: int = 50):
        self.limit_bytes = limit_mb * 1024 * 1024

    async def __call__(self, handler, event: Message, data: dict):
        if not isinstance(event, Message):
            return await handler(event, data)

        file_size = 0
        
        # Check different media types
        if event.document:
            file_size = event.document.file_size or 0
        elif event.video:
            file_size = event.video.file_size or 0
        elif event.audio:
            file_size = event.audio.file_size or 0
        elif event.voice:
            file_size = event.voice.file_size or 0
        # Photos are usually small, but strict check would check largest size
        
        if file_size > self.limit_bytes:
            await event.answer("❌ Файл слишком большой. Максимальный размер: 50 МБ.")
            return # Stop propagation

        return await handler(event, data)
