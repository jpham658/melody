from dotenv import load_dotenv
import os
import nextcord
from nextcord.ext import commands

from cogs.music_cog import MusicCog

load_dotenv()
intents = nextcord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} is connected.')

bot.add_cog(MusicCog(bot))

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))