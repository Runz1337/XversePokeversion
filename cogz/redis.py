import aioredis,asyncio
from discord.ext import commands
import os

db = os.getenv("redf")

class Redis(commands.Cog):
    """For Redis."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pool = None
        self._reconnect_task = self.bot.loop.create_task(self.connect())

    async def connect(self):
        while True:
            try:
                self.pool = await aioredis.create_redis_pool(db)
                break  # Connection successful, break the loop
            except Exception as e:
                print(f"Failed to connect to Redis: {e}")
                await asyncio.sleep(10)  # Wait for 10 seconds before retrying

    async def close(self):
        self.pool.close()
        await self.pool.wait_closed()

    async def wait_until_ready(self):
        await self._reconnect_task

    def cog_unload(self):
        self.bot.loop.create_task(self.close())

async def setup(bot: commands.Bot):
    redis_cog = Redis(bot)
    await redis_cog.connect()  # Connect before adding the cog
    await bot.add_cog(redis_cog)