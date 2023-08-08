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
    async def song(self, ctx: commands.Context) -> discord.Message:
        if not self.player or not self.player.is_connected() or not self.player.current:
            return await ctx.send("You're not playing anything.")

        embed: discord.Embed = self.__create_songs_embed(self.player.current)
        return await ctx.send(content="Currently playing:", embed=embed)

    @commands.command(name="play")
    async def play(self, ctx: commands.Context, *, search: wavelink.YouTubeTrack | wavelink.YouTubePlaylist = None) -> discord.Message:
        """
        Plays the track or playlist the user has given.

        :param search: The YouTube track or playlist to be played. 
        :return: A Message object describing if the player is playing anything.
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
                await self.player.queue.put_wait(search)
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
    async def pause(self, ctx: commands.Context) -> discord.Message:
        """
        Pause the current track playing.

        :return: A Message object describing if the player has paused.
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
        return await ctx.send(
            f"Paused {self.player.current.title} by {self.player.current.author}"
        )

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context) -> discord.Message:
        """
        Resume playing a track that was paused.

        :return: A Message object describing if the player resumed playing.
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
        return await ctx.send(
            f"Resumed playing {self.player.current.title} by {self.player.current.author}"
        )

    @commands.command(name="disconnect")
    async def disconnect(self, ctx: commands.Context) -> discord.Message:
        """
        The bot will leave the voice channel if connected and
        stop playing music.

        :return: A Message object describing if the player has disconnected from VC.
        """
        if not self.player:
            return await ctx.send("You haven't played anything yet.")
        elif not self.player.is_connected():
            return await ctx.send("I've already disconnected from the channel.")

        await ctx.voice_client.disconnect()
        return await ctx.send("Successfully disconnected from VC.")

    @commands.command(name="queue")
    async def queue(self, ctx: commands.Context) -> discord.Message:
        """
        View the player's queue.

        :return: A Message object describing the queue's current state.
        """
        if not self.player:
            return await ctx.send("You haven't played anything yet.")

        if self.player.queue.is_empty:
            return await ctx.send("Queue is empty.")
        
        embed: discord.Embed = self.__create_queue_embed(self.player.queue)
        return await ctx.send(content="Queue:", embed=embed)

    @commands.command(name="shuffle")
    async def shuffle_queue(self, ctx: commands.Context) -> discord.Message:
        """
        Shuffle the player's queue.

        :return: A Message object describing if the queue has been shuffled.
        """
        if not self.player or not self.player.is_connected():
            return await ctx.send("You're not playing anything!")

        if not self.player.queue or self.player.queue.is_empty:
            return await ctx.send("Queue is empty.")

        self.player.queue.shuffle()
        await ctx.send("Shuffled the queue!")
        embed: discord.Embed = self.__create_queue_embed(self.player.queue)
        return await ctx.send(content="Queue:", embed=embed)
    
    @commands.command(name="clear")
    async def clear(self, ctx: commands.Context) -> discord.Message:
        if not self.player or not self.player.is_connected():
            return await ctx.send("You're not playing anything!")

        if self.player.queue.is_empty:
            return await ctx.send("Queue is already empty.")

        await self.player.queue.reset()
        return await ctx.send("Queue is now empty.")

    @commands.command(name="skip")
    async def skip(self, ctx: commands.Context) -> discord.Message:
        """
        Skip the song currently playing.

        :return: A Message object describing if the current song has been skipped.
        """
        if not self.player or not self.player.is_connected():
            return await ctx.send("You're not playing anything!")
        if self.player.queue.is_empty and not self.player.current:
            return await ctx.send("Queue is empty.")

        await self.player.stop()
        return await ctx.send("Skipped song!")

    @commands.Cog.listener()
    async def on_ready(self):
        print("MusicCog is ready.")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.errors.CommandError):
        if isinstance(error, commands.errors.CommandNotFound):
            await ctx.send("This command is not supported. Use `!help` to see what commands are supported.")
        elif isinstance(error, commands.errors.CommandInvokeError):
            print("invoke error")
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