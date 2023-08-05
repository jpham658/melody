from dotenv import load_dotenv
from nextcord.ext import commands
import wavelink
import nextcord
import os

load_dotenv()


class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        """Constructor for the MusicCog."""
        commands.Cog.__init__(self)
        self.bot: commands.Bot = bot
        bot.loop.create_task(self.node_connect())

    @commands.command()
    async def play(self, ctx: commands.Context, *, track: wavelink.YouTubeTrack):
        if not ctx.voice_client and not ctx.author.voice:
            await ctx.send("Please enter a voice channel first!")
            return
        
        if ctx.voice_client:
            vc: nextcord.VoiceChannel = ctx.voice_client
        else: 
            vc: nextcord.VoiceChannel = ctx.author.voice.channel

        player: wavelink.Player = await vc.connect(timeout=90, reconnect=False, cls=wavelink.Player)

        if player.is_playing():
            await ctx.send("I'm already playing something!")
            return
        
        await player.play(track)
        embed: nextcord.Embed = nextcord.Embed(colour=0xe5bed0, 
                                                title=f"{track.title} by {track.author}", 
                                                description=f"{track.duration}",
                                                url=track.uri)
        thumbnail: str = await track.fetch_thumbnail()
        if thumbnail: 
            embed.set_thumbnail(thumbnail)
        await ctx.send(content="`˚₊‧꒰ა ♡ ໒꒱ ‧₊˚`", embed=embed)

    @commands.command()
    async def pause(self, ctx):
        if not ctx.voice_client and not ctx.author.voice:
            await ctx.send("Please enter a voice channel first!")
            return
        
        if ctx.voice_client:
            vc: nextcord.VoiceChannel = ctx.voice_client
        else: 
            vc: nextcord.VoiceChannel = ctx.author.voice.channel

        player: wavelink.Player = await vc.connect(timeout=90, reconnect=False, cls=wavelink.Player)

        if not player.is_playing():
            await ctx.send("You're not playing anything!")
            return 
        
        player.pause()

    @commands.command()
    async def resume(self, ctx):
        if not ctx.voice_client and not ctx.author.voice:
            await ctx.send("Please enter a voice channel first!")
            return
        
        if ctx.voice_client:
            vc: nextcord.VoiceChannel = ctx.voice_client
        else: 
            vc: nextcord.VoiceChannel = ctx.author.voice.channel

        player: wavelink.Player = await vc.connect(timeout=90, reconnect=False, cls=wavelink.Player)

        if player.is_playing():
            await ctx.send("You're already playing something!")
            return 
        
        player.resume()

    @commands.command()
    async def skip(self, ctx: commands.Context):
        return

    @commands.command()
    async def queue(self, ctx: commands.Context, *, track: wavelink.YouTubeTrack):
        return

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        print(f"Node {node.id} is ready.")

    async def node_connect(self):
        """Connect node to the Lavalink server."""
        await self.bot.wait_until_ready()
        NODE_HOST = os.getenv("NODE_HOST")
        NODE_PASSWORD = os.getenv("NODE_PASSWORD")
        node: wavelink.Node = wavelink.Node(
            uri=NODE_HOST, password=NODE_PASSWORD, use_http=True
        )
        await wavelink.NodePool.connect(client=self.bot, nodes=[node])


def setup(bot):
    bot.add_cog(MusicCog(bot))
