from nextcord.ext import commands
import wavelink

class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        """ Constructor for the MusicCog. """
        commands.Cog.__init__(self)
        self.bot: commands.Bot= bot
        bot.loop.create_task(self.node_connect())

    async def play(self):
        return
    
    async def skip(self):
        return

    async def queue(self):
        return 
    
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        print(f'Node {node.id} is ready.')

    async def node_connect(self):
        """ Connect to the nodes. """
        await self.bot.wait_until_ready()
        node: wavelink.Node = wavelink.Node(uri='lavalink.devamop.in', password='DevamOP', use_http=True, secure=True)
        await wavelink.NodePool.connect(client=self.bot, nodes=[node])

def setup(bot):
    bot.add_cog(MusicCog(bot))