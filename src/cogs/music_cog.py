import asyncio
import sys
from dotenv import load_dotenv
from discord.ext import commands
import wavelink
import discord
import os

load_dotenv()


class MusicCog(commands.Cog):
    EMBED_COLOUR: discord.Colour = 0xE5BED0

    def __init__(self, bot: commands.Bot) -> None:
        """Constructor for the MusicCog."""
        commands.Cog.__init__(self)
        self.bot: commands.Bot = bot
        self.player: wavelink.Player = None
        self.bot.loop.create_task(self.node_connect())

    @commands.command(name="song")
    async def song(self, ctx: commands.Context):
        if not self.player or not self.player.is_connected() or not self.player.current:
            return await ctx.send("You're not playing anything.")

        await ctx.send(
            f"Currently playing: {self.player.current.title} by {self.player.current.author}"
        )

    @commands.command(name="play")
    async def play(self, ctx: commands.Context, *, search: wavelink.YouTubeTrack | wavelink.YouTubePlaylist = None) -> discord.Message:
        """
        If the player is not playing a track, play the track/s given.
        Otherwise, if the track is not valid or the user is not in
        a voice channel, return an error message.
        """
        if not search:
            return await ctx.send("Please state what song you want to play.")
        if not ctx.voice_client and not ctx.author.voice:
            return await ctx.send("Please enter a voice channel first!")

        if ctx.voice_client:
            vc: discord.VoiceChannel = ctx.voice_client
        else:
            vc: discord.VoiceChannel = ctx.author.voice.channel

        if not self.player or not self.player.is_connected():
            self.player: wavelink.Player = await vc.connect(
                timeout=90, reconnect=False, cls=wavelink.Player
            )

        if self.player.is_paused():
            return await ctx.send("Use command '!resume' to unpause your music.")
        
        if isinstance(search, wavelink.YouTubeTrack):
            embed: discord.Embed = self.__create_songs_embed(search)

            if self.player.queue.is_empty and not self.player.is_playing():
                await self.player.play(search)
                return await ctx.send(content="Currently playing:", embed=embed)
            else:
                await self.player.queue.put_wait(track)
                return await ctx.send(content="Queued:", embed=embed)
        else:
            embed: discord.Embed = self.__create_songs_embed(search)
            await self.player.queue.put_wait(search)
            
            if not self.player.queue.is_empty and not self.player.is_playing():
                track: wavelink.YouTubeTrack = await self.player.queue.get_wait()
                await self.player.play(track)
                return await ctx.send(
                    content="Currently playing playlist:", embed=embed
                )
            else:
                return await ctx.send(content="Queued:", embed=embed)

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context):
        """
        Pause the current track playing.
        """
        if not ctx.voice_client and not ctx.author.voice:
            return await ctx.send("Please enter a voice channel first!")

        if ctx.voice_client:
            vc: discord.VoiceChannel = ctx.voice_client
        else:
            vc: discord.VoiceChannel = ctx.author.voice.channel

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

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context):
        """
        Resume playing a track that was paused.
        """
        if not ctx.voice_client and not ctx.author.voice:
            return await ctx.send("Please enter a voice channel first!")

        if ctx.voice_client:
            vc: discord.VoiceChannel = ctx.voice_client
        else:
            vc: discord.VoiceChannel = ctx.author.voice.channel

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

    @commands.command(name="disconnect")
    async def disconnect(self, ctx: commands.Context):
        """
        The bot will leave the voice channel if connected and
        stop playing music.
        """
        if not self.player:
            return await ctx.send("You haven't played anything yet.")
        elif not self.player.is_connected():
            return await ctx.send("I've already disconnected from the channel.")

        await ctx.voice_client.disconnect()
        await ctx.send("Successfully disconnected from VC.")

    @commands.command(name="queue")
    async def queue(self, ctx: commands.Context) -> discord.Message:
        if not self.player:
            return await ctx.send("You haven't played anything yet.")

        if self.player.queue.is_empty:
            return await ctx.send("Queue is empty.")
        
        embed: discord.Embed = self.__create_queue_embed(self.player.queue)
        return await ctx.send(content="Queue:", embed=embed)

    @commands.command(name="shuffle")
    async def shuffle(self, ctx: commands.Context) -> None:
        if not self.player or not self.player.is_connected():
            return await ctx.send("You're not playing anything!")

        if self.player.queue.is_empty:
            return await ctx.send("Queue is empty.")

        await self.player.queue.shuffle()

    @commands.command(name="clear")
    async def clear(self, ctx: commands.Context) -> None:
        if not self.player or not self.player.is_connected():
            return await ctx.send("You're not playing anything!")

        if self.player.queue.is_empty:
            return await ctx.send("Queue is already empty.")

        await self.player.queue.reset()
        await ctx.send("Queue is now empty.")

    @commands.command(name="skip")
    async def skip(self, ctx: commands.Context):
        if not self.player or not self.player.is_connected():
            return await ctx.send("You're not playing anything!")
        if self.player.queue.is_empty and not self.player.current:
            return await ctx.send("Queue is empty.")

        # Play the next track if available
        await self.player.stop()
        await ctx.send("Skipped song!")

    @commands.Cog.listener()
    async def on_ready(self):
        print("MusicCog is ready.")

    @commands.Cog.listener()
    async def on_command_error(ctx: commands.Context, error: commands.errors.CommandError):
        await ctx.send("Invalid command, try again!")

    @commands.Cog.listener()
    async def on_command_error(self):
        print("Invalid command sent.")

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
        print(f"Player has finished playing a track.\n")
        if not self.player.queue.is_empty:
            next_track: wavelink.YouTubeTrack = await self.player.queue.get_wait()
            await self.player.play(next_track)
        else:
            print("Queue is empty.")

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

    def __create_queue_embed(self, queue: wavelink.Queue) -> discord.Embed:
        queue_list: str = ""
        for track in queue:
            queue_list += f"- {track.title} by {track.author}\n"

        embed: discord.Embed = discord.Embed(
            colour=self.EMBED_COLOUR,
            title="Queue:",
            description=queue_list
        )
        return embed
    
    def __create_songs_embed(
        self, search: wavelink.YouTubeTrack | wavelink.YouTubePlaylist
    ) -> discord.Embed:
        if isinstance(search, wavelink.YouTubeTrack):
            embed: discord.Embed = discord.Embed(
                colour=self.EMBED_COLOUR,
                title=f"{search.title} by {search.author}",
                description=f"{search.title}",
                url=search.uri,
            )
            return embed
        else:
            tracklist: str = "".join(
                f"{search.tracks.index(song)}. {song.title} by {song.author}\n"
                for song in search.tracks
            )
            embed: discord.Embed = discord.Embed(
                colour=self.EMBED_COLOUR,
                title=f"{search.name}",
                description=f"{tracklist}",
            )
            return embed

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))