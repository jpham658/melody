from dotenv import load_dotenv
import os
import discord
from discord.ext import commands
import asyncio

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} is connected.')

async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"Added {filename[:-3]}")

async def main():
    async with bot:
        await load()
        await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())