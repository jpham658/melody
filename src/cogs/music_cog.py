from dotenv import load_dotenv
from nextcord.ext import commands
import wavelink
import nextcord
import os

load_dotenv()


class MusicCog(commands.Cog):
    EMBED_COLOUR: nextcord.Colour = 0xE5BED0

    def __init__(self, bot: commands.Bot) -> None:
        """Constructor for the MusicCog."""
        commands.Cog.__init__(self)
        self.bot: commands.Bot = bot
        self.player: wavelink.Player = None
        bot.loop.create_task(self.node_connect())

    @commands.command()
    async def song(self, ctx: commands.Context):
        if not self.player or not self.player.is_connected():
            return await ctx.send("You're not playing anything.")

        await ctx.send(
            f"Currently playing: {self.player.current.title} by {self.player.current.author}"
        )

    @commands.command()
    async def play(self, ctx: commands.Context, *, track: wavelink.YouTubeTrack = None):
        """
        If the player is not playing a track, play the track given.
        """
        if not track:
            return await ctx.send("Please state what song you want to play.")

        if not ctx.voice_client and not ctx.author.voice:
            return await ctx.send("Please enter a voice channel first!")

        if ctx.voice_client:
            vc: nextcord.VoiceChannel = ctx.voice_client
        else:
            vc: nextcord.VoiceChannel = ctx.author.voice.channel

        if not self.player or not self.player.is_connected():
            self.player: wavelink.Player = await vc.connect(
                timeout=90, reconnect=False, cls=wavelink.Player
            )

        # Embed for message
        embed: nextcord.Embed = await self.__create_embed(track)

        if self.player.queue.is_empty and not self.player.is_playing():
            await self.player.play(track)
            await ctx.send(content="Currently playing:", embed=embed)
        else:
            await self.player.queue.put_wait(track)
            await ctx.send(content="Queued:", embed=embed)

    @commands.command()
    async def pause(self, ctx: commands.Context):
        """
        Pause the current track playing.
        """
        if not ctx.voice_client and not ctx.author.voice:
            return await ctx.send("Please enter a voice channel first!")

        if ctx.voice_client:
            vc: nextcord.VoiceChannel = ctx.voice_client
        else:
            vc: nextcord.VoiceChannel = ctx.author.voice.channel

        if not self.player or not self.player.is_connected():
            self.player: wavelink.Player = await vc.connect(
                timeout=90, reconnect=False, cls=wavelink.Player
            )

        if not self.player.current:
            return await ctx.send("You're not playing anything!")
        elif self.player.is_paused():
            return await ctx.send("Your track is already paused!")

        await self.player.pause()
        await ctx.send(
            f"Paused {self.player.current.title} by {self.player.current.author}"
        )

    @commands.command()
    async def resume(self, ctx: commands.Context):
        """
        Resume playing a track that was paused.
        """
        if not ctx.voice_client and not ctx.author.voice:
            return await ctx.send("Please enter a voice channel first!")

        if ctx.voice_client:
            vc: nextcord.VoiceChannel = ctx.voice_client
        else:
            vc: nextcord.VoiceChannel = ctx.author.voice.channel

        if not self.player or not self.player.is_connected():
            self.player: wavelink.Player = await vc.connect(
                timeout=90, reconnect=False, cls=wavelink.Player
            )

        if not self.player.current:
            return await ctx.send("You're not playing anything!")
        elif not self.player.is_paused():
            return await ctx.send("You're already playing something!")

        await self.player.resume()
        await ctx.send(
            f"Resumed playing {self.player.current.title} by {self.player.current.author}"
        )

    @commands.command()
    async def disconnect(self, ctx: commands.Context):
        """
        The bot will leave the voice channel if connected and
        stop playing music.
        """
        if not self.player:
            return await ctx.send("You haven't played anything yet.")
        elif not self.player.is_connected():
            return await ctx.send("I've already disconnected from the channel.")

        print("passed player isn't none check")
        await ctx.voice_client.disconnect()
        await ctx.send("Successfully disconnected from VC.")

    @commands.command()
    async def shuffle(self, ctx: commands.Context) -> None:
        if not self.player or not self.player.is_connected():
            return await ctx.send("You're not playing anything!")

        if self.player.queue.is_empty:
            return await ctx.send("Queue is empty.")

        await self.player.queue.shuffle()

    @commands.command()
    async def clear(self, ctx: commands.Context) -> None:
        if not self.player or not self.player.is_connected():
            return await ctx.send("You're not playing anything!")

        if self.player.queue.is_empty:
            return await ctx.send("Queue is already empty.")

        await self.player.queue.reset()
        await ctx.send("Queue is now empty.")

    @commands.command()
    async def skip(self, ctx: commands.Context):
        if not self.player or not self.player.is_connected():
            return await ctx.send("You're not playing anything!")
        if self.player.queue.is_empty:
            return await ctx.send("Queue is empty.")

        # Play the next track if available
        if not self.player.queue.is_empty:
            next_track: wavelink.YouTubeTrack = self.player.queue.get()
            await self.player.play(next_track)
            await ctx.send("Skipped song!")
        else:
            await ctx.send("Queue is empty!")

    @commands.Cog.listener()
    async def on_disconnect(self):
        if self.player and self.player.is_connected():
            await self.player.disconnect()
            print("Player disconnected.")
        else:
            print("Player could not be disconnected.")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        print(f"Node {node.id} is ready.")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackEventPayload):
        print(f"Player has started playing a track.")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEventPayload):
        print(f"Player has finished playing a track.")

    @commands.Cog.listener()
    async def on_wavelink_websocket_closed(
        self, payload: wavelink.WebsocketClosedPayload
    ):
        print(f"Websocket has closed successfully.")

    async def node_connect(self):
        """Connect node to the Lavalink server."""
        await self.bot.wait_until_ready()
        NODE_HOST = os.getenv("NODE_HOST")
        NODE_PASSWORD = os.getenv("NODE_PASSWORD")
        node: wavelink.Node = wavelink.Node(
            uri=NODE_HOST, password=NODE_PASSWORD, use_http=True
        )
        await wavelink.NodePool.connect(client=self.bot, nodes=[node])

    async def __create_embed(self, track: wavelink.YouTubeTrack) -> nextcord.Embed:
        embed: nextcord.Embed = nextcord.Embed(
            colour=self.EMBED_COLOUR,
            title=f"{track.title} by {track.author}",
            description=f"{track.duration}",
            url=track.uri,
        )
        thumbnail: str = await track.fetch_thumbnail()
        if thumbnail:
            embed.set_thumbnail(thumbnail)
        return embed


def setup(bot):
    bot.add_cog(MusicCog(bot))
