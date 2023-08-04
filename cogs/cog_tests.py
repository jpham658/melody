import unittest
import nextcord
import nextwave
from nextcord.ext import commands

from music_cog import MusicCog

class MusicCogTest(unittest.TestCase):
    def setUp(self):
        intents = nextcord.Intents.default()
        intents.message_content = True

        bot = commands.Bot(command_prefix="!", intents=intents)

        self.music_cog = MusicCog(bot)

    async def node_created(self):
        self.music_cog.node_connect()
        node: nextwave.Node = nextwave.NodePool.get_node()
        self.assertIsNotNone(node)